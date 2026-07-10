"""Tests for assignments/schemas.py Pydantic request/response models (Story 3.1 AC3, AC6)."""
import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.assignments.schemas import AssignmentResponse, AssignmentStatus, CreateAssignmentRequest


def test_create_assignment_request_accepts_valid_uuids():
    employee_id = uuid.uuid4()
    skill_id = uuid.uuid4()

    request = CreateAssignmentRequest(employee_id=employee_id, skill_id=skill_id)

    assert request.employee_id == employee_id
    assert request.skill_id == skill_id


def test_create_assignment_request_rejects_missing_employee_id():
    with pytest.raises(ValidationError) as exc_info:
        CreateAssignmentRequest(skill_id=uuid.uuid4())

    assert any(err["loc"] == ("employee_id",) for err in exc_info.value.errors())


def test_create_assignment_request_rejects_missing_skill_id():
    with pytest.raises(ValidationError) as exc_info:
        CreateAssignmentRequest(employee_id=uuid.uuid4())

    assert any(err["loc"] == ("skill_id",) for err in exc_info.value.errors())


def test_create_assignment_request_rejects_malformed_uuid_string():
    with pytest.raises(ValidationError):
        CreateAssignmentRequest(employee_id="not-a-uuid", skill_id=uuid.uuid4())


def test_create_assignment_request_rejects_client_supplied_status():
    """AC3: status/provenance must never be client-supplied — enforced by
    extra="forbid", not just by omission from the field list."""
    with pytest.raises(ValidationError) as exc_info:
        CreateAssignmentRequest(employee_id=uuid.uuid4(), skill_id=uuid.uuid4(), status="COMPLETED")

    assert any(err["type"] == "extra_forbidden" for err in exc_info.value.errors())


def test_assignment_response_serializes_all_fields():
    assignment_id = uuid.uuid4()
    employee_id = uuid.uuid4()
    skill_id = uuid.uuid4()
    content_id = uuid.uuid4()
    assigned_by = uuid.uuid4()
    assigned_at = datetime.now(timezone.utc)

    response = AssignmentResponse(
        id=assignment_id,
        employee_id=employee_id,
        skill_id=skill_id,
        content_id=content_id,
        assigned_at=assigned_at,
        assigned_by=assigned_by,
        status=AssignmentStatus.NOT_STARTED,
        provenance="Assigned · Awaiting first watch",
    )

    assert response.id == assignment_id
    assert response.employee_id == employee_id
    assert response.skill_id == skill_id
    assert response.content_id == content_id
    assert response.assigned_by == assigned_by
    assert response.assigned_at == assigned_at
    assert response.status == AssignmentStatus.NOT_STARTED
    assert response.provenance == "Assigned · Awaiting first watch"


def test_assignment_response_content_id_is_optional():
    response = AssignmentResponse(
        id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        skill_id=uuid.uuid4(),
        content_id=None,
        assigned_at=datetime.now(timezone.utc),
        assigned_by=uuid.uuid4(),
        status=AssignmentStatus.NOT_STARTED,
        provenance="Assigned · Awaiting first watch",
    )

    assert response.content_id is None


def test_assignment_response_rejects_invalid_status_value():
    with pytest.raises(ValidationError):
        AssignmentResponse(
            id=uuid.uuid4(),
            employee_id=uuid.uuid4(),
            skill_id=uuid.uuid4(),
            content_id=None,
            assigned_at=datetime.now(timezone.utc),
            assigned_by=uuid.uuid4(),
            status="NOT_A_REAL_STATUS",
            provenance="Assigned · Awaiting first watch",
        )


def test_assignment_response_builds_from_orm_attributes():
    """AssignmentResponse must be buildable via model_validate(orm_obj, from_attributes=True)
    since the service layer will construct it from an Assignment ORM row plus a
    separately-computed status/provenance pair, not from a plain dict."""

    class _FakeOrmAssignment:
        def __init__(self):
            self.id = uuid.uuid4()
            self.employee_id = uuid.uuid4()
            self.skill_id = uuid.uuid4()
            self.content_id = None
            self.assigned_at = datetime.now(timezone.utc)
            self.assigned_by = uuid.uuid4()
            self.status = AssignmentStatus.NOT_STARTED
            self.provenance = "Assigned · Awaiting first watch"

    orm_obj = _FakeOrmAssignment()
    response = AssignmentResponse.model_validate(orm_obj, from_attributes=True)

    assert response.id == orm_obj.id
    assert response.status == AssignmentStatus.NOT_STARTED
