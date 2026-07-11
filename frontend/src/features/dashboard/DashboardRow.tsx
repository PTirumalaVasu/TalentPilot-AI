/**
 * Single row in the dashboard grid (Story 5-1).
 */
import { formatDistanceToNow } from "date-fns";
import { AssignmentRow } from "../../types/dashboard";
import { StatusBadge } from "../../components/StatusBadge";
import { Button } from "../../components/ui/button";

interface DashboardRowProps {
  row: AssignmentRow;
  onViewDetails: (assignmentId: string) => void;
}

export function DashboardRow({ row, onViewDetails }: DashboardRowProps) {
  // AC3: Format last_updated as relative time (with error handling for invalid timestamps)
  let lastUpdatedRelative: string;
  try {
    const date = new Date(row.last_updated);
    if (isNaN(date.getTime())) {
      lastUpdatedRelative = "Unknown";
    } else {
      lastUpdatedRelative = formatDistanceToNow(date, {
        addSuffix: true,
      });
    }
  } catch (error) {
    lastUpdatedRelative = "Unknown";
  }

  return (
    <tr className="border-b hover:bg-gray-50">
      {/* AC1: Employee Name column */}
      <td className="px-4 py-3 text-sm">{row.employee_name}</td>

      {/* AC1: Skill Name column */}
      <td className="px-4 py-3 text-sm">{row.skill_name}</td>

      {/* AC1/AC2: Status Badge column (never color-only per AC2) */}
      <td className="px-4 py-3">
        <StatusBadge status={row.status} percentage={row.status_percentage} />
      </td>

      {/* AC1/AC3: Last Updated column (relative time, never ISO-8601) */}
      <td className="px-4 py-3 text-sm text-gray-600">{lastUpdatedRelative}</td>

      {/* AC1/AC4: Actions column ([View Details] button always visible) */}
      <td className="px-4 py-3">
        <Button
          onClick={() => onViewDetails(row.assignment_id)}
          variant="outline"
          size="sm"
          aria-label={`View details for ${row.employee_name} ${row.skill_name}`}
        >
          View Details
        </Button>
      </td>
    </tr>
  );
}
