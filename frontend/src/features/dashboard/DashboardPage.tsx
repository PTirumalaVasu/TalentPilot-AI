import { useEffect, useRef, useState, useImperativeHandle, forwardRef } from "react";
import { dashboardApi } from "../../lib/api/dashboardApi";
import { AssignmentRow } from "../../types/dashboard";
import { DashboardRow } from "./DashboardRow";
import { ProvenanceDrillDownModal } from "./ProvenanceDrillDownModal";
import { EmployeeSummaryModal } from "./EmployeeSummaryModal";
import { GroupedEmployeeView } from "./GroupedEmployeeView";
import { Toast } from "../../components/ui/toast";
import { groupAssignmentsByEmployee } from "../../lib/utils/grouping";

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

interface ExpandedEmployees {
  [employeeName: string]: boolean;
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
    const [selectedEmployeeName, setSelectedEmployeeName] = useState<string | null>(null);
    const [liveAnnouncement, setLiveAnnouncement] = useState("");
    // Story 5.5: success toast after a Mark-as-Ready confirm.
    const [toastMessage, setToastMessage] = useState<string | null>(null);
    const [expandedEmployees, setExpandedEmployees] = useState<ExpandedEmployees>({});
    const pollIntervalRef = useRef<number | null>(null);
    const isPollingRef = useRef(false);

    function handleViewDetails(assignmentId: string) {
      setSelectedAssignmentId(assignmentId);
    }

    function handleCloseDrillDown() {
      setSelectedAssignmentId(null);
    }

    function handleViewEmployeeSummary(employeeName: string) {
      setSelectedEmployeeName(employeeName);
    }

    function handleCloseEmployeeSummary() {
      setSelectedEmployeeName(null);
    }

    function handleToggleExpand(employeeName: string) {
      setExpandedEmployees((prev) => ({
        ...prev,
        [employeeName]: !prev[employeeName],
      }));
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

    return (
      <div>
        {liveRegion}
        {toastElement}
        {/* Toolbar */}
        <div className="py-3 flex items-center justify-start gap-4">
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

        {/* Grouped View - Default Display */}
        <div>
          {groupAssignmentsByEmployee(state.assignments).map((group) => (
            <GroupedEmployeeView
              key={group.employeeName}
              employeeName={group.employeeName}
              assignments={group.assignments}
              onViewDetails={handleViewDetails}
              onViewEmployeeSummary={handleViewEmployeeSummary}
              isExpanded={expandedEmployees[group.employeeName] ?? true}
              onToggleExpand={handleToggleExpand}
            />
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

        {selectedEmployeeName && (
          <EmployeeSummaryModal
            open={selectedEmployeeName !== null}
            employeeName={selectedEmployeeName}
            employeeAssignments={state.assignments.filter(
              (a) => a.employee_name === selectedEmployeeName
            )}
            onClose={handleCloseEmployeeSummary}
            onViewSkillDetails={handleViewDetails}
          />
        )}

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
