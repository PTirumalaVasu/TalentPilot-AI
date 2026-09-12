"""Service layer for the employees module.

Story 7.1 added the bcrypt hash/verify helpers. Story 7.2 (create, FR-24)
adds password generation and the first real CRUD service method.
Cross-module callers must go through here (AD-1).
"""
import asyncio
import logging
import secrets
from datetime import datetime, timezone
from uuid import UUID

import bcrypt
from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import repository as auth_repository
from app.auth.schemas import CurrentUser
from app.auth.service import require_hr_admin
from app.core.errors import AppException
from app.employees import repository
from app.employees.schemas import (
    CreateEmployeeRequest,
    DeleteEmployeeResponse,
    EmployeeCreatedResponse,
    EmployeeResponse,
    UpdateEmployeeRequest,
)

# NOTE: app.assignments.service is deliberately imported locally (inside the
# functions below), never at module level -- assignments/service.py imports
# assert_employee_active_for_assignment from THIS module at its own module
# level (Story 7.5 AC5), so a module-level import here would be a circular
# import. Deferring these imports to call time is safe because by the time
# any of these functions actually runs, both modules have finished loading.

logger = logging.getLogger(__name__)

# Excludes visually-ambiguous characters (I, O, l, 0, 1) -- matches the
# already-validated UX prototype's generatePassword() exactly
# (05.1-Employees-Tab.html), so a real build's generated passwords look and
# behave the same as what Rita's roster management flow was designed around.
_PASSWORD_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"
_PASSWORD_LENGTH = 12


def hash_password(plaintext: str) -> str:
    """Hash a plaintext password with bcrypt. Returns a UTF-8 string suitable
    for storing in Account.password_hash."""
    return bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))


def generate_password() -> str:
    """Generate a 12-character random password using a cryptographically
    secure source (`secrets`, not `random` -- this is a real credential, not
    a UI mock), drawn from an alphabet that excludes visually-ambiguous
    characters. No complexity policy (uppercase/digit/symbol requirements) is
    applied -- no AC or PRD FR specifies one (Story 7.2 Dev Notes)."""
    return "".join(secrets.choice(_PASSWORD_ALPHABET) for _ in range(_PASSWORD_LENGTH))


def _with_assignment_history(response: EmployeeResponse, has_history: bool) -> EmployeeResponse:
    """Sets the computed (non-ORM-column) has_assignment_history field on an
    already-validated EmployeeResponse (Story 7.5). Pydantic v2 models are
    mutable by default, so this is a plain attribute set after
    `model_validate` rather than trying to smuggle the value through
    `from_attributes=True`, which would require a real attribute on the ORM
    object itself."""
    response.has_assignment_history = has_history
    return response


async def _get_employee_ids_with_any_history(db: AsyncSession) -> set[UUID]:
    """Union of every signal that should make has_assignment_history True
    (Story 7.5 code review, 2026-09-12): Assignment target/assigner/deleter
    (assignments/), AssignmentOverride set/reversed actor (progress/), and
    AdminApiKey/ContentCatalog admin actor (content/) -- three separate
    cross-module service calls per AD-1, one bulk query each."""
    from app.assignments.service import get_employee_ids_with_assignment_history
    from app.content.service import get_employee_ids_with_admin_actor_history
    from app.progress.service import ProgressService

    assignment_ids = await get_employee_ids_with_assignment_history(db)
    override_ids = await ProgressService.get_employee_ids_with_override_actor_history(db)
    admin_ids = await get_employee_ids_with_admin_actor_history(db)
    return assignment_ids | override_ids | admin_ids


async def _has_any_history_for_employee(db: AsyncSession, employee_id: UUID) -> bool:
    """Single-employee equivalent of _get_employee_ids_with_any_history, for
    create/update's one-row responses (Story 7.5 code review, 2026-09-12)."""
    from app.assignments.service import has_assignment_history_for_employee
    from app.content.service import has_admin_actor_history_for_employee
    from app.progress.service import ProgressService

    if await has_assignment_history_for_employee(db, employee_id):
        return True
    if await ProgressService.has_override_actor_history_for_employee(db, employee_id):
        return True
    return await has_admin_actor_history_for_employee(db, employee_id)


