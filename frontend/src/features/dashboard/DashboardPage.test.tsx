/**
 * Tests for DashboardPage component (Story 5-1).
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { createRef } from "react";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import { DashboardPage, type DashboardPageHandle } from "./DashboardPage";
import * as dashboardApi from "../../lib/api/dashboardApi";

// Mock the dashboardApi module
vi.mock("../../lib/api/dashboardApi", () => ({
  dashboardApi: {
    getDashboard: vi.fn(),
    getDrillDown: vi.fn(),
    setOverride: vi.fn(),
  },
}));

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state on mount", () => {
    // Mock API to delay response
    vi.mocked(dashboardApi.dashboardApi.getDashboard).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<DashboardPage />);
    expect(screen.getByText(/Loading assignments/i)).toBeInTheDocument();
  });

  it("renders assignment grid when data loads", async () => {
    const mockData = {
      assignments: [
        {
          assignment_id: "id-1",
          employee_id: "emp-1",
          employee_name: "Casey the Continuer",
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

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Casey the Continuer")).toBeInTheDocument();
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

    render(<DashboardPage />);

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

    render(<DashboardPage />);

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

    render(<DashboardPage />);

    await waitFor(() => {
      const buttons = screen.getAllByText("View Details");
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

    render(<DashboardPage />);

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

    render(<DashboardPage />);

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

    render(<DashboardPage />);

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

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/Page 1 of 3/)).toBeInTheDocument();
      expect(screen.getByText(/Total: 125 assignments/)).toBeInTheDocument();
    });
  });

  it("keyboard navigation works - View Details button is focusable", async () => {
    const mockData = {
      assignments: [
        {
          assignment_id: "id-1",
          employee_id: "emp-1",
          employee_name: "Test Employee",
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

    render(<DashboardPage />);

    // Await for the grid to render
    await waitFor(() => {
      expect(screen.getByText("Test Employee")).toBeInTheDocument();
    });

    // Check that View Details button exists and is focusable
    const viewDetailsButtons = screen.getAllByRole("button", { name: /View Details/i });
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

    await waitFor(() => {
      expect(screen.getByText("Casey the Continuer")).toBeInTheDocument();
    });
    expect(dashboardApi.dashboardApi.getDashboard).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: /View Details/i }));

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
});

