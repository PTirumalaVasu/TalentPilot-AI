"""Service layer for the dashboard module (read-composition, no table ownership)."""
from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.assignments.models import Assignment, AssignmentOverride
from app.assignments.service import AssignmentsService
from app.content.service import match_content_for_skill
from app.dashboard.schemas import (
    AssignmentRowResponse,
    DashboardResponse,
    DashboardStatsResponse,
    EmployeeSegmentationResponse,
    ExperienceBucketResponse,
    ExperienceDistributionResponse,
    NeedsAttentionEntry,
)
from app.progress.service import STATUS_DISPLAY, ProgressService
from app.progress.models import SkillProgress

logger = logging.getLogger(__name__)

# Story 9.2 (FR-32, AR-28): PRD Open Question 20 -- this is a PM-drafted
# default, not user-confirmed, and therefore the item most likely to change
# once a real HR Admin sees the pie chart (addendum.md's own framing).
# Module-level constant, not a Settings/.env field, mirroring
# progress/service.py's NEEDS_ATTENTION_STALENESS_DAYS precedent -- lives
# here (not progress/service.py) because Employee Segmentation is a
# dashboard-owned aggregation (AR-26), not part of progress/'s AD-3
# per-Assignment Status/Provenance derivation authority.
ON_TRACK_THRESHOLD = 0.8

# Story 10.4 (FR-36): 7 contiguous, exhaustive experience-year buckets,
# locked 2026-09-15 -- a single named constant, not inlined, mirroring
# employees/service.py's TALENT_POOL_FLAG_DAYS precedent for a fixed,
# product-decided threshold. Lives here (not employees/service.py) because
# the Experience Distribution panel is a dashboard-owned aggregation
# (AR-26), same reasoning as ON_TRACK_THRESHOLD above. `max_years=None`
# marks the open-ended final bucket ("20+ yrs").
EXPERIENCE_BUCKETS: list[tuple[str, int, int | None]] = [
    ("0–4 yrs", 0, 4),
    ("5–7 yrs", 5, 7),
    ("8–9 yrs", 8, 9),
    ("10–11 yrs", 10, 11),
    ("12–14 yrs", 12, 14),
    ("15–19 yrs", 15, 19),
    ("20+ yrs", 20, None),
]


