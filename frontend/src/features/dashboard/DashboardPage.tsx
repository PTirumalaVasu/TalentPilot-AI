import { useEffect, useRef, useState, useImperativeHandle, forwardRef } from "react";
import { dashboardApi } from "../../lib/api/dashboardApi";
import { AssignmentRow } from "../../types/dashboard";
import { ProvenanceDrillDownModal } from "./ProvenanceDrillDownModal";
import { Toast } from "../../components/ui/toast";

// AC1 (epics.md:1771-1774): poll every 10-15s. 12000ms picked as the
// midpoint -- config constant, not a magic number, so it's easy to adjust
// (mirrors Story 5.3's NEEDS_ATTENTION_STALENESS_DAYS / Story 2.4's
// SIMILARITY_THRESHOLD convention).
const POLL_INTERVAL_MS = 12000;

interface DashboardState {
  assignments: AssignmentRow[];
  loading: boolean;
  error: string | null;
  page: number;
  pageSize: number;
  totalCount: number;
  requestId: number;
}

// AC2/Finding 1: Status/Provenance/percentage changes matter for "did this
// row change" (Subtask 2.3) -- last_updated is deliberately excluded since it
// ticks forward on every poll once relative-time rendering exists, so
// diffing it too would announce on every no-op poll.
function diffAssignments(prev: AssignmentRow[], next: AssignmentRow[]): AssignmentRow[] {
  const prevById = new Map(prev.map((row) => [row.assignment_id, row]));
  return next.filter((row) => {
    const before = prevById.get(row.assignment_id);
    return (
      !before ||
      before.status !== row.status ||
      before.provenance !== row.provenance ||
      before.status_percentage !== row.status_percentage
    );
  });
}

// Story 5.6's own literal AC text (epics.md:1964) specifies this exact
// wording for the same aria-live announcement -- matched here so Story 5.6
// can verify/extend rather than rebuild it (see Story 5.4's Finding 3).
function describeChanges(changes: AssignmentRow[]): string {
  return changes
    .map((row) => `${row.employee_name} ${row.skill_name} status updated to ${row.status}`)
    .join(". ");
}

// Group assignments by employee name
function groupAssignmentsByEmployee(assignments: AssignmentRow[]): Map<string, AssignmentRow[]> {
  const grouped = new Map<string, AssignmentRow[]>();
  assignments.forEach((assignment) => {
    const employeeKey = assignment.employee_name;
    if (!grouped.has(employeeKey)) {
      grouped.set(employeeKey, []);
    }
    grouped.get(employeeKey)!.push(assignment);
  });
  return grouped;
}

interface DashboardPageProps {
  onNewAssignment: () => void;
}

export interface DashboardPageHandle {
  refreshGrid: () => void;
  /** Shows the shared Toast with `message` (Story 5-6, AC5 -- e.g. the
   * "Skill assigned to..." success toast fired from the real Dashboard route). */
  announceToast: (message: string) => void;
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
    const [liveAnnouncement, setLiveAnnouncement] = useState("");
    // Story 5.5: success toast after a Mark-as-Ready confirm.
    const [toastMessage, setToastMessage] = useState<string | null>(null);
    const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
    const pollIntervalRef = useRef<number | null>(null);
    const isPollingRef = useRef(false);

    function handleViewDetails(assignmentId: string) {
      setSelectedAssignmentId(assignmentId);
    }

    function handleCloseDrillDown() {
      setSelectedAssignmentId(null);
    }

    useImperativeHandle(ref, () => ({
      refreshGrid: () => fetchDashboard(),
      announceToast: (message: string) => setToastMessage(message),
    }));

    useEffect(() => {
      const timer = setTimeout(() => {
        fetchDashboard();
      }, 150);

      return () => clearTimeout(timer);
    }, [state.page, state.pageSize]);

