"""Service layer for the employees module.

Story 7.1 added the bcrypt hash/verify helpers. Story 7.2 (create, FR-24)
adds password generation and the first real CRUD service method.
Cross-module callers must go through here (AD-1).
"""
import asyncio
import logging
import secrets

import bcrypt
from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import repository as auth_repository
from app.auth.schemas import CurrentUser
from app.auth.service import require_hr_admin
from app.core.errors import AppException
from app.employees import repository
from app.employees.schemas import CreateEmployeeRequest, EmployeeCreatedResponse, EmployeeResponse

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


async def list_employees_service(db: AsyncSession, *, current_user: CurrentUser) -> list[EmployeeResponse]:
    """Full Employee roster (Story 7.3, FR-25) -- HR_ADMIN-only (AD-6/FR-14),
    mirrors content.service.list_skills_with_content's require_hr_admin
    gate. Search/filter/pagination are deliberately not implemented here --
    the frontend fetches this full list once and does all of that
    client-side (Story 7.3 Scope Note 2), matching the SkillsPage/Story 6.10
    precedent."""
    require_hr_admin(current_user)
    employees = await repository.list_all_employees(db)
    return [EmployeeResponse.model_validate(employee) for employee in employees]


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
