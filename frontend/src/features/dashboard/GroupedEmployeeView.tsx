import { AssignmentRow } from "../../types/dashboard";
import { DashboardRow } from "./DashboardRow";

interface GroupedEmployeeViewProps {
  employeeName: string;
  assignments: AssignmentRow[];
  onViewDetails: (assignmentId: string) => void;
  onViewEmployeeSummary: (employeeName: string) => void;
  isExpanded: boolean;
  onToggleExpand: (employeeName: string) => void;
}

export function GroupedEmployeeView({
  employeeName,
  assignments,
  onViewDetails,
  onViewEmployeeSummary,
  isExpanded,
  onToggleExpand,
}: GroupedEmployeeViewProps) {
  const completedCount = assignments.filter((a) => a.status === "Completed").length;
  const inProgressCount = assignments.filter((a) => a.status === "In Progress").length;

  return (
    <div className="mb-6 border border-gray-200 rounded-lg overflow-hidden">
      {/* Group Header - Collapsible */}
      <button
        onClick={() => onToggleExpand(employeeName)}
        className="w-full px-4 py-3 bg-gray-50 border-b border-gray-200 hover:bg-gray-100 transition-colors flex items-center justify-between"
      >
        <div className="flex items-center gap-3 text-left">
          <span className="text-lg font-semibold text-gray-900">{employeeName}</span>
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
            {assignments.length} skill{assignments.length !== 1 ? "s" : ""}
          </span>
          {completedCount > 0 && (
            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
              {completedCount} completed
            </span>
          )}
          {inProgressCount > 0 && (
            <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
              {inProgressCount} in progress
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onViewEmployeeSummary(employeeName);
            }}
            className="px-3 py-1 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded transition-colors"
          >
            View Summary
          </button>
          <span className={`text-gray-400 transition-transform ${isExpanded ? "rotate-180" : ""}`}>
            ▼
          </span>
        </div>
      </button>

      {/* Group Content - Collapsible */}
      {isExpanded && (
        <div className="divide-y divide-gray-100 bg-white">
          <table className="w-full text-sm">
            <tbody>
              {assignments.map((row) => (
                <DashboardRow
                  key={row.assignment_id}
                  row={row}
                  onViewDetails={onViewDetails}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
