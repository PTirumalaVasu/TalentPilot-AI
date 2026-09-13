/** Skill Assignment Dashboard landing page (Story 9.3, FR-31/FR-32 display,
 * UX-DR44). Consumes Story 9.1's `GET /api/dashboard/stats` and Story 9.2's
 * `GET /api/dashboard/segmentation` -- both already shipped; this page is
 * pure display, never re-deriving Status/Provenance/segmentation itself.
 *
 * Route: `/dashboard` (not `/hr/dashboard`, which stays the existing full
 * grid page, untouched by this story). The left-nav "Dashboard" link still
 * points at `/hr/dashboard` until Story 9.5 repoints it -- a deliberate
 * scope boundary, not a gap (see this story's Dev Notes).
 *
 * The Needs Attention legend row is intentionally display-only here (no
 * click, no popover) -- that interactive layer is Story 9.4's job. */
import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { HrAppShell } from '@/components/layout/HrAppShell';
import { dashboardApi } from '@/lib/api/dashboardApi';
import type { DashboardStatsResponse, EmployeeSegmentationResponse } from '@/types/dashboard';

function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response?: { data?: { message?: string } } }).response;
    if (response?.data?.message) return response.data.message;
  }
  return fallback;
}

interface GradientStop {
  color: string;
  count: number;
}

/** Single source of truth for every chart-fill/legend-dot color on this page
 * -- named so a future consumer (e.g. Story 9.4's popover reusing "Needs
 * Attention red") has something to import instead of re-guessing the hex. */
const CHART_COLORS = {
  completed: '#1d4ed8',
  inProgress: '#93c5fd',
  notStarted: '#e5e7eb',
  onTrack: '#16a34a',
  segmentationInProgress: '#f59e0b',
  needsAttention: '#dc2626',
} as const;

/** Renders a CSS `conic-gradient()` string proportional to each stop's share
 * of the total -- ported from the Phase-5 prototype's own `conicGradient`
 * helper (06.1-Skill-Assignment-Dashboard.html), the only place this logic
 * is needed so no shared util was introduced. */
function conicGradient(stops: GradientStop[]): string {
  const total = stops.reduce((sum, s) => sum + s.count, 0);
  if (total === 0) return 'conic-gradient(#e5e7eb 0% 100%)';
  let acc = 0;
  const parts = stops.map((s) => {
    const start = (acc / total) * 100;
    acc += s.count;
    const end = (acc / total) * 100;
    return `${s.color} ${start}% ${end}%`;
  });
  return `conic-gradient(${parts.join(', ')})`;
}

function StatCard({ label, value, testId }: { label: string; value: number; testId: string }) {
  return (
    <div
      data-testid={testId}
      className="rounded-lg border border-gray-200 bg-white px-5 py-4 dark:border-gray-700 dark:bg-gray-900"
    >
      <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
      <p className="mt-1 text-3xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
    </div>
  );
}

function LegendRow({
  testId,
  dotColor,
  text,
}: {
  testId: string;
  dotColor: string;
  text: string;
}) {
  return (
    <p data-testid={testId} className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
      <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: dotColor }} />
      <span>{text}</span>
    </p>
  );
}

