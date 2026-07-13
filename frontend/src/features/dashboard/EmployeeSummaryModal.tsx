import { AssignmentRow } from "../../types/dashboard";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDistanceToNow } from "date-fns";

interface EmployeeSummaryModalProps {
  open: boolean;
  employeeName: string;
  employeeAssignments: AssignmentRow[];
  onClose: () => void;
  onViewSkillDetails?: (assignmentId: string) => void;
}

export function EmployeeSummaryModal({
  open,
  employeeName,
  employeeAssignments,
  onClose,
  onViewSkillDetails,
}: EmployeeSummaryModalProps) {
  if (!open) return null;

  const totalAssignments = employeeAssignments.length;
  const completedCount = employeeAssignments.filter((a) => a.status === "Completed").length;
  const inProgressCount = employeeAssignments.filter((a) => a.status === "In Progress").length;
  const notStartedCount = employeeAssignments.filter((a) => a.status === "Not Started").length;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{employeeName}</h2>
            <p className="text-sm text-gray-500 mt-1">
              {totalAssignments} skill assignment{totalAssignments !== 1 ? "s" : ""}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{completedCount}</div>
            <div className="text-xs text-gray-600 mt-1">Completed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{inProgressCount}</div>
            <div className="text-xs text-gray-600 mt-1">In Progress</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600">{notStartedCount}</div>
            <div className="text-xs text-gray-600 mt-1">Not Started</div>
          </div>
        </div>

        {/* Skills Table */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Assigned Skills</h3>
          {employeeAssignments.length === 0 ? (
            <p className="text-gray-500 text-sm">No skills assigned to this employee.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm bg-white border border-gray-200 rounded-lg">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-2 text-left font-medium text-gray-700">Skill Name</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-700">Status</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-700">Progress</th>
                    <th className="px-4 py-2 text-left font-medium text-gray-700">Last Updated</th>
                    <th className="px-4 py-2 text-center font-medium text-gray-700">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {employeeAssignments.map((assignment) => (
                    <tr
                      key={assignment.assignment_id}
                      className="border-b border-gray-100 hover:bg-gray-50"
                    >
                      <td className="px-4 py-3 text-gray-900">{assignment.skill_name}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={assignment.status} percentage={assignment.status_percentage} />
                      </td>
                      <td className="px-4 py-3">
                        <div className="w-20 h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-600"
                            style={{ width: `${assignment.status_percentage || 0}%` }}
                          />
                        </div>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">
                        {formatDistanceToNow(new Date(assignment.last_updated), { addSuffix: true })}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => onViewSkillDetails?.(assignment.assignment_id)}
                          className="text-blue-600 hover:underline text-xs font-medium"
                          title="View skill details"
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
