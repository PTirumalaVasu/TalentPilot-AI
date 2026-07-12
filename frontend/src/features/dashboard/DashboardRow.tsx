import { formatDistanceToNow } from "date-fns";
import { AssignmentRow } from "../../types/dashboard";
import { StatusBadge } from "../../components/StatusBadge";

interface DashboardRowProps {
  row: AssignmentRow;
  onViewDetails: (assignmentId: string) => void;
}

export function DashboardRow({ row, onViewDetails }: DashboardRowProps) {
  const progressPercent = row.status_percentage || 0;

  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      <td className="px-4 py-3 text-gray-900">{row.employee_name}</td>
      <td className="px-4 py-3 text-gray-700">{row.skill_name}</td>
      <td className="px-4 py-3">
        <StatusBadge status={row.status} percentage={row.status_percentage} />
      </td>
      <td className="px-4 py-3">
        <div className="w-24 h-2 bg-gray-100 rounded-full overflow-hidden">
          <div className="h-full bg-blue-600" style={{ width: `${progressPercent}%` }}></div>
        </div>
      </td>
      <td className="px-4 py-3 text-gray-500 text-sm">
        {formatDistanceToNow(new Date(row.last_updated), { addSuffix: true })}
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