    // Task 2/3 (AC1,2,4,5,7,8; Findings 1,3,4): silent background poll, kept
    // decoupled from fetchDashboard()'s loading/blanking behavior so a poll
    // tick never flashes the loading skeleton (Finding 1). The effect depends
    // on [state.page, state.pageSize, state.requestId] so pollDashboard's
    // closure never goes stale after a page change (see story file's
    // "Closure trap" note) -- requestId is included too so the poll's
    // requestId snapshot (below) tracks fetchDashboard's optimistic bump
    // instead of freezing at its pre-mount-fetch value forever.
    useEffect(() => {
      function startPolling() {
        if (pollIntervalRef.current !== null) {
          return;
        }
        pollIntervalRef.current = window.setInterval(pollDashboard, POLL_INTERVAL_MS) as unknown as number;
      }

      function stopPolling() {
        if (pollIntervalRef.current === null) {
          return;
        }
        window.clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }

      async function pollDashboard() {
        if (isPollingRef.current) {
          return; // Subtask 3.3: skip if a poll is already in-flight
        }
        isPollingRef.current = true;
        // Finding 1: snapshot requestId so a slow poll response can't clobber
        // a newer manual fetch (page change, retry) that started after it --
        // mirrors fetchDashboard's own requestId staleness guard.
        const requestIdAtPollStart = state.requestId;
        try {
          const response = await dashboardApi.getDashboard(state.page, state.pageSize);
          setState((prev) => {
            if (prev.requestId !== requestIdAtPollStart) {
              return prev;
            }
            const changes = diffAssignments(prev.assignments, response.assignments);
            if (changes.length > 0) {
              setLiveAnnouncement(describeChanges(changes));
            }
            return { ...prev, assignments: response.assignments, totalCount: response.total_count };
          });
        } catch (err) {
          // AC8: non-blocking -- log and let the next interval retry, never
          // touch state.error (that's reserved for the manual/initial fetch).
          console.warn("Dashboard poll failed, will retry on next interval", err);
        } finally {
          isPollingRef.current = false;
        }
      }

      function handleVisibilityChange() {
        if (document.visibilityState === "hidden") {
          stopPolling();
        } else {
          startPolling();
        }
      }

      // AC7: don't start polling if the tab is already hidden at mount time
      // (e.g. opened into a background tab) -- visibilitychange only fires on
      // a transition, so an unconditional startPolling() here would miss the
      // "already hidden" case entirely.
      if (document.visibilityState !== "hidden") {
        startPolling();
      }
      document.addEventListener("visibilitychange", handleVisibilityChange);

      return () => {
        stopPolling();
        document.removeEventListener("visibilitychange", handleVisibilityChange);
      };
    }, [state.page, state.pageSize, state.requestId]);

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

        // Keep all accordions collapsed by default on load
        setExpandedGroups(new Set());
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

    function toggleEmployee(employeeName: string) {
      setExpandedGroups((prev) => {
        const newSet = new Set(prev);
        if (newSet.has(employeeName)) {
          newSet.delete(employeeName);
        } else {
          newSet.add(employeeName);
        }
        return newSet;
      });
    }

    // Task 4 (Finding 3, NFR-A4/UX-DR24): visually-hidden aria-live region
    // announcing poll-driven row changes, matching Story 5.6's own literal
    // announcement wording so that story can verify/extend rather than
    // rebuild this. Rendered once, reused across every state branch below.
    const liveRegion = (
      <div aria-live="polite" className="sr-only">
        {liveAnnouncement}
      </div>
    );

    // Shared success-toast slot, rendered alongside liveRegion in every
    // branch below. Two callers as of Story 5.6: (1) Story 5.5's
    // Mark-as-Ready confirm, where a fetchDashboard() refresh can trigger a
    // brief loading-skeleton flash (Finding 1) right after -- the toast must
    // survive that transition, not just the final loaded branch; (2) Story
    // 5.6's assignment-created toast via announceToast() (AC5), fired from
    // Dashboard.tsx's AssignmentModal onAssigned handler.
    const toastElement = <Toast message={toastMessage} onDismiss={() => setToastMessage(null)} />;

