"""Service layer for the dashboard module (read-composition, no table ownership)."""
from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import AssignmentOverride
from app.assignments.service import AssignmentsService
from app.dashboard.schemas import DashboardResponse, AssignmentRowResponse
from app.progress.service import STATUS_DISPLAY, ProgressService
from app.progress.models import SkillProgress

logger = logging.getLogger(__name__)


class DashboardService:
    """Service layer for HR Admin dashboard (read composition, no table ownership per AD-1)."""

    @staticmethod
    async def get_dashboard_assignments(
        session: AsyncSession,
        hr_admin_id: UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> DashboardResponse:
        """
        Fetch all Assignments for an HR Admin with computed Status & Provenance.

        Implements AD-3 single derivation authority: Status and Provenance are
        computed here from {watch signal, self-report staleness, active HR override}.

        Args:
            session: AsyncSession for database operations
            hr_admin_id: UUID of the HR Admin requesting the dashboard
            page: Page number (1-indexed)
            page_size: Number of rows per page

        Returns:
            DashboardResponse with paginated assignments and computed Status badges
        """
        from app.progress.repository import ProgressRepository

        # Get all assignments for this HR Admin (AD-6: HR Admin sees all their assignments)
        assignments_page = await AssignmentsService.list_assignments_for_hr(
            session, hr_admin_id=hr_admin_id, page=page, page_size=page_size
        )

        # Batch-load all progress records and overrides for this page (prevents N+1 queries)
        assignment_ids = [a.id for a in assignments_page.assignments]
        progress_map = await DashboardService._batch_load_progress(session, assignment_ids)
        override_map = await DashboardService._batch_load_overrides(session, assignment_ids)

        rows = []
        for assignment in assignments_page.assignments:
            # Derive Status & Provenance for each assignment (AD-3)
            progress = progress_map.get(assignment.id)
            override = override_map.get(assignment.id)

            # Extract video duration from content metadata if available (coerce to int for safety)
            video_duration = None
            if assignment.content and assignment.content.content_metadata:
                duration_raw = assignment.content.content_metadata.get("duration")
                if duration_raw is not None:
                    try:
                        video_duration = int(duration_raw) if isinstance(duration_raw, (int, float, str)) else None
                    except (ValueError, TypeError):
                        video_duration = None
                        logger.warning(f"Invalid video duration for assignment {assignment.id}: {duration_raw}")

            status, provenance, percentage, last_updated = DashboardService._compute_status_and_provenance_from_data(
                assignment, progress, override, video_duration=video_duration
            )

            employee_name = assignment.employee.name if assignment.employee else "Unknown"
            employee_group = assignment.employee.group if assignment.employee else None
            skill_name = assignment.skill.name if assignment.skill else "Unknown"

            row = AssignmentRowResponse(
                assignment_id=assignment.id,
                employee_id=assignment.employee_id,
                employee_name=employee_name,
                employee_group=employee_group,
                skill_id=assignment.skill_id,
                skill_name=skill_name,
                status=status,
                status_percentage=percentage,
                provenance=provenance,
                last_updated=last_updated,
                assignment_created_at=assignment.assigned_at,
            )
            rows.append(row)

        return DashboardResponse(
            assignments=rows,
            total_count=assignments_page.total_count,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    async def _batch_load_progress(
        session: AsyncSession, assignment_ids: list[UUID]
    ) -> dict[UUID, SkillProgress]:
        """Batch-load all progress records for assignments (prevents N+1)."""
        from app.progress.repository import ProgressRepository

        progress_records = await ProgressRepository.get_progress_for_assignments(session, assignment_ids)
        return {p.assignment_id: p for p in progress_records}

    @staticmethod
    async def _batch_load_overrides(
        session: AsyncSession, assignment_ids: list[UUID]
    ) -> dict[UUID, AssignmentOverride]:
        """Batch-load all active override records for assignments (prevents N+1)."""
        from app.progress.repository import ProgressRepository

        override_records = await ProgressRepository.get_active_overrides_for_assignments(session, assignment_ids)
        return {o.assignment_id: o for o in override_records}

    @staticmethod
    def _compute_status_and_provenance_from_data(
        assignment, progress: SkillProgress | None, override: AssignmentOverride | None, video_duration: int | None = None
    ) -> tuple[str, str, int | None, datetime]:
        """
        Compute Status, Provenance, percentage, and last_updated from pre-fetched data.

        Implements AD-3/AR-3 single derivation authority — delegates entirely to
        `ProgressService.get_provenance_detail` (Story 5.2) rather than
        recomputing this independently, which is what this method used to do
        before Story 5.2's consolidation (see that story's Finding 3: the
        duplication risked the grid's badge and the drill-down modal silently
        showing different Provenance for the same assignment).

        Args:
            assignment: The Assignment record
            progress: Optional SkillProgress record
            override: Optional AssignmentOverride record (must have set_by_user eager-loaded)
            video_duration: Optional video duration in seconds (from content metadata)

        Returns:
            Tuple of (status_str, provenance_str, percentage_or_none, last_updated_datetime)
        """
        detail = ProgressService.get_provenance_detail(assignment, progress, override, video_duration)
        status = STATUS_DISPLAY[detail.status]
        percentage = detail.percentage if status == "In Progress" else None
        return status, detail.provenance, percentage, detail.last_updated