async def list_employees_service(db: AsyncSession, *, current_user: CurrentUser) -> list[EmployeeResponse]:
    """Full Employee roster (Story 7.3, FR-25) -- HR_ADMIN-only (AD-6/FR-14),
    mirrors content.service.list_skills_with_content's require_hr_admin
    gate. Search/filter/pagination are deliberately not implemented here --
    the frontend fetches this full list once and does all of that
    client-side (Story 7.3 Scope Note 2), matching the SkillsPage/Story 6.10
    precedent.

    has_assignment_history (Story 7.5) is computed via one bulk query per
    signal source (assignments target/assigner/deleter, progress override
    actor, content admin-key/attach actor -- code review, 2026-09-12,
    broadened this beyond target-only so the Delete/Archive confirm dialog's
    prediction also covers HR Admins who've acted elsewhere in the app), not
    per-row (N+1)."""
    require_hr_admin(current_user)
    employees = await repository.list_all_employees(db)
    history_ids = await _get_employee_ids_with_any_history(db)
    return [
        _with_assignment_history(EmployeeResponse.model_validate(employee), employee.id in history_ids)
        for employee in employees
    ]


def _code_conflict(employee_code: str) -> AppException:
    return AppException(
        status.HTTP_409_CONFLICT,
        error_code="EMPLOYEE_CODE_CONFLICT",
        message=f"An employee with ID/Code '{employee_code}' already exists",
    )


def _email_conflict(email: str) -> AppException:
    return AppException(
        status.HTTP_409_CONFLICT,
        error_code="EMPLOYEE_EMAIL_CONFLICT",
        message=f"An employee with email '{email}' already exists",
    )


async def create_employee_service(
    db: AsyncSession, *, current_user: CurrentUser, request: CreateEmployeeRequest
) -> EmployeeCreatedResponse:
    """Create a new Employee with a working login (Story 7.2, FR-24).
    HR_ADMIN-only (AD-6), matching skills/service.py::create_skill_service's
    established service-layer require_hr_admin gate pattern.

    Duplicate checks cover active AND archived records (AC2) -- employee_code
    is checked exact-match (case-sensitive, matching the plain DB UNIQUE
    constraint); email is checked case-insensitively (AC1, "matching FR-20's
    Skill-name dedup pattern"), backstopped by migration 012's functional
    unique index for the same concurrent-request race skills/'s migration 006
    closes.

    The plaintext password exists only in this function's return value --
    never logged, never stored anywhere except its bcrypt hash in Account.
    """
    require_hr_admin(current_user)

    existing_code, existing_email = await repository.get_employee_by_code_or_email_ci(
        db, request.employee_code, request.email
    )
    if existing_code is not None:
        raise _code_conflict(request.employee_code)
    if existing_email is not None:
        raise _email_conflict(request.email)

    plaintext_password = generate_password()
    # bcrypt's default cost factor takes ~100-300ms -- run it off the event
    # loop (Story 7.2 code review) so it doesn't stall every other in-flight
    # request on this single-process asyncio server. Mirrors main.py's
    # existing asyncio.to_thread(load_embedding_model) precedent for
    # offloading blocking CPU work.
    password_hash = await asyncio.to_thread(hash_password, plaintext_password)

    employee_data = {
        "employee_code": request.employee_code,
        "name": request.name,
        "email": request.email,
        "role": "EMPLOYEE",
        "phone": request.phone,
        "experience": request.experience,
        "technologies": request.technologies,
        "position": request.position,
        "project": request.project,
        "manager_name": request.manager_name,
        "location": request.location,
        "department": request.department,
    }

    try:
        employee = await repository.create_employee_with_account(db, employee_data, password_hash)
    except IntegrityError:
        # Concurrent-request race backstop, same shape as
        # skills/service.py::create_skill_service's IntegrityError handling:
        # two requests for the same employee_code or same-case-insensitive
        # email could both pass the pre-checks above before either commits.
        #
        # The rollback undoes BOTH of create_employee_with_account's writes
        # (the Employee insert and the Account insert), so re-checking only
        # `employees` here would misattribute a failure that actually came
        # from the *Account* insert (e.g. a stale accounts.email left over
        # from some future Employee-edit story letting the two tables'
        # emails drift apart, FR-26's own `[ASSUMPTION]`) -- that case would
        # otherwise fall through to a raw, unattributed 500 (Story 7.2 code
        # review). Check accounts too before giving up.
        await db.rollback()
        existing_code, existing_email = await repository.get_employee_by_code_or_email_ci(
            db, request.employee_code, request.email
        )
        if existing_code is not None:
            raise _code_conflict(request.employee_code) from None
        if existing_email is not None:
            raise _email_conflict(request.email) from None
        existing_account = await auth_repository.get_account_by_email_ci(db, request.email)
        if existing_account is not None:
            raise _email_conflict(request.email) from None
        raise

    return EmployeeCreatedResponse(
        **EmployeeResponse.model_validate(employee).model_dump(),
        generated_password=plaintext_password,
    )


