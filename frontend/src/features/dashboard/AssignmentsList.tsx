import * as React from 'react';
import { Button } from '@/components/ui/button';
import { FormErrorText } from '@/components/ui/form-error-text';
import { getDashboardAssignments, type DashboardAssignmentRow } from '@/lib/api/dashboardApi';
import { cn } from '@/lib/utils';

export interface AssignmentsListHandle {
  /**
   * Immediately re-fetches the list — this is Story 3.5 AC1's own ~1s
   * "row appears" mechanism, deliberately independent of any future
   * background polling loop (Story 5.4's poll interval is 10-15s, far too
   * slow for this AC). Resolves `true` on success, `false` on failure so
   * the caller can render the refresh-error state (AC5).
   */
  refetch: () => Promise<boolean>;
}

export interface AssignmentsListProps {
  /** Row id to visually highlight (AC4) — owned by the parent so it can
   * clear the highlight on the same timer it uses for the toast. */
  highlightedId?: string | null;
}

const PAGE_SIZE = 10;

function formatStatus(status: DashboardAssignmentRow['status']): string {
  switch (status) {
    case 'NOT_STARTED':
      return 'Not Started';
    case 'IN_PROGRESS':
      return 'In Progress';
    case 'COMPLETED':
      return 'Completed';
    default:
      return status;
  }
}

function statusBadgeClass(status: DashboardAssignmentRow['status']): string {
  switch (status) {
    case 'COMPLETED':
      return 'bg-green-100 text-green-800';
    case 'IN_PROGRESS':
      return 'bg-yellow-100 text-yellow-800';
    case 'NOT_STARTED':
    default:
      return 'bg-gray-100 text-gray-700';
  }
}

/**
 * HR dashboard assignment list (Story 3.5, expanded at user request to
 * visually/functionally match the WDS prototype's dashboard — real
 * Status/Progress derivation, colored badges, a progress bar, a total
 * count, and pagination). Still not the final Epic 5 grid: no Provenance
 * drill-down (Story 5.2), no Needs-Attention staleness threshold (Story
 * 5.3), no live 10-15s auto-polling for existing rows (Story 5.4) — this
 * list only refreshes on mount and via the parent's immediate post-create
 * `refetch()`.
 */
