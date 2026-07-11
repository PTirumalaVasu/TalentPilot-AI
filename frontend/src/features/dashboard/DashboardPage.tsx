/**
 * HR Admin's Assignment Dashboard Page (Story 5-1).
 */
import { useEffect, useState } from "react";
import { dashboardApi } from "../../lib/api/dashboardApi";
import { DashboardResponse, AssignmentRow } from "../../types/dashboard";
import { DashboardRow } from "./DashboardRow";
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

export function DashboardPage() {
  const [state, setState] = useState<DashboardState>({
    assignments: [],
    loading: true,
    error: null,
    page: 1,
    pageSize: 50,
    totalCount: 0,
    requestId: 0,
  });

  // Fetch dashboard data when page changes (with debounce/cancellation)
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

        const message = err instanceof Error ? err.message : "Failed to load dashboard";
        return { ...prev, error: message, loading: false };
      });
    }
  }

  function handleViewDetails(assignmentId: string) {
    // Story 5.2 will handle drill-down modal
    console.log("View details for assignment:", assignmentId);
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

  // AC7: Loading state
  if (state.loading && state.assignments.length === 0) {
    return (
      <div className="container mx-auto p-4">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <p className="mt-2 text-gray-600">Loading assignments...</p>
        </div>
      </div>
    );
  }

  // AC8: Error state
  if (state.error) {
    return (
      <div className="container mx-auto p-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{state.error}</p>
          <Button onClick={handleRetry} className="mt-2" variant="outline">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  // AC6: Empty state
  if (state.assignments.length === 0 && !state.loading) {
    return (
      <div className="container mx-auto p-4">
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold mb-2">No assignments yet</h2>
          <p className="text-gray-600 mb-4">
            Create your first skill assignment to get started
          </p>
          <Button>+ New Assignment</Button>
        </div>
      </div>
    );
  }

  // AC5: Calculate total pages
  const totalPages = Math.ceil(state.totalCount / state.pageSize);

  return (
    <div className="container mx-auto p-4">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold">Assignment Dashboard</h1>
        <Button>+ New Assignment</Button>
      </div>

      <div className="bg-white rounded-lg border overflow-x-auto">
        <table className="w-full" role="table">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900" aria-label="Employee Name column">
                Employee Name
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900" aria-label="Skill Name column">
                Skill Name
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900" aria-label="Status column">
                Status
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900" aria-label="Last Updated column">
                Last Updated
              </th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900" aria-label="Actions column">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {state.assignments.map((row) => (
              <DashboardRow
                key={row.assignment_id}
                row={row}
                onViewDetails={handleViewDetails}
              />
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-6 flex justify-between items-center">
        <div className="text-sm text-gray-600">
          Page {state.page} of {totalPages} (Total: {state.totalCount} assignments)
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => handlePageChange(state.page - 1)}
            disabled={state.page === 1}
            variant="outline"
          >
            Previous
          </Button>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min="1"
              max={totalPages}
              value={state.page}
              onChange={(e) => handlePageChange(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-12 px-2 py-1 border rounded text-center"
              aria-label={`Go to page, current page ${state.page} of ${totalPages}`}
            />
            <span className="text-sm text-gray-600">of {totalPages}</span>
          </div>
          <Button
            onClick={() => handlePageChange(state.page + 1)}
            disabled={state.page >= totalPages}
            variant="outline"
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