def _not_found(employee_id: UUID) -> AppException:
    return AppException(
        status.HTTP_404_NOT_FOUND,
        error_code="EMPLOYEE_NOT_FOUND",
        message=f"No employee found with id '{employee_id}'",
    )


async def update_employee_service(
    db: AsyncSession, *, current_user: CurrentUser, employee_id: UUID, request: UpdateEmployeeRequest
) -> EmployeeResponse:
    """Edit an existing Employee's profile fields (Story 7.4, FR-26).
    HR_ADMIN-only (AD-6). Employee ID/Code is immutable (not part of
    UpdateEmployeeRequest at all) and Assignment history never gates this --
    unlike skills/service.py::update_skill_service's ever_assigned lock.

    Email-conflict checks (both the pre-check and the IntegrityError
    backstop below) exclude the Employee's own row/Account -- otherwise
    re-saving with an unchanged email would spuriously 409 against itself
    (the most common real-world save). If the email changed, Account.email
    is updated too, in the same transaction, to keep the two tables from
    drifting apart (Story 7.2 code review's explicit forward reference to
    this story). No optimistic lock: concurrent edits are last-write-wins,
    matching this PRD's existing precedent everywhere else.
    """
    require_hr_admin(current_user)

    employee = await repository.get_employee_by_id(db, employee_id)
    if employee is None:
        raise _not_found(employee_id)

    # Raw (case-sensitive) comparison, captured before repository.update_employee
    # mutates employee.email in place -- a case-only edit (e.g. "Jane@x.com" ->
    # "jane@x.com") must still sync Account.email (code review, Story 7.4),
    # even though it never trips the case-insensitive conflict check below.
    email_value_changed = request.email != employee.email
    email_ci_changed = request.email.lower() != employee.email.lower()
    if email_ci_changed:
        existing_email = await repository.get_employee_by_email_ci_excluding_id(db, request.email, employee.id)
        if existing_email is not None:
            raise _email_conflict(request.email)

    employee_data = {
        "name": request.name,
        "email": request.email,
        "phone": request.phone,
        "experience": request.experience,
        "technologies": request.technologies,
        "position": request.position,
        "project": request.project,
        "manager_name": request.manager_name,
        "location": request.location,
        "department": request.department,
    }

    try:
        await repository.update_employee(db, employee, employee_data)
        if email_value_changed:
            await auth_repository.update_account_email(db, id=employee_id, email=request.email)
    except IntegrityError:
        # Race backstop, same shape as create_employee_service's: two
        # concurrent edits could both pass the pre-check above before either
        # commits. Re-check both tables (self-excluded) before giving up.
        #
        # Use employee_id (the plain function parameter), not employee.id --
        # db.rollback() expires every attribute on `employee`, and reading one
        # outside an active greenlet/await context raises MissingGreenlet
        # (code review, Story 7.4; matches the existing documented pattern in
        # content/service.py and skills/service.py's own IntegrityError
        # backstops, which use a plain id parameter post-rollback for the
        # same reason).
        await db.rollback()
        existing_email = await repository.get_employee_by_email_ci_excluding_id(db, request.email, employee_id)
        if existing_email is not None:
            raise _email_conflict(request.email) from None
        existing_account = await auth_repository.get_account_by_email_ci_excluding_id(
            db, request.email, employee_id
        )
        if existing_account is not None:
            raise _email_conflict(request.email) from None
        raise

    has_history = await _has_any_history_for_employee(db, employee_id)
    return _with_assignment_history(EmployeeResponse.model_validate(employee), has_history)


def _archived_conflict(employee_id: UUID) -> AppException:
    # Code review, 2026-09-12: the message deliberately says "no longer
    # available" rather than "has been archived" -- this same 409 also
    # covers a genuinely nonexistent employee_id (never existed, or already
    # hard-deleted), which isn't accurately described as "archived" either.
    return AppException(
        status.HTTP_409_CONFLICT,
        error_code="EMPLOYEE_ARCHIVED",
        message=f"Employee '{employee_id}' is no longer available — please re-pick from the current roster.",
    )


