/**
 * Tests for DeleteAssignmentModal (Story 5.7).
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DeleteAssignmentModal } from "./DeleteAssignmentModal";
import { dashboardApi } from "../../lib/api/dashboardApi";

vi.mock("../../lib/api/dashboardApi", () => ({
  dashboardApi: {
    deleteAssignment: vi.fn(),
  },
}));

describe("DeleteAssignmentModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows plain copy when hasRecordedProgress is false (Not Started)", () => {
    render(
      <DeleteAssignmentModal
        assignmentId="assign-1"
        employeeName="Casey the Continuer"
        skillName="Data Visualization"
        hasRecordedProgress={false}
        progressPercent={null}
        open
        onClose={vi.fn()}
        onDeleted={vi.fn()}
      />
    );

    expect(screen.getByRole("heading", { name: "Remove this assignment?" })).toBeInTheDocument();
    expect(screen.getByText("Casey the Continuer — Data Visualization")).toBeInTheDocument();
    expect(screen.queryByText(/recorded progress/i)).not.toBeInTheDocument();
  });

  it("shows escalated copy naming the percentage when hasRecordedProgress is true with a progressPercent", () => {
    render(
      <DeleteAssignmentModal
        assignmentId="assign-1"
        employeeName="Casey the Continuer"
        skillName="Data Visualization"
        hasRecordedProgress
        progressPercent={73}
        open
        onClose={vi.fn()}
        onDeleted={vi.fn()}
      />
    );

    expect(screen.getByText(/recorded progress \(73% watched\)/)).toBeInTheDocument();
    expect(screen.getByText(/retained for audit/)).toBeInTheDocument();
  });

  it("shows escalated 'Completed' copy when hasRecordedProgress is true and progressPercent is null", () => {
    render(
      <DeleteAssignmentModal
        assignmentId="assign-1"
        employeeName="Casey the Continuer"
        skillName="Data Visualization"
        hasRecordedProgress
        progressPercent={null}
        open
        onClose={vi.fn()}
        onDeleted={vi.fn()}
      />
    );

    expect(screen.getByText(/recorded progress \(Completed\)/)).toBeInTheDocument();
  });

  it("Cancel sends no request and closes", async () => {
    const onClose = vi.fn();
    render(
      <DeleteAssignmentModal
        assignmentId="assign-1"
        employeeName="Casey the Continuer"
        skillName="Data Visualization"
        hasRecordedProgress={false}
        progressPercent={null}
        open
        onClose={onClose}
        onDeleted={vi.fn()}
      />
    );

    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));

    expect(dashboardApi.deleteAssignment).not.toHaveBeenCalled();
    expect(onClose).toHaveBeenCalled();
  });

  it("Confirm calls deleteAssignment with the right id, then onDeleted and onClose", async () => {
    vi.mocked(dashboardApi.deleteAssignment).mockResolvedValue(undefined);
    const onClose = vi.fn();
    const onDeleted = vi.fn();
    render(
      <DeleteAssignmentModal
        assignmentId="assign-1"
        employeeName="Casey the Continuer"
        skillName="Data Visualization"
        hasRecordedProgress={false}
        progressPercent={null}
        open
        onClose={onClose}
        onDeleted={onDeleted}
      />
    );

    await userEvent.click(screen.getByRole("button", { name: "Remove Assignment" }));

    await waitFor(() => {
      expect(dashboardApi.deleteAssignment).toHaveBeenCalledWith("assign-1");
      expect(onDeleted).toHaveBeenCalledWith("assign-1");
      expect(onClose).toHaveBeenCalled();
    });
  });

  it("failure shows an inline role=alert error, keeps the modal open, does not call onDeleted", async () => {
    vi.mocked(dashboardApi.deleteAssignment).mockRejectedValueOnce(new Error("Server error"));
    const onDeleted = vi.fn();
    const onClose = vi.fn();
    render(
      <DeleteAssignmentModal
        assignmentId="assign-1"
        employeeName="Casey the Continuer"
        skillName="Data Visualization"
        hasRecordedProgress={false}
        progressPercent={null}
        open
        onClose={onClose}
        onDeleted={onDeleted}
      />
    );

    await userEvent.click(screen.getByRole("button", { name: "Remove Assignment" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Server error");
    });
    expect(screen.getByRole("heading", { name: "Remove this assignment?" })).toBeInTheDocument();
    expect(onDeleted).not.toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
  });

  it("code review regression: cancelling while a delete is in flight does not leave Cancel/Confirm permanently disabled on reopen", async () => {
    let resolveDelete: () => void;
    const pendingDelete = new Promise<void>((resolve) => {
      resolveDelete = resolve;
    });
    vi.mocked(dashboardApi.deleteAssignment).mockReturnValue(pendingDelete);
    const onClose = vi.fn();

    const { rerender } = render(
      <DeleteAssignmentModal
        assignmentId="assign-1"
        employeeName="Casey the Continuer"
        skillName="Data Visualization"
        hasRecordedProgress={false}
        progressPercent={null}
        open
        onClose={onClose}
        onDeleted={vi.fn()}
      />
    );

    await userEvent.click(screen.getByRole("button", { name: "Remove Assignment" }));
    expect(screen.getByRole("button", { name: "Remove Assignment" })).toBeDisabled();
    // Cancel itself is disabled while submitting -- a real user can only
    // escape mid-flight via Escape/backdrop-click, which the Dialog
    // primitive's own keydown listener handles independently of any
    // button's disabled state.
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();

    await userEvent.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalled();

    // Parent closes the modal, then the admin reopens it (same or a
    // different row) -- simulated here via open=false then open=true again.
    rerender(
      <DeleteAssignmentModal
        assignmentId="assign-1"
        employeeName="Casey the Continuer"
        skillName="Data Visualization"
        hasRecordedProgress={false}
        progressPercent={null}
        open={false}
        onClose={onClose}
        onDeleted={vi.fn()}
      />
    );
    rerender(
      <DeleteAssignmentModal
        assignmentId="assign-2"
        employeeName="Morgan"
        skillName="SQL Fundamentals"
        hasRecordedProgress={false}
        progressPercent={null}
        open
        onClose={onClose}
        onDeleted={vi.fn()}
      />
    );

    // Before the fix, submitting stayed true forever -- both buttons would
    // still render disabled here.
    expect(screen.getByRole("button", { name: "Cancel" })).not.toBeDisabled();
    expect(screen.getByRole("button", { name: "Remove Assignment" })).not.toBeDisabled();

    // The original (now-stale) request resolving later must not resurrect
    // any state onto the new row's modal.
    resolveDelete!();
    await new Promise((r) => setTimeout(r, 0));
    expect(screen.getByRole("button", { name: "Cancel" })).not.toBeDisabled();
    expect(screen.getByRole("button", { name: "Remove Assignment" })).not.toBeDisabled();
  });

  it("renders nothing when open is false", () => {
    render(
      <DeleteAssignmentModal
        assignmentId="assign-1"
        employeeName="Casey the Continuer"
        skillName="Data Visualization"
        hasRecordedProgress={false}
        progressPercent={null}
        open={false}
        onClose={vi.fn()}
        onDeleted={vi.fn()}
      />
    );

    expect(screen.queryByRole("heading", { name: "Remove this assignment?" })).not.toBeInTheDocument();
  });
});
