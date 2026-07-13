/**
 * Status badge component (AC2 - never color-only, always with text label).
 */
import { StatusType } from "../types/dashboard";

interface StatusBadgeProps {
  status: StatusType;
  percentage?: number | null;
  /** Row context for the full "{Employee} {Skill}: {Status}..." announcement
   * (Story 5-6, AC2). Optional: the drill-down modal's call site already
   * states Employee/Skill in its own header, so passing these there would
   * double-announce -- only DashboardRow passes them. */
  employeeName?: string;
  skillName?: string;
}

export function StatusBadge({ status, percentage, employeeName, skillName }: StatusBadgeProps) {
  // Config for each status (AC2: text + optional icon + color)
  const statusConfig: Record<
    StatusType,
    { bg: string; text: string; icon: string }
  > = {
    "Not Started": {
      bg: "bg-gray-100",
      text: "text-gray-800",
      icon: "○",
    },
    "In Progress": {
      bg: "bg-yellow-100",
      text: "text-yellow-800",
      icon: "▶",
    },
    Completed: {
      bg: "bg-green-100",
      text: "text-green-800",
      icon: "✓",
    },
  };

  const config = statusConfig[status];

  // Build label with percentage for In Progress (AC2). Trust the derived
  // `status`, don't infer it from `percentage` -- an unknown/unparseable
  // video duration legitimately produces (status: "In Progress", percentage: 0)
  // for content that has genuinely been watched (indeterminate %, not zero
  // watched); inferring "Not Started" from percentage===0 alone silently
  // mislabels that case (code review finding, Story 5-2).
  let label: string;
  if (status === "In Progress" && percentage !== null && percentage !== undefined && percentage > 0) {
    label = `${status} (${percentage}%)`;
  } else {
    label = status;
  }

  // AC2: full "{Employee} {Skill}: {Status}..." announcement when row context
  // is available (DashboardRow); otherwise fall back to status-only (drill-down).
  const ariaLabel = employeeName && skillName ? `${employeeName} ${skillName}: ${label}` : label;

  return (
    <span
      className={`inline-flex items-center gap-1 px-3 py-1 rounded font-medium ${config.bg} ${config.text}`}
      role="status"
      // aria-live="off" mutes role="status"'s implicit live-region behavior
      // (code review finding, Story 5-6): DashboardPage.tsx already owns a
      // dedicated aria-live="polite" region for poll-driven Status changes
      // (AC4) -- without this, the badge's own live-region semantics would
      // double-announce the same change. Focus-driven announcement (AC2)
      // doesn't need a live region at all; any focusable element's
      // aria-label is announced on focus regardless of aria-live.
      aria-live="off"
      aria-label={ariaLabel}
      tabIndex={0}
    >
      <span aria-hidden="true">{config.icon}</span>
      <span>{label}</span>
    </span>
  );
}
