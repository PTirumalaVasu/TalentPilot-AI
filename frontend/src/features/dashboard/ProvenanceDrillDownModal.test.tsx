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
    setOverride: vi.fn(),
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

  it("Finding 3: a defensive blank-string override_reason still shows 'No reason provided', not a blank line", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(
      baseResponse({ provenance: "HR Override", status: "COMPLETED", override_reason: "" })
    );
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Reason: No reason provided/)).toBeInTheDocument();
    });
  });

  describe("Mark as Ready confirm flow (Story 5.5)", () => {
    async function openConfirmView() {
      vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(baseResponse());
      render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);
      await waitFor(() => screen.getByRole("button", { name: "Mark as Ready" }));
      await userEvent.click(screen.getByRole("button", { name: "Mark as Ready" }));
    }

    it("clicking Mark as Ready opens a confirm view with the employee/skill names and a Reason field", async () => {
      await openConfirmView();

      expect(
        screen.getByRole("heading", { name: "Mark Casey the Continuer as Ready for Data Visualization?" })
      ).toBeInTheDocument();
      expect(screen.getByLabelText(/Reason \(optional\)/)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Confirm" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
    });

    it("Cancel returns to the detail view without calling setOverride", async () => {
      await openConfirmView();

      await userEvent.click(screen.getByRole("button", { name: "Cancel" }));

      expect(screen.getByRole("button", { name: "Mark as Ready" })).toBeInTheDocument();
      expect(dashboardApi.setOverride).not.toHaveBeenCalled();
    });

    it("Confirm calls setOverride with the trimmed reason, updates the view, and reports a success message via onOverrideChanged", async () => {
      const onOverrideChanged = vi.fn();
      vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(baseResponse());
      vi.mocked(dashboardApi.setOverride).mockResolvedValue(
        baseResponse({
          provenance: "HR Override",
          status: "COMPLETED",
          override_set_by_name: "Rita the Recommender",
          override_reason: "Verified in call",
          underlying_provenance: "Not Started",
          underlying_status: "NOT_STARTED",
        })
      );
      render(
        <ProvenanceDrillDownModal
          assignmentId="assign-1"
          open
          onClose={vi.fn()}
          onOverrideChanged={onOverrideChanged}
        />
      );
      await waitFor(() => screen.getByRole("button", { name: "Mark as Ready" }));
      await userEvent.click(screen.getByRole("button", { name: "Mark as Ready" }));

      await userEvent.type(screen.getByLabelText(/Reason \(optional\)/), "  Verified in call  ");
      await userEvent.click(screen.getByRole("button", { name: "Confirm" }));

      await waitFor(() => {
        expect(dashboardApi.setOverride).toHaveBeenCalledWith("assign-1", "set", "Verified in call");
      });
      await waitFor(() => {
        expect(screen.getByText(/Overridden by: Rita the Recommender/)).toBeInTheDocument();
      });
      // Confirm view closed, Mark as Ready is now absent (provenance is HR Override).
      expect(screen.queryByRole("button", { name: "Mark as Ready" })).not.toBeInTheDocument();
      expect(onOverrideChanged).toHaveBeenCalledWith(
        "Casey the Continuer marked as Ready for Data Visualization."
      );
    });

    it("an empty/whitespace-only reason is sent as undefined, not an empty string", async () => {
      vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(baseResponse());
      vi.mocked(dashboardApi.setOverride).mockResolvedValue(baseResponse({ provenance: "HR Override" }));
      await openConfirmView();

      await userEvent.type(screen.getByLabelText(/Reason \(optional\)/), "   ");
      await userEvent.click(screen.getByRole("button", { name: "Confirm" }));

      await waitFor(() => {
        expect(dashboardApi.setOverride).toHaveBeenCalledWith("assign-1", "set", undefined);
      });
    });

    it("Confirm failure shows an error, stays in the confirm view, and keeps the typed reason", async () => {
      vi.mocked(dashboardApi.setOverride).mockRejectedValueOnce(new Error("Server error"));
      await openConfirmView();

      await userEvent.type(screen.getByLabelText(/Reason \(optional\)/), "Verified in call");
      await userEvent.click(screen.getByRole("button", { name: "Confirm" }));

      await waitFor(() => {
        expect(screen.getByText("Server error")).toBeInTheDocument();
      });
      expect(screen.getByRole("heading", { name: /Mark Casey the Continuer as Ready/ })).toBeInTheDocument();
      expect(screen.getByLabelText(/Reason \(optional\)/)).toHaveValue("Verified in call");
    });
  });

  describe("Reverse Override confirm flow (Story 5.5b)", () => {
    async function openReversalConfirmView(overrides: Partial<DrillDownResponse> = {}) {
      vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(
        baseResponse({
          provenance: "HR Override",
          status: "COMPLETED",
          override_set_by_name: "Rita the Recommender",
          override_set_at: new Date("2026-07-09T12:00:00Z").toISOString(),
          ...overrides,
        })
      );
      render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);
      await waitFor(() => screen.getByRole("button", { name: "Reverse Override" }));
      await userEvent.click(screen.getByRole("button", { name: "Reverse Override" }));
    }

    it("clicking Reverse Override opens a confirm view with the override summary and underlying-signal preview", async () => {
      await openReversalConfirmView({
        underlying_provenance: "Verified",
        underlying_status: "IN_PROGRESS",
        underlying_status_percentage: 65,
      });

      expect(screen.getByRole("heading", { name: "Remove this HR Override?" })).toBeInTheDocument();
      // Code review finding, Story 5-5b review: this must render the same
      // relative-time format the detail view's "Overridden at:" line already
      // uses (e.g. "3 days ago"), not a raw locale date -- otherwise the same
      // override_set_at timestamp reads inconsistently across the two views.
      expect(screen.getByText(/Status: Completed \(set by Rita the Recommender .* ago\)/)).toBeInTheDocument();
      expect(screen.getByText(/Currently: Watch Progress 65% \(Verified\)/)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Remove Override" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
    });

    it("shows the no-signal case as a real string, not a blank line, when there's no underlying signal at all", async () => {
      await openReversalConfirmView({
        underlying_provenance: null,
        underlying_status: null,
        underlying_status_percentage: null,
      });

      expect(
        screen.getByText(/Currently: No signal yet — nothing had been watched or reported/)
      ).toBeInTheDocument();
    });

    it("Cancel returns to the detail view without calling setOverride, override stays active", async () => {
      await openReversalConfirmView({ underlying_provenance: "Verified" });

      await userEvent.click(screen.getByRole("button", { name: "Cancel" }));

      expect(screen.getByRole("button", { name: "Reverse Override" })).toBeInTheDocument();
      expect(dashboardApi.setOverride).not.toHaveBeenCalled();
    });

    it("Remove Override calls setOverride with 'unset' and no reason argument, updates the view, and reports a signal-aware success message", async () => {
      const onOverrideChanged = vi.fn();
      vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(
        baseResponse({ provenance: "HR Override", status: "COMPLETED", override_set_by_name: "Rita the Recommender" })
      );
      vi.mocked(dashboardApi.setOverride).mockResolvedValue(
        baseResponse({
          provenance: "Verified",
          status: "IN_PROGRESS",
          status_percentage: 65,
          underlying_provenance: null,
        })
      );
      render(
        <ProvenanceDrillDownModal
          assignmentId="assign-1"
          open
          onClose={vi.fn()}
          onOverrideChanged={onOverrideChanged}
        />
      );
      await waitFor(() => screen.getByRole("button", { name: "Reverse Override" }));
      await userEvent.click(screen.getByRole("button", { name: "Reverse Override" }));
      await userEvent.click(screen.getByRole("button", { name: "Remove Override" }));

      await waitFor(() => {
        expect(dashboardApi.setOverride).toHaveBeenCalledWith("assign-1", "unset");
      });
      // Confirm view closed, detail view now shows Mark as Ready (provenance is no longer HR Override).
      await waitFor(() => {
        expect(screen.getByRole("button", { name: "Mark as Ready" })).toBeInTheDocument();
      });
      expect(screen.queryByRole("button", { name: "Reverse Override" })).not.toBeInTheDocument();
      expect(onOverrideChanged).toHaveBeenCalledWith("Override removed. Status now based on video progress.");
    });

    it("the toast message reads the response's own provenance, not underlying_provenance (Self-reported branch, previously untested)", async () => {
      // Fixture deliberately makes response.provenance and
      // response.underlying_provenance disagree, so this test actually fails
      // if the code regresses to reading the wrong field (the exact bug this
      // story's Debug Log documents catching) -- unlike a fixture where both
      // fields map to the same message, which can't tell the two apart.
      const onOverrideChanged = vi.fn();
      vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(
        baseResponse({ provenance: "HR Override", status: "COMPLETED", override_set_by_name: "Rita the Recommender" })
      );
      vi.mocked(dashboardApi.setOverride).mockResolvedValue(
        baseResponse({ provenance: "Self-reported", underlying_provenance: null })
      );
      render(
        <ProvenanceDrillDownModal
          assignmentId="assign-1"
          open
          onClose={vi.fn()}
          onOverrideChanged={onOverrideChanged}
        />
      );
      await waitFor(() => screen.getByRole("button", { name: "Reverse Override" }));
      await userEvent.click(screen.getByRole("button", { name: "Reverse Override" }));
      await userEvent.click(screen.getByRole("button", { name: "Remove Override" }));

      await waitFor(() => {
        expect(onOverrideChanged).toHaveBeenCalledWith(
          "Override removed. Status now based on self-reported progress."
        );
      });
    });

    it("the toast message uses the same self-reported wording for the Needs Attention branch (fallthrough case)", async () => {
      const onOverrideChanged = vi.fn();
      vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(
        baseResponse({ provenance: "HR Override", status: "COMPLETED", override_set_by_name: "Rita the Recommender" })
      );
      vi.mocked(dashboardApi.setOverride).mockResolvedValue(
        baseResponse({ provenance: "Needs Attention", underlying_provenance: null })
      );
      render(
        <ProvenanceDrillDownModal
          assignmentId="assign-1"
          open
          onClose={vi.fn()}
          onOverrideChanged={onOverrideChanged}
        />
      );
      await waitFor(() => screen.getByRole("button", { name: "Reverse Override" }));
      await userEvent.click(screen.getByRole("button", { name: "Reverse Override" }));
      await userEvent.click(screen.getByRole("button", { name: "Remove Override" }));

      await waitFor(() => {
        expect(onOverrideChanged).toHaveBeenCalledWith(
          "Override removed. Status now based on self-reported progress."
        );
      });
    });

    it("the toast message falls back to the no-prior-progress wording when the response's provenance is Not Started", async () => {
      const onOverrideChanged = vi.fn();
      vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(
        baseResponse({ provenance: "HR Override", status: "COMPLETED", override_set_by_name: "Rita the Recommender" })
      );
      vi.mocked(dashboardApi.setOverride).mockResolvedValue(
        baseResponse({ provenance: "Not Started", underlying_provenance: null })
      );
      render(
        <ProvenanceDrillDownModal
          assignmentId="assign-1"
          open
          onClose={vi.fn()}
          onOverrideChanged={onOverrideChanged}
        />
      );
      await waitFor(() => screen.getByRole("button", { name: "Reverse Override" }));
      await userEvent.click(screen.getByRole("button", { name: "Reverse Override" }));
      await userEvent.click(screen.getByRole("button", { name: "Remove Override" }));

      await waitFor(() => {
        expect(onOverrideChanged).toHaveBeenCalledWith(
          "Override removed. No prior progress recorded — status now shows Not Started."
        );
      });
    });

    it("Remove Override failure shows an error and stays in the confirm view", async () => {
      vi.mocked(dashboardApi.setOverride).mockRejectedValueOnce(new Error("Server error"));
      await openReversalConfirmView({ underlying_provenance: "Verified" });

      await userEvent.click(screen.getByRole("button", { name: "Remove Override" }));

      await waitFor(() => {
        expect(screen.getByText("Server error")).toBeInTheDocument();
      });
      expect(screen.getByRole("heading", { name: "Remove this HR Override?" })).toBeInTheDocument();
    });

    it("a stale response (assignment switched mid-request) does not overwrite what's now on screen", async () => {
      let resolveFirst: (value: DrillDownResponse) => void;
      const firstCallPromise = new Promise<DrillDownResponse>((resolve) => {
        resolveFirst = resolve;
      });
      vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(
        baseResponse({
          provenance: "HR Override",
          status: "COMPLETED",
          override_set_by_name: "Rita the Recommender",
          underlying_provenance: "Verified",
        })
      );
      vi.mocked(dashboardApi.setOverride).mockReturnValueOnce(firstCallPromise);
      const { rerender } = render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);
      await waitFor(() => screen.getByRole("button", { name: "Reverse Override" }));
      await userEvent.click(screen.getByRole("button", { name: "Reverse Override" }));
      await userEvent.click(screen.getByRole("button", { name: "Remove Override" }));

      // Re-render the same instance with a different assignmentId while the
      // first reversal request is still in flight -- mirrors the modal being
      // reused for a second row before the first submit resolves.
      vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(
        baseResponse({ provenance: "HR Override", status: "COMPLETED", override_set_by_name: "Someone Else" })
      );
      rerender(<ProvenanceDrillDownModal assignmentId="assign-2" open onClose={vi.fn()} />);
      await waitFor(() => screen.getByText(/Overridden by: Someone Else/));

      resolveFirst!(baseResponse({ provenance: "Verified" }));

      // The late response from the first (now-stale) request must not clobber
      // the second assignment's currently-displayed HR Override state.
      await waitFor(() => {
        expect(screen.getByText(/Overridden by: Someone Else/)).toBeInTheDocument();
      });
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

  it("Story 5.5/5.5b: Mark as Ready is visible and enabled when Provenance is not HR Override; Reverse Override is absent (mutually exclusive)", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(baseResponse());
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Mark as Ready" })).toBeEnabled();
      expect(screen.queryByRole("button", { name: "Reverse Override" })).not.toBeInTheDocument();
    });
  });

  it("Story 5.5b: Mark as Ready is absent entirely on an HR Override row; Reverse Override is visible and enabled instead", async () => {
    vi.mocked(dashboardApi.getDrillDown).mockResolvedValue(baseResponse({ provenance: "HR Override" }));
    render(<ProvenanceDrillDownModal assignmentId="assign-1" open onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.queryByRole("button", { name: "Mark as Ready" })).not.toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Reverse Override" })).toBeEnabled();
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
