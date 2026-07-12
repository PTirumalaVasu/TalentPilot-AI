import { useEffect, useState, useImperativeHandle, forwardRef } from "react";
import { dashboardApi } from "../../lib/api/dashboardApi";
import { DashboardResponse, AssignmentRow } from "../../types/dashboard";
import { DashboardRow } from "./DashboardRow";
import { ProvenanceDrillDownModal } from "./ProvenanceDrillDownModal";
import { Button } from "../../components/ui/button";

interface DashboardState {
  assignments: AssignmentRow[];
  loading: boolean;
  error: string | null;
  page: number;
  pageSize: number;
  totalCount: number;
  requestId: number;
}

interface DashboardPageProps {
  onNewAssignment: () => void;
}

export interface DashboardPageHandle {
  refreshGrid: () => void;
}

export const DashboardPage = forwardRef<DashboardPageHandle, DashboardPageProps>(
  function DashboardPageComponent({ onNewAssignment }, ref) {
    const [state, setState] = useState<DashboardState>({
      assignments: [],
      loading: true,
      error: null,
      page: 1,
      pageSize: 50,
      totalCount: 0,
      requestId: 0,
    });
    const [selectedAssignmentId, setSelectedAssignmentId] = useState<string | null>(null);

    function handleViewDetails(assignmentId: string) {
      setSelectedAssignmentId(assignmentId);
    }

    function handleCloseDrillDown() {
      setSelectedAssignmentId(null);
    }

    useImperativeHandle(ref, () => ({
      refreshGrid: () => fetchDashboard(),
    }));

    useEffect(() => {
      const timer = setTimeout(() => {
        fetchDashboard();
      }, 150);

      return () => clearTimeout(timer);
    }, [state.page, state.pageSize]);

    async function fetchDashboard() {
      const currentRequestId = state.requestId + 1;
      setState((prev) => ({ ...prev, requestId: currentRequestId, loading: true, error: null, assignments: [] }));

      try {
        const response = await dashboardApi.getDashboard(state.page, state.pageSize);

        setState((prev) => {
          if (prev.requestId !== currentRequestId) {
            return prev;
          }

          return {
            ...prev,
            assignments: response.assignments,
            totalCount: response.total_count,
            loading: false,
          };
        });
      } catch (err) {
        setState((prev) => {
          if (prev.requestId !== currentRequestId) {
            return prev;
          }

          const message = err instanceof Error ? err.message : "Couldn't load assignments.";
          return { ...prev, error: message, loading: false };
        });
      }
    }

    function handleRetry() {
      fetchDashboard();
    }

    function handlePageChange(newPage: number) {
      const totalPages = Math.ceil(state.totalCount / state.pageSize) || 1;
      const validatedPage = Math.max(1, Math.min(newPage, totalPages));

      if (validatedPage !== state.page) {
        setState((prev) => ({ ...prev, page: validatedPage }));
      }
    }

    // Loading state
    if (state.loading && state.assignments.length === 0) {
      return (
        <div>
          <div className="py-3 flex items-center justify-between">
            <button
              onClick={onNewAssignment}
              className="bg-blue-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              + New Assignment
            </button>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4 space-y-3">
            <div className="h-6 bg-gray-100 rounded animate-pulse w-full"></div>
            <div className="h-6 bg-gray-100 rounded animate-pulse w-full"></div>
            <div className="h-6 bg-gray-100 rounded animate-pulse w-full"></div>
            <div className="h-6 bg-gray-100 rounded animate-pulse w-full"></div>
          </div>
        </div>
      );
    }

    // Error state
    if (state.error) {
      return (
        <div>
          <div className="py-3 flex items-center justify-between">
            <button
              onClick={onNewAssignment}
              className="bg-blue-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              + New Assignment
            </button>
          </div>
          <div className="text-center py-12 border-2 border-dashed border-red-200 rounded-lg text-red-600">
            {state.error}
            <button onClick={handleRetry} className="underline font-medium ml-1">
              Retry
            </button>
          </div>
        </div>
      );
    }

    // Empty state
    if (state.assignments.length === 0 && !state.loading) {
      return (
        <div>
          <div className="py-3 flex items-center justify-between">
            <button
              onClick={onNewAssignment}
              className="bg-blue-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              + New Assignment
            </button>
          </div>
          <div className="text-center py-12 border-2 border-dashed border-gray-200 rounded-lg text-gray-500">
            No assignments yet — click <strong>+ New Assignment</strong> to get started
          </div>
        </div>
      );
    }

    const totalPages = Math.ceil(state.totalCount / state.pageSize);

    return (
      <div>
        {/* Toolbar */}
        <div className="py-3 flex items-center justify-between">
          <button
            onClick={onNewAssignment}
            className="bg-blue-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            + New Assignment
          </button>
        </div>

        {/* Title and Summary */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-black text-gray-900">Skill Assignments</h2>
          <span className="text-sm text-gray-500">Total: {state.totalCount} assignment{state.totalCount !== 1 ? 's' : ''}</span>
        </div>

        {/* Table */}
        <table className="w-full border-collapse text-sm bg-white rounded-lg overflow-hidden shadow-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-gray-500">
              <th className="px-4 py-3 font-medium">Employee</th>
              <th className="px-4 py-3 font-medium">Assigned Skill</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Progress</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {state.assignments.map((row) => (
              <DashboardRow key={row.assignment_id} row={row} onViewDetails={handleViewDetails} />
            ))}
          </tbody>
        </table>

        <ProvenanceDrillDownModal
          assignmentId={selectedAssignmentId}
          open={selectedAssignmentId !== null}
          onClose={handleCloseDrillDown}
        />

        {/* Pagination */}
        <div className="flex items-center justify-center gap-2 mt-4 text-sm">
          <button
            onClick={() => handlePageChange(state.page - 1)}
            disabled={state.page === 1}
            className="px-3 py-1 rounded border border-gray-200 text-gray-400 disabled:cursor-not-allowed hover:border-gray-300 disabled:hover:border-gray-200"
          >
            Previous
          </button>
          <button className="px-3 py-1 rounded border border-blue-600 bg-blue-50 text-blue-700 font-medium">
            {state.page}
          </button>
          <button
            onClick={() => handlePageChange(state.page + 1)}
            disabled={state.page >= totalPages}
            className="px-3 py-1 rounded border border-gray-200 text-gray-400 disabled:cursor-not-allowed hover:border-gray-300 disabled:hover:border-gray-200"
          >
            Next
          </button>
        </div>

        <p className="text-center text-xs text-gray-400 mt-8">App v0.1.0</p>
      </div>
    );
  }
);
