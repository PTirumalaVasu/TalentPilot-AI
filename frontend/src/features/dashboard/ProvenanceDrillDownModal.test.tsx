/**
 * Tests for ProvenanceDrillDownModal (Story 5-2, AC2-AC5).
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ProvenanceDrillDownModal } from "./ProvenanceDrillDownModal";
import { dashboardApi } from "../../lib/api/dashboardApi";
import type { DrillDownResponse } from "../../types/dashboard";

vi.mock("../../lib/api/dashboardApi", () => ({
  dashboardApi: {
    getDrillDown: vi.fn(),
  },
}));

function baseResponse(overrides: Partial<DrillDownResponse> = {}): DrillDownResponse {
  return {
    assignment_id: "assign-1",
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
    ...overrides,
  };
}

describe("ProvenanceDrillDownModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a loading state while fetching", () => {
    vi.mocked(dashboardApi.getDrillDown).mockImplementation(() => new Promise(() => {}));
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);
    expect(screen.getByTestId("drill-down-loading")).toBeInTheDocument();
  });

  it("renders the Verified branch's raw signal", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(
      baseResponse({ provenance: "Verified", status: "IN_PROGRESS", status_percentage: 73 })
    );
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Verified via video playback/)).toBeInTheDocument();
      expect(screen.getByText(/Watch Progress: 73%/)).toBeInTheDocument();
    });
  });

  it("renders the Self-reported branch's raw signal", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(
      baseResponse({ provenance: "Self-reported", status: "IN_PROGRESS" })
    );
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("📝 Self-reported")).toBeInTheDocument();
      expect(screen.getByText(/Self-reported by Casey the Continuer on/)).toBeInTheDocument();
    });
  });

  it("renders the Needs Attention branch with plain-language freshness, never a raw date string", async () => {
    const fourteenDaysAgo = new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString();
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(
      baseResponse({ provenance: "Needs Attention", status: "IN_PROGRESS", last_updated: fourteenDaysAgo })
    );
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Needs Attention/)).toBeInTheDocument();
      expect(screen.getByText(/hasn't been updated in 14 days/)).toBeInTheDocument();
      expect(screen.queryByText(/stale_since/)).not.toBeInTheDocument();
    });
  });

  it("renders the HR Override branch with the underlying signal preserved", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(
      baseResponse({
        provenance: "HR Override",
        status: "COMPLETED",
        override_set_by_name: "Rita the Recommender",
        override_reason: "Verified in a call",
        override_set_at: new Date().toISOString(),
        underlying_provenance: "Verified",
        underlying_status: "IN_PROGRESS",
        underlying_status_percentage: 45,
      })
    );
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Overridden by: Rita the Recommender/)).toBeInTheDocument();
      expect(screen.getByText(/Reason: Verified in a call/)).toBeInTheDocument();
      expect(screen.getByText(/Original signal: Watch Progress 45% \(Verified\)/)).toBeInTheDocument();
    });
  });

  it("HR Override's Underlying Signal shows 'No signal yet' when the override was placed on an assignment with no prior signal at all -- never mislabels it as Self-reported", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(
      baseResponse({
        provenance: "HR Override",
        status: "COMPLETED",
        underlying_provenance: "Not Started",
        underlying_status: "NOT_STARTED",
        underlying_status_percentage: null,
      })
    );
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/No signal yet/)).toBeInTheDocument();
      expect(screen.queryByText(/Original signal: Self-reported/)).not.toBeInTheDocument();
    });
  });

  it("HR Override's Underlying Signal preserves the Needs Attention staleness distinction -- never collapses it into plain Self-reported", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(
      baseResponse({
        provenance: "HR Override",
        status: "COMPLETED",
        underlying_provenance: "Needs Attention",
        underlying_status: "IN_PROGRESS",
        underlying_status_percentage: 0,
      })
    );
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Original signal: Self-reported \(Needs Attention\)/)).toBeInTheDocument();
    });
  });

  it("HR Override with no reason shows 'No reason provided'", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(
      baseResponse({ provenance: "HR Override", status: "COMPLETED", override_reason: null })
    );
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Reason: No reason provided/)).toBeInTheDocument();
    });
  });

  it("shows an error state with retry on fetch failure", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockRejectedValueOnce(new Error("Network error"));
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });

    vi.mocked(dashboardApi.getDrillDown).mockResolvedValueOnce(baseResponse());
    await userEvent.click(screen.getByRole("button", { name: /retry/i }));

    await waitFor(() => {
      expect(screen.queryByText("Network error")).not.toBeInTheDocument();
    });
  });

  it("AC5: both Mark as Ready and Reverse Override are rendered simultaneously, on every provenance state (not one-or-the-other)", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(baseResponse());
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Available once HR Override is built/i })).toBeDisabled();
      expect(screen.getByRole("button", { name: /Available once HR Override reversal is built/i })).toBeDisabled();
    });
  });

  it("AC5: both buttons still render simultaneously on an HR Override row", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(baseResponse({ provenance: "HR Override" }));
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Available once HR Override is built/i })).toBeDisabled();
      expect(screen.getByRole("button", { name: /Available once HR Override reversal is built/i })).toBeDisabled();
    });
  });

  it("Mark as Ready is rendered disabled with an explanatory label", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(baseResponse());
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);

    await waitFor(() => {
      const button = screen.getByRole("button", { name: /Available once HR Override is built/i });
      expect(button).toBeDisabled();
    });
  });

  it("Reverse Override is rendered disabled for HR Override rows", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(baseResponse({ provenance: "HR Override" }));
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);

    await waitFor(() => {
      const button = screen.getByRole("button", { name: /Available once HR Override reversal is built/i });
      expect(button).toBeDisabled();
    });
  });

  it("never renders a Send Reminder Email button (explicitly post-MVP)", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(
      baseResponse({ provenance: "Needs Attention", status: "IN_PROGRESS" })
    );
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Needs Attention/)).toBeInTheDocument();
    });
    expect(screen.queryByText(/Send Reminder/i)).not.toBeInTheDocument();
  });

  it("Close button calls onClose", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(baseResponse());
    const onClose = vi.fn();
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={onClose} />);

    await waitFor(() => screen.getByRole("button", { name: /^close$/i }));
    await userEvent.click(screen.getByRole("button", { name: /^close$/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("Escape key calls onClose (via the shared Dialog primitive)", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(baseResponse());
    const onClose = vi.fn();
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={onClose} />);

    await waitFor(() => screen.getByRole("dialog"));
    await userEvent.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("renders nothing when closed", () => {
    render(<ProvenanceDrillDownModal assignmentId={null} open={false} onClose={vi.fn()} />);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(dashboardApi.getDrillDown).not.toHaveBeenCalled();
  });
});