async def assert_employee_active_for_assignment(db: AsyncSession, employee_id: UUID) -> None:
    """Story 7.5 (FR-27) AC5: rejects a stale Assignment-picker submission
    against an Employee archived (or hard-deleted) since the picker loaded.
    Called by assignments/service.py::create_assignment_service immediately
    after its role gate, before any write.

    Takes the same `FOR UPDATE` row lock delete_or_archive_employee_service
    uses (repository.get_employee_for_update) -- a plain (non-locking) read
    would not be race-safe here: Postgres's FK check on the Assignment
    INSERT only verifies the referenced employees row still exists, not its
    archived_at value, so an unlocked read could observe a pre-archive
    value, pass, and only then block on the INSERT's own implicit lock,
    proceeding once the archiving transaction commits regardless of the
    now-current archived_at. Locking here first makes this call block until
    any concurrent archive resolves and always see the freshest value."""
    employee = await repository.get_employee_for_update(db, employee_id)
    if employee is None or employee.archived_at is not None:
        raise _archived_conflict(employee_id)


async def delete_or_archive_employee_service(
    db: AsyncSession, *, current_user: CurrentUser, employee_id: UUID
) -> DeleteEmployeeResponse:
    """Removes an Employee who has left (Story 7.5, FR-27). HR_ADMIN-only
    (AD-6). Hard-deletes if the Employee has zero Assignment history ever
    (AC1); archives instead (archived_at set) if they have any (AC2) --
    decided atomically via a `FOR UPDATE` row lock on the employees row
    (repository.get_employee_for_update), which blocks any concurrent
    Assignment-creation targeting this employee for the whole duration of
    this call (Postgres takes an implicit FOR KEY SHARE lock on the
    referenced employees row for such an INSERT, which conflicts with
    FOR UPDATE) -- see repository.get_employee_for_update's docstring for
    the full reasoning.

    `_has_any_history_for_employee` (code review, 2026-09-12) pre-checks
    every FK relationship that could block a hard-delete -- Assignment
    target/assigner/deleter, AssignmentOverride set/reversed actor, and
    AdminApiKey/ContentCatalog admin actor -- so an HR Admin who has acted
    in any of those roles for *other* employees is correctly archived
    without ever attempting (and failing) a hard-delete first. The
    `IntegrityError` fallback below remains as a defensive backstop only,
    for any FK this pre-check doesn't yet know about (e.g. a future
    migration adding a new `employees.id` reference) -- narrowed (code
    review) to only treat an actual foreign-key-violation as "archive
    instead", re-raising anything else rather than silently reporting an
    unrelated DB defect as a successful 200.

    Self-deletion is rejected outright (code review): an HR Admin archiving
    or hard-deleting their own row would immediately invalidate their own
    session on the very next request (AC4) with no recovery path (no
    un-archive feature exists). Re-archiving an already-archived employee is
    a no-op (code review): without this check, clicking Delete/Archive again
    on an already-archived row would silently overwrite `archived_at` with a
    new, later timestamp, destroying the original audit trail FR-27 exists
    to preserve."""
    require_hr_admin(current_user)

    if str(employee_id) == current_user.user_id:
        raise AppException(
            status.HTTP_409_CONFLICT,
            error_code="CANNOT_DELETE_SELF",
            message="You cannot delete or archive your own account.",
        )

    employee = await repository.get_employee_for_update(db, employee_id)
    if employee is None:
        raise _not_found(employee_id)

    if employee.archived_at is not None:
        return DeleteEmployeeResponse(action="archived")

    has_history = await _has_any_history_for_employee(db, employee_id)

    if not has_history:
        try:
            await auth_repository.delete_account(db, id=employee_id)
            await repository.hard_delete_employee(db, employee)
            return DeleteEmployeeResponse(action="deleted")
        except IntegrityError as exc:
            # SQLSTATE 23503 = foreign_key_violation (Postgres) -- some
            # other FK (assigned_by/deleted_by/set_by/reversed_by/admin_id/
            # attached_by) still references this row despite the pre-check
            # above (e.g. a future migration adding a new employees.id
            # reference this pre-check doesn't know about yet). Any other
            # IntegrityError is a genuine, unexpected DB defect and must not
            # be silently reported as a successful archive.
            if getattr(exc.orig, "sqlstate", None) != "23503":
                raise
            logger.exception(
                "Hard-delete of employee %s failed on an unexpected FK reference; archiving instead",
                employee_id,
            )
            # rollback releases the FOR UPDATE lock and expires `employee`'s
            # attributes, so re-acquire both before falling through to the
            # archive path below.
            await db.rollback()
            employee = await repository.get_employee_for_update(db, employee_id)
            if employee is None:
                raise _not_found(employee_id) from None

    archived_at = datetime.now(timezone.utc)
    await repository.archive_employee(db, employee, archived_at)
    await auth_repository.update_account_archived_at(db, id=employee_id, archived_at=archived_at)
    return DeleteEmployeeResponse(action="archived")
