/**
 * Tests for DashboardRow's Actions column / [View Details] button (Story 5-2,
 * AC1 -- restores the entry point that a later "align with Rita's prototype"
 * rewrite of this component had silently dropped, reintroducing the exact
 * prototype regression this story exists to fix).
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DashboardRow } from "./DashboardRow";
import type { AssignmentRow } from "../../types/dashboard";

const row: AssignmentRow = {
  assignment_id: "assign-1",
  employee_id: "emp-1",
  employee_name: "Casey the Continuer",
  skill_id: "skill-1",
  skill_name: "Data Visualization",
  status: "In Progress",
  status_percentage: 45,
  provenance: "Verified",
  last_updated: new Date().toISOString(),
  assignment_created_at: new Date().toISOString(),
};

function renderRow(onViewDetails = vi.fn()) {
  return render(
    <table>
      <tbody>
        <DashboardRow row={row} onViewDetails={onViewDetails} />
      </tbody>
    </table>
  );
}

describe("DashboardRow Actions column", () => {
  it("renders a [View Details] button on every row, never hidden", () => {
    renderRow();
    const button = screen.getByRole("button", { name: /view details/i });
    expect(button).toBeInTheDocument();
    expect(button).not.toHaveAttribute("disabled");
  });

  it("calls onViewDetails with this row's assignment_id when clicked", async () => {
    const onViewDetails = vi.fn();
    renderRow(onViewDetails);

    await userEvent.click(screen.getByRole("button", { name: /view details/i }));

    expect(onViewDetails).toHaveBeenCalledWith("assign-1");
    expect(onViewDetails).toHaveBeenCalledTimes(1);
  });

  it("button has an accessible name including the employee and skill", () => {
    renderRow();
    expect(
      screen.getByRole("button", { name: "View details for Casey the Continuer Data Visualization" })
    ).toBeInTheDocument();
  });

  it("is reachable via real Tab-key traversal from the document body, not just button.focus()", async () => {
    renderRow();
    document.body.focus();

    await userEvent.tab();

    expect(document.activeElement).toBe(screen.getByRole("button", { name: /view details/i }));
  });

  it("activates on Enter", async () => {
    const onViewDetails = vi.fn();
    renderRow(onViewDetails);

    screen.getByRole("button", { name: /view details/i }).focus();
    await userEvent.keyboard("{Enter}");

    expect(onViewDetails).toHaveBeenCalledWith("assign-1");
  });

  it("activates on Space (AC1 requires Tab, Enter/Space)", async () => {
    const onViewDetails = vi.fn();
    renderRow(onViewDetails);

    screen.getByRole("button", { name: /view details/i }).focus();
    await userEvent.keyboard(" ");

    expect(onViewDetails).toHaveBeenCalledWith("assign-1");
  });
});