export function SkillAssignmentDashboard() {
  const [stats, setStats] = useState<DashboardStatsResponse | null>(null);
  const [segmentation, setSegmentation] = useState<EmployeeSegmentationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const requestIdRef = useRef(0);

  const fetchData = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    setLoading(true);
    setError(null);
    try {
      const [statsResponse, segmentationResponse] = await Promise.all([
        dashboardApi.getDashboardStats(),
        dashboardApi.getEmployeeSegmentation(),
      ]);
      if (requestIdRef.current !== requestId) return;
      setStats(statsResponse);
      setSegmentation(segmentationResponse);
      setLoading(false);
    } catch (err) {
      if (requestIdRef.current !== requestId) return;
      setError(extractErrorMessage(err, "Couldn't load dashboard data."));
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  const isEmpty =
    stats !== null && (stats.total_employees === 0 || stats.total_skills_assigned === 0);

  return (
    <HrAppShell>
      <main className="px-6 pb-12">
        <div className="pt-6">
          <h1 data-testid="dashboard-heading-title" className="text-3xl font-black text-gray-900 dark:text-gray-100">
            Dashboard
          </h1>
          <p data-testid="dashboard-heading-subtitle" className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Org-wide skill assignment overview
          </p>
        </div>

        {loading && (
          <div data-testid="dashboard-state-loading" className="mt-6 animate-pulse">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="h-20 rounded-lg bg-gray-200 dark:bg-gray-800" />
              <div className="h-20 rounded-lg bg-gray-200 dark:bg-gray-800" />
              <div className="h-20 rounded-lg bg-gray-200 dark:bg-gray-800" />
            </div>
            <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-[1fr_1.5fr]">
              <div className="h-72 rounded-lg bg-gray-200 dark:bg-gray-800" />
              <div className="h-72 rounded-lg bg-gray-200 dark:bg-gray-800" />
            </div>
          </div>
        )}

        {!loading && error && (
          <div
            data-testid="dashboard-state-error"
            className="mt-6 rounded-lg border border-gray-200 bg-white p-12 text-center dark:border-gray-700 dark:bg-gray-900"
          >
            <p role="alert" className="text-gray-600 dark:text-gray-400">
              {error}
            </p>
            <button
              type="button"
              onClick={() => void fetchData()}
              className="mt-4 inline-block rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && stats && segmentation && (
          <>
            {/* Top-line stats row (secondary) -- shown in both the Loaded and
                Empty states per the UX spec's Page States table ("Stats show
                zeros"): only the ring/pie region below is swapped out when
                there is genuinely nothing to show. */}
            <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
              <StatCard testId="dashboard-stat-employees" label="Total Employees" value={stats.total_employees} />
              <StatCard
                testId="dashboard-stat-skills-assigned"
                label="Total Skills Assigned"
                value={stats.total_skills_assigned}
              />
              <StatCard testId="dashboard-stat-completed" label="Total Completed" value={stats.total_completed} />
            </div>

            {isEmpty ? (
              <div
                data-testid="dashboard-state-empty"
                className="mt-4 rounded-lg border border-gray-200 bg-white p-12 text-center dark:border-gray-700 dark:bg-gray-900"
              >
                <p className="text-gray-600 dark:text-gray-400">
                  Nothing to show yet — assign a Skill to get started.
                </p>
                <Link
                  to="/hr/dashboard"
                  className="mt-4 inline-block rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600"
                >
                  + New Assignment
                </Link>
              </div>
            ) : (
            <div data-testid="dashboard-state-loaded" className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-[1fr_1.5fr]">
              {/* Assignment Progress Ring -- secondary: smaller card, smaller heading */}
              <div
                data-testid="dashboard-progress-card"
                className="flex flex-col items-center rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900"
              >
                <h2
                  data-testid="dashboard-progress-heading"
                  className="mb-4 self-start text-xl font-bold text-gray-900 dark:text-gray-100"
                >
                  Assignment Progress
                </h2>
                <div
                  data-testid="dashboard-progress-ring"
                  className="relative h-40 w-40 rounded-full"
                  style={{
                    background: conicGradient([
                      { color: CHART_COLORS.completed, count: stats.completed_count },
                      { color: CHART_COLORS.inProgress, count: stats.in_progress_count },
                      { color: CHART_COLORS.notStarted, count: stats.not_started_count },
                    ]),
                  }}
                >
                  <div className="absolute inset-3 flex items-center justify-center rounded-full bg-white dark:bg-gray-900">
                    <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                      {stats.overall_percent}%
                    </span>
                  </div>
                </div>
                <div className="mt-5 w-full space-y-1.5">
                  <LegendRow
                    testId="dashboard-progress-legend-completed"
                    dotColor={CHART_COLORS.completed}
                    text={`Completed — ${stats.completed_count}`}
                  />
                  <LegendRow
                    testId="dashboard-progress-legend-inprogress"
                    dotColor={CHART_COLORS.inProgress}
                    text={`In Progress — ${stats.in_progress_count}`}
                  />
                  <LegendRow
                    testId="dashboard-progress-legend-notstarted"
                    dotColor={CHART_COLORS.notStarted}
                    text={`Not Started — ${stats.not_started_count}`}
                  />
                </div>
              </div>

              {/* Employee Segmentation -- PRIMARY: larger card, larger heading (UX-DR44) */}
              <div
                data-testid="dashboard-segmentation-card"
                className="rounded-lg border-2 border-gray-200 bg-white p-6 dark:border-gray-600 dark:bg-gray-900"
              >
                <h2
                  data-testid="dashboard-segmentation-heading"
                  className="mb-4 text-2xl font-bold text-gray-900 dark:text-gray-100"
                >
                  Employee Segmentation
                </h2>
                <div className="flex flex-col items-center gap-8 sm:flex-row">
                  <div
                    data-testid="dashboard-segmentation-pie"
                    className="h-52 w-52 shrink-0 rounded-full"
                    style={{
                      background: conicGradient([
                        { color: CHART_COLORS.onTrack, count: segmentation.on_track_count },
                        { color: CHART_COLORS.segmentationInProgress, count: segmentation.in_progress_count },
                        { color: CHART_COLORS.needsAttention, count: segmentation.needs_attention_count },
                      ]),
                    }}
                  />
                  <div className="w-full space-y-3">
                    <LegendRow
                      testId="dashboard-segmentation-legend-ontrack"
                      dotColor={CHART_COLORS.onTrack}
                      text={`On Track — ${segmentation.on_track_count}`}
                    />
                    <LegendRow
                      testId="dashboard-segmentation-legend-inprogress"
                      dotColor={CHART_COLORS.segmentationInProgress}
                      text={`In Progress — ${segmentation.in_progress_count}`}
                    />
                    {/* Display-only in this story (Story 9.4 adds the click/popover
                        interaction) -- always a plain legend row, never a button. */}
                    <LegendRow
                      testId="dashboard-segmentation-legend-needsattention"
                      dotColor={CHART_COLORS.needsAttention}
                      text={`Needs Attention — ${segmentation.needs_attention_count}`}
                    />
                  </div>
                </div>
              </div>
            </div>
            )}
          </>
        )}

        <p data-testid="dashboard-version-info" className="mt-8 text-center text-xs text-gray-400 dark:text-gray-500">
          App v0.1.0
        </p>
      </main>
    </HrAppShell>
  );
}