class DashboardService:
    """Service layer for HR Admin dashboard (read composition, no table ownership per AD-1)."""

    @staticmethod
    async def get_dashboard_assignments(
        session: AsyncSession,
        hr_admin_id: UUID,
        page: int = 1,
        page_size: int = 50,
        search: str | None = None,
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
            search: Story 10.6 (FR-38) -- optional case-insensitive substring
                match against Employee name OR Skill name, passed straight
                through to AssignmentsService/the repository (AD-1: this
                module owns no table, so it never filters rows itself).

        Returns:
            DashboardResponse with paginated assignments and computed Status badges
        """
        from app.progress.repository import ProgressRepository

        # Get all assignments for this HR Admin (AD-6: HR Admin sees all their assignments)
        assignments_page = await AssignmentsService.list_assignments_for_hr(
            session, hr_admin_id=hr_admin_id, page=page, page_size=page_size, search=search
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

            # Video duration in seconds (AD-3: progress/ is the single derivation
            # authority for this -- ProgressRepository.parse_duration_seconds
            # handles the real ISO-8601 duration strings YouTube-ingested
            # content stores, e.g. "PT4H20M39S", which a naive int() cast
            # can't parse and previously silently zeroed out every row's
            # percentage).
            video_duration = ProgressRepository.get_video_duration(assignment)
            if video_duration is None and progress is not None and progress.watch_position > 0:
                # Assignment.content_id is frequently unset (the "assign
                # without content" flow, or older rows created before a
                # match existed) -- fall back to the same live semantic
                # match the employee's Content Discovery grid already uses
                # (assignments/service.py's list_my_assignments), so a real,
                # nonzero watch signal isn't stuck at an indeterminate 0%/
                # never-Completed here just because no content_id was ever
                # recorded on the Assignment row itself. Only attempted when
                # there's an actual watch signal to explain -- a
                # NOT_STARTED row has nothing to gain from a duration.
                matched_content = await match_content_for_skill(session, assignment.skill_id)
                if matched_content is not None and matched_content.metadata:
                    video_duration = ProgressRepository.parse_duration_seconds(
                        matched_content.metadata.get("duration")
                    )

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
    async def get_dashboard_stats(session: AsyncSession) -> DashboardStatsResponse:
        """
        Org-wide stats + Assignment Progress breakdown for the Skill
        Assignment Dashboard landing page (Story 9.1, FR-31/FR-32).

        Read-composition only (AR-26, no new table): reuses
        `assignments/`'s org-wide read, `employees/`'s active-count read, and
        `progress/`'s single Status/Provenance derivation authority (AD-3) --
        does not recompute Status independently.
        """
        from app.assignments.repository import list_assignments_for_dashboard
        from app.employees.repository import count_active_employees
        from app.progress.repository import ProgressRepository

        all_assignments = await list_assignments_for_dashboard(session)

        # AC3: an archived Employee's assignments are excluded from every
        # count here, not just from total_employees. `list_assignments_for_dashboard`
        # only filters Assignment.active -- it does not know about
        # Employee.archived_at -- so that exclusion happens here instead of
        # widening the (dead-but-resurrected) repository query's own filter.
        assignments = [a for a in all_assignments if a.employee is not None and a.employee.archived_at is None]

        # `list_assignments_for_dashboard` already eager-loads `.progress`
        # (unlike `list_assignments_for_hr`, which is why
        # get_dashboard_assignments above needs a separate
        # _batch_load_progress step) -- only overrides need a batch fetch here.
        assignment_ids = [a.id for a in assignments]
        override_map = await DashboardService._batch_load_overrides(session, assignment_ids)

        completed_count = 0
        in_progress_count = 0
        not_started_count = 0

        for assignment in assignments:
            progress = assignment.progress
            override = override_map.get(assignment.id)

            # Deliberately NOT the same fallback get_dashboard_assignments uses
            # above. That fallback calls match_content_for_skill, which can
            # re-embed Content as a side effect (content/service.py) when no
            # match clears the threshold -- a real write, contradicting this
            # endpoint's AC4 "read-only" guarantee. Code review 2026-09-13,
            # decision-needed #1: user chose to harden this endpoint rather
            # than accept the inherited side effect, even though the sibling
            # endpoint still has it. Consequence: an assignment with partial
            # watch progress but no known duration (no content_id, or
            # content with no duration metadata) classifies as Not Started
            # here instead of a percentage-based In Progress/Completed --
            # slightly less accurate than the sibling endpoint, in exchange
            # for genuinely no writes from a GET.
            video_duration = ProgressRepository.get_video_duration(assignment)

            status, _, _, _ = DashboardService._compute_status_and_provenance_from_data(
                assignment, progress, override, video_duration=video_duration
            )

            if status == "Completed":
                completed_count += 1
            elif status == "In Progress":
                in_progress_count += 1
            else:
                not_started_count += 1

        total_employees = await count_active_employees(session)
        total_skills_assigned = len(assignments)
        overall_percent = round(completed_count / total_skills_assigned * 100) if total_skills_assigned else 0

        return DashboardStatsResponse(
            total_employees=total_employees,
            total_skills_assigned=total_skills_assigned,
            total_completed=completed_count,
            completed_count=completed_count,
            in_progress_count=in_progress_count,
            not_started_count=not_started_count,
            overall_percent=overall_percent,
        )

    @staticmethod
    async def get_employee_segmentation(session: AsyncSession) -> EmployeeSegmentationResponse:
        """
        Per-Employee On Track / In Progress / Needs Attention classification
        for the Skill Assignment Dashboard's pie chart (Story 9.2, FR-32,
        AR-27, AR-28).

        Read-composition only (AR-26, no new table): reuses the exact same
        org-wide read + archived-Employee filter + override batch-load
        `get_dashboard_stats` (Story 9.1) already introduced -- the only new
        step this method adds is grouping that same filtered Assignment list
        by Employee (AR-27's "first per-Employee, full-roster aggregation
        read" -- no new SQL query, just a new in-memory groupby over data
        already fetched by one query + one batch-load).

        Classification priority (exact order, epics.md Story 9.2 AC1):
        1. Needs Attention -- at least one Assignment's derived provenance is
           "Needs Attention". Overrides everything else.
        2. On Track -- no Needs Attention assignments, and completion rate
           (Completed / total active Assignments for that Employee) >=
           ON_TRACK_THRESHOLD.
        3. In Progress -- everything else (explicit catch-all, including
           Employees at 0% complete -- there is deliberately no separate
           "Not Started" segment, per FR-32 consequence #3).

        An Employee with zero active Assignments never appears in any group
        here (they simply have no rows in the filtered Assignment list), so
        they are excluded "for free" -- no separate exclusion check needed.
        """
        from app.assignments.repository import list_assignments_for_dashboard
        from app.progress.repository import ProgressRepository

        all_assignments = await list_assignments_for_dashboard(session)

        # Same archived-Employee exclusion as get_dashboard_stats (Story
        # 9.1) -- list_assignments_for_dashboard only filters
        # Assignment.active, not Employee.archived_at.
        assignments = [a for a in all_assignments if a.employee is not None and a.employee.archived_at is None]

        assignment_ids = [a.id for a in assignments]
        override_map = await DashboardService._batch_load_overrides(session, assignment_ids)

        by_employee: dict[UUID, list[Assignment]] = {}
        for assignment in assignments:
            by_employee.setdefault(assignment.employee_id, []).append(assignment)

        on_track_count = 0
        in_progress_count = 0
        needs_attention_entries: list[NeedsAttentionEntry] = []
        needs_attention_employee_count = 0

        for employee_id, employee_assignments in by_employee.items():
            employee_name = employee_assignments[0].employee.name if employee_assignments[0].employee else "Unknown"
            completed_count = 0
            flagged_for_this_employee: list[NeedsAttentionEntry] = []

            for assignment in employee_assignments:
                progress = assignment.progress
                override = override_map.get(assignment.id)
                # Deliberately the same no-side-effect video_duration
                # resolution as get_dashboard_stats -- no match_content_for_skill
                # fallback, since that can trigger a Content re-embed write,
                # which this read-only endpoint must not do.
                video_duration = ProgressRepository.get_video_duration(assignment)

                status, provenance, _, _ = DashboardService._compute_status_and_provenance_from_data(
                    assignment, progress, override, video_duration=video_duration
                )

                if status == "Completed":
                    completed_count += 1

                if provenance == "Needs Attention":
                    skill_name = assignment.skill.name if assignment.skill else "Unknown"
                    flagged_for_this_employee.append(
                        NeedsAttentionEntry(
                            employee_id=employee_id,
                            employee_name=employee_name,
                            assignment_id=assignment.id,
                            skill_id=assignment.skill_id,
                            skill_name=skill_name,
                        )
                    )

            if flagged_for_this_employee:
                needs_attention_employee_count += 1
                needs_attention_entries.extend(flagged_for_this_employee)
            elif completed_count / len(employee_assignments) >= ON_TRACK_THRESHOLD:
                on_track_count += 1
            else:
                in_progress_count += 1

        return EmployeeSegmentationResponse(
            on_track_count=on_track_count,
            in_progress_count=in_progress_count,
            needs_attention_count=needs_attention_employee_count,
            needs_attention=needs_attention_entries,
        )

    @staticmethod
    async def get_experience_distribution(session: AsyncSession) -> ExperienceDistributionResponse:
        """
        Headcount broken down by years of experience for the Employees
        page's Experience Distribution panel (Story 10.4, FR-36).

        Read-composition only (AR-26, no new table): reads
        `employees/`'s active, non-null `experience_years` values via
        `list_active_employee_experience_years` (AD-1 -- dashboard/ never
        queries the `employees` table directly) and buckets them in Python
        against the fixed `EXPERIENCE_BUCKETS` ranges, mirroring
        `get_employee_segmentation`'s existing fetch-then-groupby-in-Python
        shape rather than issuing 7 separate range-COUNT queries.

        Distinct from `get_employee_segmentation`'s On Track/In Progress/
        Needs Attention chart -- this is a headcount-by-tenure view with no
        relationship to Assignment/watch-progress status.
        """
        from app.employees.repository import list_active_employee_experience_years

        years_values = await list_active_employee_experience_years(session)

        buckets = []
        for label, min_years, max_years in EXPERIENCE_BUCKETS:
            count = sum(
                1
                for years in years_values
                if years >= min_years and (max_years is None or years <= max_years)
            )
            buckets.append(
                ExperienceBucketResponse(label=label, min_years=min_years, max_years=max_years, count=count)
            )

        return ExperienceDistributionResponse(buckets=buckets)

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