export const AssignmentsList = React.forwardRef<AssignmentsListHandle, AssignmentsListProps>(
  function AssignmentsList({ highlightedId }, ref) {
    const [rows, setRows] = React.useState<DashboardAssignmentRow[]>([]);
    const [loading, setLoading] = React.useState(true);
    const [loadError, setLoadError] = React.useState(false);
    const [page, setPage] = React.useState(1);
    // Distinguishes the initial load (no data on screen yet — a failure
    // must render *something*, so show the inline error view) from a later
    // refetch (rows already reflect a real prior success — a failed refetch
    // must not blow that away with an error screen; the caller, e.g.
    // DashboardStub's AC5 refresh-error banner, is responsible for
    // surfacing that failure instead). Without this split, a refetch
    // failure on an otherwise-empty list would show two contradictory
    // error messages stacked on top of each other.
    const hasLoadedOnceRef = React.useRef(false);
    // Bumped on every load()/refetch() call so a superseded (slower,
    // out-of-order) response can't overwrite fresher data — mirrors
    // AssignmentModal.tsx's contentFetchTokenRef pattern, added there after
    // a real regression in Story 3.4's review. Each call still resolves
    // true/false based on its own request's outcome; only the *application*
    // of that outcome to shared state is gated by the token check.
    const loadTokenRef = React.useRef(0);
    const [retryPending, setRetryPending] = React.useState(false);

    const load = React.useCallback(async () => {
      const token = ++loadTokenRef.current;
      try {
        const result = await getDashboardAssignments();
        if (loadTokenRef.current === token) {
          setRows(result);
          setLoadError(false);
          hasLoadedOnceRef.current = true;
        }
        return true;
      } catch {
        if (loadTokenRef.current === token && !hasLoadedOnceRef.current) {
          setLoadError(true);
        }
        return false;
      }
    }, []);

    async function handleRetryClick() {
      setRetryPending(true);
      try {
        await load();
      } finally {
        setRetryPending(false);
      }
    }

    React.useEffect(() => {
      setLoading(true);
      load().finally(() => setLoading(false));
    }, [load]);

    React.useImperativeHandle(ref, () => ({ refetch: load }), [load]);

    const totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
    const clampedPage = Math.min(page, totalPages);
    const pageRows = rows.slice((clampedPage - 1) * PAGE_SIZE, clampedPage * PAGE_SIZE);

    if (loading) {
      return (
        <div className="animate-pulse rounded-lg border border-gray-200 p-4" data-testid="assignments-list-loading">
          <div className="h-4 w-1/3 rounded bg-gray-200" />
        </div>
      );
    }

    if (loadError && rows.length === 0) {
      return (
        <div className="rounded-lg border border-dashed border-red-300 p-4 text-sm">
          <FormErrorText>Couldn&apos;t load assignments.</FormErrorText>
          <div className="mt-2">
            <Button variant="outline" disabled={retryPending} onClick={handleRetryClick}>
              {retryPending ? 'Retrying…' : 'Retry'}
            </Button>
          </div>
        </div>
      );
    }

    return (
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-2xl font-black text-gray-900">Skill Assignments</h2>
          <span className="text-sm text-gray-500">
            Total: {rows.length} assignment{rows.length === 1 ? '' : 's'}
          </span>
        </div>

        {rows.length === 0 ? (
          <div className="rounded-lg border-2 border-dashed border-gray-200 py-12 text-center text-gray-500">
            No assignments yet — click <strong>+ New Assignment</strong> to get started
          </div>
        ) : (
          <>
            <table className="w-full border-collapse overflow-hidden rounded-lg bg-white text-left text-sm shadow-sm">
              <thead>
                <tr className="border-b border-gray-200 text-gray-500">
                  <th scope="col" className="px-4 py-3 font-medium">
                    Employee
                  </th>
                  <th scope="col" className="px-4 py-3 font-medium">
                    Assigned Skill
                  </th>
                  <th scope="col" className="px-4 py-3 font-medium">
                    Status
                  </th>
                  <th scope="col" className="px-4 py-3 font-medium">
                    Progress
                  </th>
                </tr>
              </thead>
              <tbody>
                {pageRows.map((row) => (
                  <tr
                    key={row.id}
                    data-testid={`assignment-row-${row.id}`}
                    className={cn(
                      'border-b border-gray-100 transition-colors duration-500',
                      row.id === highlightedId && 'bg-amber-50'
                    )}
                  >
                    <td className="px-4 py-3 text-gray-900">{row.employee_name}</td>
                    <td className="px-4 py-3 text-gray-700">{row.skill_name}</td>
                    <td className="px-4 py-3">
                      <span
                        className={cn(
                          'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
                          statusBadgeClass(row.status)
                        )}
                      >
                        {formatStatus(row.status)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div
                        role="progressbar"
                        aria-label={`${row.employee_name} progress on ${row.skill_name}`}
                        aria-valuenow={row.progress_percent}
                        aria-valuemin={0}
                        aria-valuemax={100}
                        className="h-2 w-24 overflow-hidden rounded-full bg-gray-100"
                      >
                        <div
                          className="h-full bg-talentpilot-600"
                          style={{ width: `${row.progress_percent}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {totalPages > 1 && (
              <div className="mt-4 flex items-center justify-center gap-2 text-sm">
                <button
                  type="button"
                  disabled={clampedPage === 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="rounded border border-gray-200 px-3 py-1 text-gray-600 disabled:cursor-not-allowed disabled:text-gray-400"
                >
                  Previous
                </button>
                <span className="rounded border border-talentpilot-600 bg-talentpilot-50 px-3 py-1 font-medium text-talentpilot-700">
                  {clampedPage}
                </span>
                <button
                  type="button"
                  disabled={clampedPage === totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="rounded border border-gray-200 px-3 py-1 text-gray-600 disabled:cursor-not-allowed disabled:text-gray-400"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    );
  }
);
