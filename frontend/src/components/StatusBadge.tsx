/**
 * Status badge component (AC2 - never color-only, always with text label).
 */
import { StatusType } from "../types/dashboard";

interface StatusBadgeProps {
  status: StatusType;
  percentage?: number | null;
}

export function StatusBadge({ status, percentage }: StatusBadgeProps) {
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

  // Build label with percentage for In Progress (AC2), with validation
  // If percentage is 0, should show "Not Started" instead of "In Progress (0%)"
  let label: string;
  if (percentage === 0) {
    // 0% watch position should display as "Not Started", not "In Progress (0%)"
    label = "Not Started";
  } else if (status === "In Progress" && percentage !== null && percentage !== undefined && percentage > 0) {
    label = `${status} (${percentage}%)`;
  } else {
    label = status;
  }

  return (
    <span
      className={`inline-flex items-center gap-1 px-3 py-1 rounded font-medium ${config.bg} ${config.text}`}
      role="status"
      aria-label={label}
    >
      <span aria-hidden="true">{config.icon}</span>
      <span>{label}</span>
    </span>
  );
}
