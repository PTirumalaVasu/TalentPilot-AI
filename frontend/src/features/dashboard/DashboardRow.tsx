import { formatDistanceToNow } from "date-fns";
import { AssignmentRow } from "../../types/dashboard";
import { StatusBadge } from "../../components/StatusBadge";
import { staleDaysSince, formatStaleDaysText } from "../../lib/utils/staleness";

interface DashboardRowProps {
  row: AssignmentRow;
  onViewDetails: (assignmentId: string) => void;
}

export function DashboardRow({ row, onViewDetails }: DashboardRowProps) {
  const progressPercent = row.status_percentage || 0;

  // Story 5-6, AC9 (closing Story 5-1's own never-built stale-highlight AC):
  // never color-only -- pair the red highlight with literal staleness text,
  // via the shared staleness helper (code review finding: was duplicated
  // inline here and in ProvenanceDrillDownModal.tsx). Code review round 2:
  // the text must ALWAYS accompany the color, including at the 0-day
  // boundary -- an earlier fix suppressed the text at 0 days, which left the
  // red highlight as a color-only signal (a real NFR-A2 regression); fixed
  // by having formatStaleDaysText() itself return distinct, non-blank
  // wording at 0 days ("Not updated today") instead of conditionally hiding it.
  const isStale = row.provenance === "Needs Attention";
  const staleDays = isStale ? staleDaysSince(row.last_updated) : null;

  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      <td className="px-4 py-3 text-gray-900">{row.employee_name}</td>
      <td className="px-4 py-3 text-gray-700">{row.skill_name}</td>
      <td className="px-4 py-3">
        <StatusBadge
          status={row.status}
          percentage={row.status_percentage}
          employeeName={row.employee_name}
          skillName={row.skill_name}
        />
      </td>
      <td className="px-4 py-3">
        <div className="w-24 h-2 bg-gray-100 rounded-full overflow-hidden">
          <div className="h-full bg-blue-600" style={{ width: `${progressPercent}%` }}></div>
        </div>
      </td>
      <td className={`px-4 py-3 text-sm ${isStale ? "text-red-700 font-medium" : "text-gray-500"}`}>
        {formatDistanceToNow(new Date(row.last_updated), { addSuffix: true })}
        {isStale && ` (${formatStaleDaysText(staleDays!)})`}
      </td>
      <td className="px-4 py-3">
        <button
          onClick={() => onViewDetails(row.assignment_id)}
          aria-label={`View details for ${row.employee_name} ${row.skill_name}`}
          className="text-blue-600 hover:underline text-sm font-medium"
        >
          View Details
        </button>
      </td>
    </tr>
  );
}
