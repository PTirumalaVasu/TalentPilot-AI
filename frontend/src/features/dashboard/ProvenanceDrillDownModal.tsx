import { useEffect, useState, useCallback, useId, useRef } from "react";
import { formatDistanceToNow, differenceInCalendarDays } from "date-fns";
import { Dialog } from "@/components/ui/dialog";
import { StatusBadge } from "@/components/StatusBadge";
import { dashboardApi } from "@/lib/api/dashboardApi";
import type { DrillDownResponse, StatusType } from "@/types/dashboard";

interface ProvenanceDrillDownModalProps {
  assignmentId: string | null;
  open: boolean;
  onClose: () => void;
}

const STATUS_DISPLAY: Record<DrillDownResponse["status"], StatusType> = {
  NOT_STARTED: "Not Started",
  IN_PROGRESS: "In Progress",
  COMPLETED: "Completed",
};

function relativeTime(iso: string): string {
  return formatDistanceToNow(new Date(iso), { addSuffix: true });
}

/**
 * Provenance Drill-Down modal (Story 5-2, AC2-AC5). Built on the existing
 * `Dialog` primitive (Story 3.4) — Escape/backdrop-click/focus-trap already
 * handled there, not reimplemented here.
 */
export function ProvenanceDrillDownModal({ assignmentId, open, onClose }: ProvenanceDrillDownModalProps) {
  const titleId = useId();
  const [data, setData] = useState<DrillDownResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Guards against a slower, earlier fetch overwriting a newer one if the
  // user clicks [View Details] on a second row before the first response
  // resolves -- mirrors DashboardPage's own requestId / AssignmentModal's
  // tokenRef pattern already established elsewhere in this codebase (code
  // review finding, Story 5-2).
  const requestIdRef = useRef(0);

  const fetchDetail = useCallback(() => {
    if (!assignmentId) return;
    const requestId = ++requestIdRef.current;
    setLoading(true);
    setError(null);
    setData(null);
    dashboardApi
      .getDrillDown(assignmentId)
      .then((response) => {
        if (requestIdRef.current !== requestId) return;
        setData(response);
      })
      .catch((err) => {
        if (requestIdRef.current !== requestId) return;
        const message = err instanceof Error ? err.message : "Couldn't load details.";
        setError(message);
      })
      .finally(() => {
        if (requestIdRef.current !== requestId) return;
        setLoading(false);
      });
  }, [assignmentId]);

  useEffect(() => {
    if (open && assignmentId) {
      fetchDetail();
    }
  }, [open, assignmentId, fetchDetail]);

  if (!open) return null;

  // A stable heading carrying `titleId` renders in every branch (loading,
  // error, loaded) so Dialog's `aria-labelledby` always resolves to a real
  // element -- previously only the loaded branch rendered it, leaving the
  // dialog with no accessible name while loading or on fetch failure
  // (code review finding, Story 5-2).
  return (
    <Dialog open={open} onClose={onClose} titleId={titleId}>
      {loading && (
        <div className="space-y-3" data-testid="drill-down-loading">
          <h2 id={titleId} className="sr-only">
            Loading assignment details
          </h2>
          <div className="h-6 bg-gray-100 rounded animate-pulse w-2/3" />
          <div className="h-4 bg-gray-100 rounded animate-pulse w-full" />
          <div className="h-4 bg-gray-100 rounded animate-pulse w-full" />
          <p className="text-sm text-gray-500">Loading details...</p>
        </div>
      )}

      {!loading && error && (
        <div className="space-y-3">
          <h2 id={titleId} className="text-lg font-bold text-gray-900">
            Couldn't load details
          </h2>
          <p className="text-red-600 text-sm">{error}</p>
          <button
            onClick={fetchDetail}
            className="text-blue-600 hover:underline text-sm font-medium"
          >
            Retry
          </button>
        </div>
      )}

      {!loading && !error && data && (
        <div className="space-y-4">
          <header>
            <h2 id={titleId} className="text-lg font-bold text-gray-900">
              {data.employee_name} — {data.skill_name}
            </h2>
            <div className="mt-2">
              <StatusBadge status={STATUS_DISPLAY[data.status]} percentage={data.status_percentage} />
            </div>
          </header>

          <ProvenanceSection data={data} />

          <div className="flex items-center justify-between pt-2 border-t border-gray-100">
            <div className="flex gap-2">
              <button
                disabled
                aria-label="Available once HR Override is built — Story 5.5"
                title="Available once HR Override is built — Story 5.5"
                className="text-sm font-medium text-gray-400 cursor-not-allowed"
              >
                Mark as Ready
              </button>
              <button
                disabled
                aria-label="Available once HR Override reversal is built — Story 5.5b"
                title="Available once HR Override reversal is built — Story 5.5b"
                className="text-sm font-medium text-gray-400 cursor-not-allowed"
              >
                Reverse Override
              </button>
            </div>
            <button
              onClick={onClose}
              className="bg-gray-100 text-gray-700 text-sm font-semibold px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </Dialog>
  );
}

function ProvenanceSection({ data }: { data: DrillDownResponse }) {
  switch (data.provenance) {
    case "Verified":
      return (
        <section aria-label="Provenance detail" className="space-y-1 text-sm text-gray-700">
          <p className="font-medium text-gray-900">✓ Verified via video playback</p>
          <p>Watch Progress: {data.status_percentage ?? 0}%</p>
          <p>Last Updated: {relativeTime(data.last_updated)}</p>
        </section>
      );
    case "Self-reported":
      return (
        <section aria-label="Provenance detail" className="space-y-1 text-sm text-gray-700">
          <p className="font-medium text-gray-900">📝 Self-reported</p>
          <p>Status: {STATUS_DISPLAY[data.status]}</p>
          <p>Last Updated: {relativeTime(data.last_updated)}</p>
          <p>
            Self-reported by {data.employee_name} on {new Date(data.last_updated).toLocaleDateString()}
          </p>
        </section>
      );
    case "Needs Attention": {
      const staleDays = differenceInCalendarDays(new Date(), new Date(data.last_updated));
      return (
        <section aria-label="Provenance detail" className="space-y-1 text-sm text-gray-700">
          <p className="font-medium text-amber-700">⚠️ Needs Attention</p>
          <p>Status: {STATUS_DISPLAY[data.status]}</p>
          <p>Last Updated: {relativeTime(data.last_updated)}</p>
          <p>
            This status hasn't been updated in {staleDays} day{staleDays === 1 ? "" : "s"}. Consider reaching out to{" "}
            {data.employee_name} to confirm.
          </p>
          <p>
            Self-reported by {data.employee_name} on {new Date(data.last_updated).toLocaleDateString()}
          </p>
        </section>
      );
    }
    case "HR Override":
      return (
        <section aria-label="Provenance detail" className="space-y-1 text-sm text-gray-700">
          <p className="font-medium text-gray-900">🔒 HR Override</p>
          <p>Override Status: {STATUS_DISPLAY[data.status]}</p>
          <p>Overridden by: {data.override_set_by_name ?? "Unknown"}</p>
          <p>
            Overridden at:{" "}
            {data.override_set_at ? relativeTime(data.override_set_at) : "Unknown"}
          </p>
          <p>Reason: {data.override_reason || "No reason provided"}</p>
          <UnderlyingSignal data={data} />
        </section>
      );
    case "Not Started":
    default:
      return (
        <section aria-label="Provenance detail" className="space-y-1 text-sm text-gray-700">
          <p className="font-medium text-gray-900">No signal yet</p>
          <p>This assignment hasn't started — nothing has been watched or reported.</p>
        </section>
      );
  }
}

function UnderlyingSignal({ data }: { data: DrillDownResponse }) {
  if (!data.underlying_provenance) return null;

  const underlyingStatusLabel = data.underlying_status ? STATUS_DISPLAY[data.underlying_status] : "Not Started";

  // Explicit per-branch mapping (not a Verified/else split) -- collapsing
  // Not Started or Needs Attention into "Self-reported" would falsely assert
  // a self-report that may never have happened, or silently drop the
  // Needs-Attention staleness signal AR-4 exists to preserve.
  let label: string;
  switch (data.underlying_provenance) {
    case "Verified":
      label = `Original signal: Watch Progress ${data.underlying_status_percentage ?? 0}% (Verified)`;
      break;
    case "Self-reported":
      label = `Original signal: Self-reported · ${underlyingStatusLabel}`;
      break;
    case "Needs Attention":
      label = `Original signal: Self-reported (Needs Attention) · ${underlyingStatusLabel}`;
      break;
    case "Not Started":
    default:
      label = "Original signal: No signal yet — nothing had been watched or reported";
      break;
  }

  return (
    <p className="mt-2 pt-2 border-t border-gray-100 text-gray-600" aria-label="Underlying signal">
      {label}
    </p>
  );
}
