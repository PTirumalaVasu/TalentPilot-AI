/**
 * Tests for DashboardPage's live auto-update polling (Story 5-4).
 * Kept separate from DashboardPage.test.tsx, which has 3 pre-existing
 * unrelated failures (see deferred-work.md, Story 5-2 review) -- new
 * fake-timer setup/teardown is cleaner isolated from that file.
 *
 * Uses vi.advanceTimersByTimeAsync() + direct assertions instead of RTL's
 * waitFor() -- waitFor's own internal retry loop relies on setTimeout,
 * which vi.useFakeTimers() also fakes, so it never resolves under fake
 * timers (matches the working pattern already established in
 * src/tests/Toast.test.tsx, which avoids waitFor for the same reason).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { DashboardPage } from "./DashboardPage";
import { dashboardApi } from "../../lib/api/dashboardApi";
import type { AssignmentRow, DashboardResponse } from "../../types/dashboard";

vi.mock("../../lib/api/dashboardApi", () => ({
  dashboardApi: {
    getDashboard: vi.fn(),
    getDrillDown: vi.fn(),
  },
}));

function makeRow(overrides: Partial<AssignmentRow> = {}): AssignmentRow {
  return {
    assignment_id: "assign-1",
    employee_id: "emp-1",
    employee_name: "Casey the Continuer",
    employee_group: "Engineering",
    skill_id: "skill-1",
    skill_name: "Data Visualization",
    status: "Not Started",
    status_percentage: null,
    provenance: "Verified",
    last_updated: new Date().toISOString(),
    assignment_created_at: new Date().toISOString(),
    ...overrides,
  };
}

function makeResponse(assignments: AssignmentRow[], totalCount = assignments.length): DashboardResponse {
  return { assignments, total_count: totalCount, page: 1, page_size: 50 };
}

const getDashboard = vi.mocked(dashboardApi.getDashboard);

// The initial mount fetch is debounced by 150ms (DashboardPage.tsx's own
// setTimeout), so every test must advance past that before asserting on
// the first load.
const MOUNT_DEBOUNCE_MS = 150;
const POLL_INTERVAL_MS = 12000;

async function advance(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

describe("DashboardPage live auto-update polling", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("polls GET /api/dashboard again after the interval elapses, without re-showing the loading skeleton", async () => {
    getDashboard.mockResolvedValue(makeResponse([makeRow()]));

    render(<DashboardPage onNewAssignment={vi.fn()} />);
    await advance(MOUNT_DEBOUNCE_MS);

    expect(screen.getByText("Casey the Continuer")).toBeInTheDocument();
    expect(getDashboard).toHaveBeenCalledTimes(1);

    await advance(POLL_INTERVAL_MS);

    expect(getDashboard).toHaveBeenCalledTimes(2);
    // The grid must still be present the whole time -- no loading-skeleton flash.
    expect(screen.getByText("Casey the Continuer")).toBeInTheDocument();
    expect(screen.getByText("View Details")).toBeInTheDocument();
  });

  it("updates a row's Status in place when a poll response changes it, with no full unmount/remount", async () => {
    getDashboard.mockResolvedValueOnce(makeResponse([makeRow({ status: "Not Started", status_percentage: null })]));

    render(<DashboardPage onNewAssignment={vi.fn()} />);
    await advance(MOUNT_DEBOUNCE_MS);
    expect(screen.getByText("Not Started")).toBeInTheDocument();

    getDashboard.mockResolvedValueOnce(
      makeResponse([makeRow({ status: "In Progress", status_percentage: 45 })])
    );
    await advance(POLL_INTERVAL_MS);

    expect(screen.getByText(/In Progress \(45%\)/)).toBeInTheDocument();
    expect(screen.queryByText("Not Started")).not.toBeInTheDocument();
  });

  it("shows a newly-created assignment that appears in a later poll response", async () => {
    getDashboard.mockResolvedValueOnce(makeResponse([makeRow()]));

    render(<DashboardPage onNewAssignment={vi.fn()} />);
    await advance(MOUNT_DEBOUNCE_MS);
    expect(screen.getByText("Casey the Continuer")).toBeInTheDocument();

    getDashboard.mockResolvedValueOnce(
      makeResponse([
        makeRow(),
        makeRow({ assignment_id: "assign-2", employee_name: "Sam the Starter", employee_group: "Engineering", skill_name: "Public Speaking" }),
      ])
    );
    await advance(POLL_INTERVAL_MS);

    expect(screen.getByText("Sam the Starter")).toBeInTheDocument();
  });

  it("does not show the page-level error state when a poll fails; polling continues on the next interval (AC8)", async () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    getDashboard.mockResolvedValueOnce(makeResponse([makeRow()]));

    render(<DashboardPage onNewAssignment={vi.fn()} />);
    await advance(MOUNT_DEBOUNCE_MS);
    expect(screen.getByText("Casey the Continuer")).toBeInTheDocument();

    getDashboard.mockRejectedValueOnce(new Error("Network error"));
    await advance(POLL_INTERVAL_MS);

    // Grid stays visible; no error banner shown for a background poll failure.
    expect(screen.getByText("Casey the Continuer")).toBeInTheDocument();
    expect(screen.queryByText(/Network error/)).not.toBeInTheDocument();
    expect(warnSpy).toHaveBeenCalled();

    // Next interval: polling resumes normally.
    getDashboard.mockResolvedValueOnce(
      makeResponse([makeRow({ status: "Completed", status_percentage: 100 })])
    );
    await advance(POLL_INTERVAL_MS);

    expect(screen.getByText("Completed")).toBeInTheDocument();
    warnSpy.mockRestore();
  });

  it("stops polling while the tab is hidden and resumes once visible again (AC7)", async () => {
    getDashboard.mockResolvedValue(makeResponse([makeRow()]));

    render(<DashboardPage onNewAssignment={vi.fn()} />);
    await advance(MOUNT_DEBOUNCE_MS);
    expect(screen.getByText("Casey the Continuer")).toBeInTheDocument();
    expect(getDashboard).toHaveBeenCalledTimes(1);

    Object.defineProperty(document, "visibilityState", {
      writable: true,
      configurable: true,
      value: "hidden",
    });
    act(() => {
      document.dispatchEvent(new Event("visibilitychange"));
    });

    await advance(POLL_INTERVAL_MS * 3);
    expect(getDashboard).toHaveBeenCalledTimes(1); // no polls fired while hidden

    Object.defineProperty(document, "visibilityState", {
      writable: true,
      configurable: true,
      value: "visible",
    });
    act(() => {
      document.dispatchEvent(new Event("visibilitychange"));
    });

    await advance(POLL_INTERVAL_MS);
    expect(getDashboard).toHaveBeenCalledTimes(2); // polling resumed
  });

  it("announces a live Status change via an aria-live region, using Story 5.6's exact wording", async () => {
    getDashboard.mockResolvedValueOnce(makeResponse([makeRow({ status: "Not Started", status_percentage: null })]));

    render(<DashboardPage onNewAssignment={vi.fn()} />);
    await advance(MOUNT_DEBOUNCE_MS);
    expect(screen.getByText("Not Started")).toBeInTheDocument();

    getDashboard.mockResolvedValueOnce(
      makeResponse([makeRow({ status: "Completed", status_percentage: 100 })])
    );
    await advance(POLL_INTERVAL_MS);

    const region = document.querySelector('[aria-live="polite"]');
    expect(region).not.toBeNull();
    expect(region?.textContent).toBe("Casey the Continuer Data Visualization status updated to Completed");
  });

  it("does not re-announce anything on a poll with no actual Status/Provenance change", async () => {
    getDashboard.mockResolvedValue(makeResponse([makeRow({ status: "In Progress", status_percentage: 45 })]));

    render(<DashboardPage onNewAssignment={vi.fn()} />);
    await advance(MOUNT_DEBOUNCE_MS);
    expect(screen.getByText(/In Progress \(45%\)/)).toBeInTheDocument();

    await advance(POLL_INTERVAL_MS);

    const region = document.querySelector('[aria-live="polite"]');
    expect(region).not.toBeNull();
    expect(region?.textContent).toBe("");
  });
});
