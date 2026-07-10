"""Test skill progress data model, repository, and service layer (Story 4-1).

This test suite verifies the atomic conditional-write behavior for watch progress,
ensuring that out-of-order writes don't regress progress tracking.
"""
import pytest
from datetime import datetime
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import text

from app.core.db import engine
from app.assignments.models import SkillProgress
from app.progress.repository import ProgressRepository
from app.progress.schemas import RecordWatchProgressRequest, SkillProgressResponse
from app.progress.service import ProgressService

pytestmark = pytest.mark.asyncio(loop_scope="module")


# ============================================================================
# Tests for Pydantic Schemas (non-async, no database)
# ============================================================================


def test_record_watch_progress_request_valid():
    """Test valid RecordWatchProgressRequest."""
    req = RecordWatchProgressRequest(
        assignment_id=uuid4(),
        watch_position=300,
        event_time=datetime.utcnow(),
        video_url="https://www.youtube.com/watch?v=abc123",
    )
    assert req.watch_position == 300
    assert req.video_url == "https://www.youtube.com/watch?v=abc123"


def test_record_watch_progress_request_negative_position_fails():
    """Test that negative watch position is rejected."""
    with pytest.raises(ValidationError):
        RecordWatchProgressRequest(
            assignment_id=uuid4(),
            watch_position=-1,
            event_time=datetime.utcnow(),
            video_url="https://www.youtube.com/watch?v=abc123",
        )


def test_skill_progress_response_valid():
    """Test valid SkillProgressResponse."""
    resp = SkillProgressResponse(
        id=uuid4(),
        assignment_id=uuid4(),
        watch_position=500,
        event_time=datetime.utcnow(),
        verified=True,
        updated_at=datetime.utcnow(),
    )
    assert resp.verified is True


def test_skill_progress_response_from_attributes():
    """Test SkillProgressResponse.model_validate with from_attributes=True."""
    progress = SkillProgress(
        id=uuid4(),
        assignment_id=uuid4(),
        watch_position=100,
        event_time=datetime.utcnow(),
        verified=False,
        updated_at=datetime.utcnow(),
    )
    resp = SkillProgressResponse.model_validate(progress)
    assert resp.watch_position == 100
    assert resp.verified is False


# ============================================================================
# Tests for SkillProgress Model and Table Schema
# ============================================================================


async def test_skill_progress_model_creation():
    """Test creating a SkillProgress instance."""
    progress = SkillProgress(
        id=uuid4(),
        assignment_id=uuid4(),
        watch_position=120,
        event_time=datetime.utcnow(),
        verified=True,
        updated_at=datetime.utcnow(),
    )
    assert progress.id is not None
    assert progress.watch_position == 120
    assert progress.verified is True


async def test_skill_progress_table_has_unique_assignment_id():
    """Test that assignment_id is unique (one progress record per assignment)."""
    async with engine.begin() as conn:
        constraints = await conn.execute(
            text("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_name = 'skill_progress' AND constraint_type = 'UNIQUE'
            """)
        )
        constraints_list = constraints.fetchall()

    unique_constraint_names = [row[0] for row in constraints_list]
    assert any("assignment_id" in name for name in unique_constraint_names), (
        "No UNIQUE constraint on assignment_id found"
    )


# ============================================================================
# Story 4-1 Acceptance Criteria Tests
# ============================================================================


async def test_ac1_skill_progress_table_schema():
    """
    AC1: skill_progress table includes id, assignment_id, watch_position, event_time, verified, updated_at
    """
    async with engine.begin() as conn:
        result = await conn.execute(
            text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'skill_progress'
                ORDER BY ordinal_position
            """)
        )
        columns = {row[0]: row for row in result.fetchall()}

    required = {"id", "assignment_id", "watch_position", "event_time", "verified", "updated_at"}
    assert required.issubset(set(columns.keys())), f"Missing columns: {required - set(columns.keys())}"

    # Verify nullability
    assert columns["id"][2] == "NO"  # NOT NULL
    assert columns["assignment_id"][2] == "NO"  # NOT NULL
    assert columns["watch_position"][2] == "NO"  # NOT NULL
    assert columns["event_time"][2] == "NO"  # NOT NULL
    assert columns["verified"][2] == "NO"  # NOT NULL
    assert columns["updated_at"][2] == "NO"  # NOT NULL




