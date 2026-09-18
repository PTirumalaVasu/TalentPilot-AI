/**
 * Tests for DashboardPage component (Story 5-1).
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { createRef } from "react";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import { DashboardPage, type DashboardPageHandle } from "./DashboardPage";
import * as dashboardApi from "../../lib/api/dashboardApi";
import type { DashboardResponse } from "../../types/dashboard";

// Mock the dashboardApi module
vi.mock("../../lib/api/dashboardApi", () => ({
  dashboardApi: {
    getDashboard: vi.fn(),
    getDrillDown: vi.fn(),
    setOverride: vi.fn(),
    deleteAssignment: vi.fn(),
  },
}));

// Groups render collapsed by default (fetchDashboard resets expandedGroups on
// every load) -- row-level content (skill name, status, progress, last
// updated, View Details) only enters the DOM once its employee group is
// expanded, so most assertions below must open the group first.
async function expandGroup(employeeName: RegExp | string) {
  const toggle = await screen.findByRole("button", { name: employeeName });
  fireEvent.click(toggle);
}

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state on mount", () => {
    // Mock API to delay response
    vi.mocked(dashboardApi.dashboardApi.getDashboard).mockImplementation(
      () => new Promise<DashboardResponse>(() => {}) // Never resolves
    );

    render(<DashboardPage onNewAssignment={() => {}} />);
    expect(screen.getByTestId("dashboard-loading")).toBeInTheDocument();
  });

  it("renders assignment grid when data loads", async () => {
    const mockData = {
      assignments: [
        {
          assignment_id: "id-1",
          employee_id: "emp-1",
          employee_name: "Casey the Continuer",
          employee_group: "Engineering",
          skill_id: "skill-1",
          skill_name: "Data Visualization",
          status: "In Progress" as const,
          status_percentage: 45,
          provenance: "Verified" as const,
          last_updated: new Date().toISOString(),
          assignment_created_at: new Date().toISOString(),
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 50,
    };

    vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue(mockData);

    render(<DashboardPage onNewAssignment={() => {}} />);

    await expandGroup(/Casey the Continuer/);

    await waitFor(() => {
      expect(screen.getByText("Data Visualization")).toBeInTheDocument();
    });
  });

  it("displays Status badge with text (never color-only)", async () => {
    const mockData = {
      assignments: [
        {
          assignment_id: "id-1",
          employee_id: "emp-1",
          employee_name: "Test Employee",
          employee_group: "Engineering",
          skill_id: "skill-1",
          skill_name: "Test Skill",
          status: "In Progress" as const,
          status_percentage: 45,
          provenance: "Verified" as const,
          last_updated: new Date().toISOString(),
          assignment_created_at: new Date().toISOString(),
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 50,
    };

    vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue(mockData);

    render(<DashboardPage onNewAssignment={() => {}} />);

    await expandGroup(/Test Employee/);

    await waitFor(() => {
      // Status text should be present (not just color)
      expect(screen.getByText(/In Progress \(45%\)/)).toBeInTheDocument();
    });
  });

  it("displays relative timestamp (not ISO-8601)", async () => {
    const now = new Date();
    const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000);

    const mockData = {
      assignments: [
        {
          assignment_id: "id-1",
          employee_id: "emp-1",
          employee_name: "Test Employee",
          employee_group: "Engineering",
          skill_id: "skill-1",
          skill_name: "Test Skill",
          status: "Not Started" as const,
          status_percentage: null,
          provenance: "Verified" as const,
          last_updated: twoHoursAgo.toISOString(),
          assignment_created_at: twoHoursAgo.toISOString(),
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 50,
    };

    vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue(mockData);

    render(<DashboardPage onNewAssignment={() => {}} />);

    await expandGroup(/Test Employee/);

    await waitFor(() => {
      // Should show relative time like "2 hours ago", not ISO-8601
      const text = screen.getByText(/ago$/);
      expect(text.textContent).toMatch(/\d+ (hour|minute|day)s? ago/);
    });
  });

  it("View Details button is always visible on every row", async () => {
    const mockData = {
      assignments: [
        {
          assignment_id: "id-1",
          employee_id: "emp-1",
          employee_name: "Test Employee",
          employee_group: "Engineering",
          skill_id: "skill-1",
          skill_name: "Test Skill",
          status: "Not Started" as const,
          status_percentage: null,
          provenance: "Verified" as const,
          last_updated: new Date().toISOString(),
          assignment_created_at: new Date().toISOString(),
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 50,
    };

    vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue(mockData);

    render(<DashboardPage onNewAssignment={() => {}} />);

    await expandGroup(/Test Employee/);

    await waitFor(() => {
      const buttons = screen.getAllByRole("button", { name: /View details/i });
      expect(buttons.length).toBeGreaterThan(0);
      // Button should not be disabled
      buttons.forEach((btn) => {
        expect(btn).not.toHaveAttribute("disabled");
      });
    });
  });

  it("shows error state when fetch fails", async () => {
    vi.mocked(dashboardApi.dashboardApi.getDashboard).mockRejectedValue(
      new Error("Network error")
    );

    render(<DashboardPage onNewAssignment={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });
  });

  it("announces fetch errors immediately via role=alert (Story 5-6, AC6)", async () => {
    vi.mocked(dashboardApi.dashboardApi.getDashboard).mockRejectedValue(
      new Error("Network error")
    );

    render(<DashboardPage onNewAssignment={() => {}} />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Network error");
    });
  });

  it("Retry button retries fetch on error", async () => {
    vi.mocked(dashboardApi.dashboardApi.getDashboard)
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce({
        assignments: [],
        total_count: 0,
        page: 1,
        page_size: 50,
      });

    render(<DashboardPage onNewAssignment={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });

    const retryButton = screen.getByRole("button", { name: /Retry/i });
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(screen.queryByText(/Network error/)).not.toBeInTheDocument();
    });
  });

  it("shows empty state when no assignments", async () => {
    vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue({
      assignments: [],
      total_count: 0,
      page: 1,
      page_size: 50,
    });

    render(<DashboardPage onNewAssignment={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText(/No assignments yet/)).toBeInTheDocument();
    });
  });

  it("pagination shows correct page numbers and total", async () => {
    const mockData = {
      assignments: Array.from({ length: 50 }, (_, i) => ({
        assignment_id: `id-${i}`,
        employee_id: `emp-${i}`,
        employee_name: `Employee ${i}`,
        employee_group: "Engineering",
        skill_id: `skill-${i}`,
        skill_name: `Skill ${i}`,
        status: "Not Started" as const,
        status_percentage: null,
        provenance: "Verified" as const,
        last_updated: new Date().toISOString(),
        assignment_created_at: new Date().toISOString(),
      })),
      total_count: 125,
      page: 1,
      page_size: 50,
    };

    vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue(mockData);

    render(<DashboardPage onNewAssignment={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText(/Total: 125 assignments/)).toBeInTheDocument();
    });

    // 125 total / 50 per page = 3 pages. Current page button reads "1",
    // Previous is disabled (already on page 1) and Next is enabled (more
    // pages remain) -- there's no separate "Page X of Y" string in this
    // design, the button states themselves communicate paging.
    const pageButton = screen.getByRole("button", { name: "1" });
    expect(pageButton).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Next" })).toBeEnabled();
  });

  it("keyboard navigation works - View Details button is focusable", async () => {
    const mockData = {
      assignments: [
        {
          assignment_id: "id-1",
          employee_id: "emp-1",
          employee_name: "Test Employee",
          employee_group: "Engineering",
          skill_id: "skill-1",
          skill_name: "Test Skill",
          status: "Not Started" as const,
          status_percentage: null,
          provenance: "Verified" as const,
          last_updated: new Date().toISOString(),
          assignment_created_at: new Date().toISOString(),
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 50,
    };

    vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValueOnce(mockData);

    render(<DashboardPage onNewAssignment={() => {}} />);

    await expandGroup(/Test Employee/);

    // Check that View Details button exists and is focusable
    const viewDetailsButtons = await screen.findAllByRole("button", { name: /View Details/i });
    expect(viewDetailsButtons.length).toBeGreaterThan(0);
    viewDetailsButtons.forEach((btn) => {
      expect(btn).not.toHaveAttribute("disabled");
    });
  });

  it("Story 5.5: a successful Mark-as-Ready confirm shows a success toast and re-fetches the dashboard", async () => {
    const mockData = {
      assignments: [
        {
          assignment_id: "id-1",
          employee_id: "emp-1",
          employee_name: "Casey the Continuer",
          employee_group: "Engineering",
          skill_id: "skill-1",
          skill_name: "Data Visualization",
          status: "Not Started" as const,
          status_percentage: null,
          provenance: "Not Started" as const,
          last_updated: new Date().toISOString(),
          assignment_created_at: new Date().toISOString(),
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 50,
    };

    vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue(mockData);
    vi.mocked(dashboardApi.dashboardApi.getDrillDown).mockResolvedValue({
      assignment_id: "id-1",
      employee_name: "Casey the Continuer",
      skill_name: "Data Visualization",
      status: "NOT_STARTED",
      status_percentage: null,
      provenance: "Not Started",
      last_updated: new Date().toISOString(),
      override_set_by_name: null,
      override_reason: null,
      override_set_at: null,
      underlying_provenance: null,
      underlying_status: null,
      underlying_status_percentage: null,
    });
    vi.mocked(dashboardApi.dashboardApi.setOverride).mockResolvedValue({
      assignment_id: "id-1",
      employee_name: "Casey the Continuer",
      skill_name: "Data Visualization",
      status: "COMPLETED",
      status_percentage: null,
      provenance: "HR Override",
      last_updated: new Date().toISOString(),
      override_set_by_name: "Rita the Recommender",
      override_reason: null,
      override_set_at: new Date().toISOString(),
      underlying_provenance: "Not Started",
      underlying_status: "NOT_STARTED",
      underlying_status_percentage: null,
    });

    render(<DashboardPage onNewAssignment={() => {}} />);

    await expandGroup(/Casey the Continuer/);
    expect(dashboardApi.dashboardApi.getDashboard).toHaveBeenCalledTimes(1);

    fireEvent.click(await screen.findByRole("button", { name: /View Details/i }));

    await waitFor(() => screen.getByRole("button", { name: "Mark as Ready" }));
    fireEvent.click(screen.getByRole("button", { name: "Mark as Ready" }));

    await waitFor(() => screen.getByRole("button", { name: "Confirm" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));

    await waitFor(() => {
      expect(
        screen.getByText("Casey the Continuer marked as Ready for Data Visualization.")
      ).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(dashboardApi.dashboardApi.getDashboard).toHaveBeenCalledTimes(2);
    });
  });

  it("Story 5-6, AC5: announceToast() on the ref handle shows the Toast with the given message", async () => {
    vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue({
      assignments: [],
      total_count: 0,
      page: 1,
      page_size: 50,
    });

    const ref = createRef<DashboardPageHandle>();
    render(<DashboardPage ref={ref} onNewAssignment={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText(/No assignments yet/)).toBeInTheDocument();
    });

    act(() => {
      ref.current?.announceToast("✓ Skill assigned to Casey — Data Visualization");
    });

    await waitFor(() => {
      expect(
        screen.getByText("✓ Skill assigned to Casey — Data Visualization")
      ).toBeInTheDocument();
    });
    expect(screen.getByRole("status")).toHaveTextContent(
      "✓ Skill assigned to Casey — Data Visualization"
    );
  });

  describe("Story 9.4: initialAssignmentId deep-link", () => {
    function mockDrillDown() {
      return {
        assignment_id: "deep-link-id",
        employee_name: "Jamie Flagged",
        skill_name: "Data Visualization",
        status: "NOT_STARTED" as const,
        status_percentage: null,
        provenance: "Needs Attention" as const,
        last_updated: new Date().toISOString(),
        override_set_by_name: null,
        override_reason: null,
        override_set_at: null,
        underlying_provenance: null,
        underlying_status: null,
        underlying_status_percentage: null,
      };
    }

    it("opens the Provenance Drill-Down modal on mount when initialAssignmentId is set, without a grid row click", async () => {
      vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue({
        assignments: [],
        total_count: 0,
        page: 1,
        page_size: 50,
      });
      vi.mocked(dashboardApi.dashboardApi.getDrillDown).mockResolvedValue(mockDrillDown());

      render(<DashboardPage onNewAssignment={() => {}} initialAssignmentId="deep-link-id" />);

      expect(await screen.findByRole("dialog")).toBeInTheDocument();
      expect(dashboardApi.dashboardApi.getDrillDown).toHaveBeenCalledWith("deep-link-id");
    });

    it("calls onInitialAssignmentConsumed when the deep-linked modal is closed via Escape", async () => {
      vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue({
        assignments: [],
        total_count: 0,
        page: 1,
        page_size: 50,
      });
      vi.mocked(dashboardApi.dashboardApi.getDrillDown).mockResolvedValue(mockDrillDown());
      const onInitialAssignmentConsumed = vi.fn();

      render(
        <DashboardPage
          onNewAssignment={() => {}}
          initialAssignmentId="deep-link-id"
          onInitialAssignmentConsumed={onInitialAssignmentConsumed}
        />
      );

      await screen.findByRole("dialog");
      fireEvent.keyDown(document, { key: "Escape" });

      await waitFor(() => {
        expect(onInitialAssignmentConsumed).toHaveBeenCalledTimes(1);
      });
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    it("preserves the deep-linked modal's fetched state across the Loading -> Loaded transition (no remount/double-fetch)", async () => {
      // Regression test for a real bug caught in code review: `drillDownModal`
      // was rendered at a different child index in the Loaded branch than in
      // Loading/Error/Empty, so React's positional reconciliation unmounted
      // and remounted ProvenanceDrillDownModal on the Loading -> Loaded
      // transition -- discarding its already-fetched drill-down data and
      // re-firing getDrillDown. Fixed by rendering `drillDownModal` at the
      // same position (right after toastElement) in every branch.
      let resolveDashboard!: (value: DashboardResponse) => void;
      vi.mocked(dashboardApi.dashboardApi.getDashboard).mockReturnValue(
        new Promise((resolve) => {
          resolveDashboard = resolve;
        })
      );
      vi.mocked(dashboardApi.dashboardApi.getDrillDown).mockResolvedValue(mockDrillDown());

      render(<DashboardPage onNewAssignment={() => {}} initialAssignmentId="deep-link-id" />);

      // Modal opens immediately during Loading, before the grid's own fetch resolves.
      expect(await screen.findByRole("dialog")).toBeInTheDocument();
      await waitFor(() => {
        expect(dashboardApi.dashboardApi.getDrillDown).toHaveBeenCalledTimes(1);
      });

      // Resolve the grid's fetch with real, non-empty rows -- this drives the
      // Loading -> Loaded transition the position-parity bug broke.
      act(() => {
        resolveDashboard({
          assignments: [
            {
              assignment_id: "row-1",
              employee_id: "emp-1",
              employee_name: "Casey the Continuer",
              employee_group: null,
              skill_id: "skill-1",
              skill_name: "Data Visualization",
              status: "Not Started",
              status_percentage: null,
              provenance: "Not Started",
              last_updated: new Date().toISOString(),
              assignment_created_at: new Date().toISOString(),
            },
          ],
          total_count: 1,
          page: 1,
          page_size: 50,
        });
      });

      await screen.findByText(/Total: 1 assignment/);

      // Dialog instance survives the transition; getDrillDown was not re-invoked.
      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(dashboardApi.dashboardApi.getDrillDown).toHaveBeenCalledTimes(1);
    });
  });

  describe("Story 5.7: delete assignment", () => {
    function mockRow(overrides: {
      status?: "Not Started" | "In Progress" | "Completed";
      status_percentage?: number | null;
    } = {}) {
      return {
        assignment_id: "id-1",
        employee_id: "emp-1",
        employee_name: "Casey the Continuer",
        employee_group: "Engineering",
        skill_id: "skill-1",
        skill_name: "Data Visualization",
        status: overrides.status ?? ("Not Started" as const),
        status_percentage: overrides.status_percentage ?? null,
        provenance: "Not Started" as const,
        last_updated: new Date().toISOString(),
        assignment_created_at: new Date().toISOString(),
      };
    }

    async function renderAndExpandGroup(row: ReturnType<typeof mockRow>) {
      vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue({
        assignments: [row],
        total_count: 1,
        page: 1,
        page_size: 50,
      });

      render(<DashboardPage onNewAssignment={() => {}} />);

      // Regex, not exact match -- the accordion header's full text content
      // is "Casey the Continuer (1 skills)", not just the bare name.
      await waitFor(() => screen.getByRole("button", { name: /Casey the Continuer/ }));
      fireEvent.click(screen.getByRole("button", { name: /Casey the Continuer/ }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /Remove assignment/i })).toBeInTheDocument();
      });
    }

    it("delete icon renders on every row", async () => {
      await renderAndExpandGroup(mockRow());
      expect(
        screen.getByRole("button", { name: "Remove assignment for Casey the Continuer Data Visualization" })
      ).toBeInTheDocument();
    });

    it("clicking the delete icon opens the confirmation modal", async () => {
      await renderAndExpandGroup(mockRow());

      fireEvent.click(screen.getByRole("button", { name: /Remove assignment/i }));

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Remove this assignment?" })).toBeInTheDocument();
      });
    });

    it("a successful delete removes the row, decrements the total count, and shows a success toast", async () => {
      await renderAndExpandGroup(mockRow());
      vi.mocked(dashboardApi.dashboardApi.deleteAssignment).mockResolvedValue(undefined);
      // AC5: the post-delete re-fetch (Subtask 3.5) returns a *different*
      // remaining row (distinct assignment_id) with a lower total_count, so
      // the "Total: N assignments" header text itself is asserted below,
      // not just inferred from the row/toast -- and the deleted row's own
      // button disappearing isn't trivially true just because the mock
      // happens to reuse the same id.
      vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue({
        assignments: [{ ...mockRow(), assignment_id: "id-2", skill_name: "SQL Fundamentals" }],
        total_count: 1,
        page: 1,
        page_size: 50,
      });

      fireEvent.click(screen.getByRole("button", { name: /Remove assignment/i }));
      await waitFor(() => screen.getByRole("button", { name: "Remove Assignment" }));
      fireEvent.click(screen.getByRole("button", { name: "Remove Assignment" }));

      await waitFor(() => {
        expect(dashboardApi.dashboardApi.deleteAssignment).toHaveBeenCalledWith("id-1");
      });
      await waitFor(() => {
        expect(screen.getByText("Casey — Data Visualization removed.")).toBeInTheDocument();
      });
      await waitFor(() => {
        expect(screen.getByText("Total: 1 assignment")).toBeInTheDocument();
      });
      await waitFor(() => {
        expect(screen.queryByRole("button", { name: /Remove assignment/i })).not.toBeInTheDocument();
      });
    });

    it("a failed delete leaves the row in the grid", async () => {
      await renderAndExpandGroup(mockRow());
      vi.mocked(dashboardApi.dashboardApi.deleteAssignment).mockRejectedValueOnce(new Error("Server error"));

      fireEvent.click(screen.getByRole("button", { name: /Remove assignment/i }));
      await waitFor(() => screen.getByRole("button", { name: "Remove Assignment" }));
      fireEvent.click(screen.getByRole("button", { name: "Remove Assignment" }));

      await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent("Server error");
      });
      expect(
        screen.getByRole("button", { name: "Remove assignment for Casey the Continuer Data Visualization" })
      ).toBeInTheDocument();
    });

    it("escalated confirmation copy names the recorded percentage for an In Progress row", async () => {
      await renderAndExpandGroup(mockRow({ status: "In Progress", status_percentage: 45 }));

      fireEvent.click(screen.getByRole("button", { name: /Remove assignment/i }));

      await waitFor(() => {
        expect(screen.getByText(/recorded progress \(45% watched\)/)).toBeInTheDocument();
      });
    });

    it("plain confirmation copy for a Not Started row", async () => {
      await renderAndExpandGroup(mockRow({ status: "Not Started", status_percentage: null }));

      fireEvent.click(screen.getByRole("button", { name: /Remove assignment/i }));

      await waitFor(() => {
        expect(screen.getByRole("heading", { name: "Remove this assignment?" })).toBeInTheDocument();
      });
      expect(screen.queryByText(/recorded progress/i)).not.toBeInTheDocument();
    });
  });

  describe("Story 10.6: search + 15/page pagination (FR-38)", () => {
    function makeRow(overrides: Partial<Record<string, unknown>> = {}) {
      return {
        assignment_id: "id-1",
        employee_id: "emp-1",
        employee_name: "Casey the Continuer",
        employee_group: "Engineering",
        skill_id: "skill-1",
        skill_name: "Data Visualization",
        status: "Not Started" as const,
        status_percentage: null,
        provenance: "Verified" as const,
        last_updated: new Date().toISOString(),
        assignment_created_at: new Date().toISOString(),
        ...overrides,
      };
    }

    it("requests page_size 15 by default (was 50 pre-Story-10.6)", async () => {
      vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue({
        assignments: [],
        total_count: 0,
        page: 1,
        page_size: 15,
      });

      render(<DashboardPage onNewAssignment={() => {}} />);

      await waitFor(() => {
        expect(dashboardApi.dashboardApi.getDashboard).toHaveBeenCalledWith(1, 15, undefined);
      });
    });

    it("renders a search input matching Employee or Skill name", async () => {
      vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue({
        assignments: [makeRow()],
        total_count: 1,
        page: 1,
        page_size: 15,
      });

      render(<DashboardPage onNewAssignment={() => {}} />);

      await waitFor(() => {
        expect(screen.getByTestId("dashboard-search-input")).toBeInTheDocument();
      });
    });

    it("typing a search term re-fetches with that term", async () => {
      vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue({
        assignments: [makeRow()],
        total_count: 1,
        page: 1,
        page_size: 15,
      });

      render(<DashboardPage onNewAssignment={() => {}} />);

      await waitFor(() => {
        expect(dashboardApi.dashboardApi.getDashboard).toHaveBeenCalledWith(1, 15, undefined);
      });

      fireEvent.change(screen.getByTestId("dashboard-search-input"), {
        target: { value: "casey" },
      });

      await waitFor(() => {
        expect(dashboardApi.dashboardApi.getDashboard).toHaveBeenCalledWith(1, 15, "casey");
      });
    });

    it("a new search term resets pagination to page 1", async () => {
      vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue({
        assignments: Array.from({ length: 15 }, (_, i) => makeRow({ assignment_id: `id-${i}`, employee_name: `Employee ${i}` })),
        total_count: 30,
        page: 1,
        page_size: 15,
      });

      render(<DashboardPage onNewAssignment={() => {}} />);

      await waitFor(() => {
        expect(screen.getByRole("button", { name: "Next" })).toBeEnabled();
      });

      fireEvent.click(screen.getByRole("button", { name: "Next" }));

      await waitFor(() => {
        expect(dashboardApi.dashboardApi.getDashboard).toHaveBeenCalledWith(2, 15, undefined);
      });

      fireEvent.change(screen.getByTestId("dashboard-search-input"), {
        target: { value: "skill" },
      });

      await waitFor(() => {
        expect(dashboardApi.dashboardApi.getDashboard).toHaveBeenCalledWith(1, 15, "skill");
      });
    });

    it("shows a distinct empty state when a search term matches nothing", async () => {
      vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValueOnce({
        assignments: [makeRow()],
        total_count: 1,
        page: 1,
        page_size: 15,
      });

      render(<DashboardPage onNewAssignment={() => {}} />);

      await waitFor(() => {
        expect(dashboardApi.dashboardApi.getDashboard).toHaveBeenCalledTimes(1);
      });

      vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValueOnce({
        assignments: [],
        total_count: 0,
        page: 1,
        page_size: 15,
      });

      fireEvent.change(screen.getByTestId("dashboard-search-input"), {
        target: { value: "zzz-no-such-employee-or-skill" },
      });

      await waitFor(() => {
        expect(screen.getByText("No assignments match your search.")).toBeInTheDocument();
      });
      expect(screen.queryByText(/No assignments yet/)).not.toBeInTheDocument();
    });

    it("an empty roster with no search term still shows the original empty-state copy", async () => {
      vi.mocked(dashboardApi.dashboardApi.getDashboard).mockResolvedValue({
        assignments: [],
        total_count: 0,
        page: 1,
        page_size: 15,
      });

      render(<DashboardPage onNewAssignment={() => {}} />);

      await waitFor(() => {
        expect(screen.getByText(/No assignments yet/)).toBeInTheDocument();
      });
      expect(screen.queryByText("No assignments match your search.")).not.toBeInTheDocument();
    });
  });
});