    // Loading state
    if (state.loading && state.assignments.length === 0) {
      return (
        <div>
          {liveRegion}
          {toastElement}
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
          {liveRegion}
          {toastElement}
          <div className="py-3 flex items-center justify-between">
            <button
              onClick={onNewAssignment}
              className="bg-blue-600 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              + New Assignment
            </button>
          </div>
          <div className="text-center py-12 border-2 border-dashed border-red-200 rounded-lg text-red-600">
            <span role="alert">{state.error}</span>
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
          {liveRegion}
          {toastElement}
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
    const groupedAssignments = groupAssignmentsByEmployee(state.assignments);
    const sortedEmployees = Array.from(groupedAssignments.keys()).sort();

    return (
      <div>
        {liveRegion}
        {toastElement}
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

        {/* Accordion with grouped assignments by employee */}
        <div className="bg-white rounded-lg overflow-hidden shadow-sm">
          {sortedEmployees.map((employeeName, index) => (
            <div key={employeeName} className={`border-b border-gray-200 ${index === sortedEmployees.length - 1 ? 'border-b-0' : ''}`}>
              <button
                onClick={() => toggleEmployee(employeeName)}
                className="w-full flex items-center justify-between px-4 py-3 text-left font-medium text-gray-900 hover:bg-gray-50 transition-colors"
              >
                <span className="font-semibold">{employeeName} ({groupedAssignments.get(employeeName)?.length || 0} skills)</span>
                <span className={`text-gray-500 transition-transform ${expandedGroups.has(employeeName) ? "rotate-180" : ""}`}>
                  ▼
                </span>
              </button>
              {expandedGroups.has(employeeName) && (
                <div className="bg-gray-50 border-t border-gray-200">
                  <div className="px-4 py-3">
                    <table className="w-full border-collapse text-sm" style={{ tableLayout: 'fixed' }}>
                      <colgroup>
                        <col style={{ width: '25%' }} />
                        <col style={{ width: '20%' }} />
                        <col style={{ width: '20%' }} />
                        <col style={{ width: '20%' }} />
                        <col style={{ width: '15%' }} />
                      </colgroup>
                      <thead>
                        <tr className="border-b border-gray-300 text-left text-gray-600">
                          <th className="px-3 py-2 font-medium">Assigned Skill</th>
                          <th className="px-3 py-2 font-medium">Status</th>
                          <th className="px-3 py-2 font-medium">Progress</th>
                          <th className="px-3 py-2 font-medium">Last Updated</th>
                          <th className="px-3 py-2 font-medium">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(groupedAssignments.get(employeeName) || []).map((row) => (
                          <tr key={row.assignment_id} className="border-b border-gray-200 hover:bg-white transition-colors align-middle">
                            <td className="px-3 py-2 truncate align-middle">{row.skill_name}</td>
                            <td className="px-3 py-2 text-left align-middle">
                              {row.status === "In Progress" && row.status_percentage !== null ? (
                                <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded whitespace-nowrap text-xs inline-block">In Progress ({row.status_percentage}%)</span>
                              ) : row.status === "Completed" ? (
                                <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs inline-block">Completed</span>
                              ) : (
                                <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs inline-block">Not Started</span>
                              )}
                            </td>
                            <td className="px-3 py-2 align-middle">
                              {row.status === "In Progress" && row.status_percentage !== null ? (
                                <div className="flex items-center gap-2">
                                  <div className="w-16 h-1 bg-gray-200 rounded-full overflow-hidden">
                                    <div
                                      className="h-full bg-blue-600"
                                      style={{ width: `${row.status_percentage}%` }}
                                    ></div>
                                  </div>
                                  <span className="text-xs text-gray-500">{row.status_percentage}%</span>
                                </div>
                              ) : row.status === "Completed" ? (
                                <div className="flex items-center gap-2">
                                  <div className="w-16 h-1 bg-gray-200 rounded-full overflow-hidden">
                                    <div className="h-full bg-green-600" style={{ width: "100%" }}></div>
                                  </div>
                                  <span className="text-xs text-gray-500">100%</span>
                                </div>
                              ) : (
                                <span className="text-xs text-gray-400">-</span>
                              )}
                            </td>
                            <td className="px-3 py-2 text-xs text-gray-500 truncate align-middle">
                              {new Date(row.last_updated).toLocaleDateString()} {new Date(row.last_updated).toLocaleTimeString()}
                            </td>
                            <td className="px-3 py-2 align-middle">
                              <button
                                onClick={() => handleViewDetails(row.assignment_id)}
                                className="text-blue-600 hover:text-blue-800 text-sm font-medium whitespace-nowrap"
                                aria-label={`View details for ${row.employee_name} ${row.skill_name}`}
                              >
                                View Details
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        <ProvenanceDrillDownModal
          assignmentId={selectedAssignmentId}
          open={selectedAssignmentId !== null}
          onClose={handleCloseDrillDown}
          onOverrideChanged={(message) => {
            setToastMessage(message);
            fetchDashboard();
          }}
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
