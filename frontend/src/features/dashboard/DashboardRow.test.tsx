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
  employee_group: "Engineering",
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

    // Story 5-6: the Status badge is now a Tab stop too (AC1/AC2), so it's
    // reached first -- View Details is the row's second Tab stop, not its first.
    await userEvent.tab();
    expect(document.activeElement).toBe(screen.getByRole("status"));

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

describe("DashboardRow Last Updated column (Story 5-4)", () => {
  it("renders a relative-time string for last_updated, not a raw ISO-8601 timestamp", () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString();
    render(
      <table>
        <tbody>
          <DashboardRow row={{ ...row, last_updated: twoHoursAgo }} onViewDetails={vi.fn()} />
        </tbody>
      </table>
    );

    const cell = screen.getByText(/ago$/);
    expect(cell.textContent).toMatch(/\d+ (hour|minute|day)s? ago/);
    expect(cell.textContent).not.toContain(twoHoursAgo);
  });
});

describe("DashboardRow stale-row highlight (Story 5-6, AC9)", () => {
  it("shows red/highlighted styling + 'Not updated in X days' text when provenance is Needs Attention", () => {
    const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString();
    render(
      <table>
        <tbody>
          <DashboardRow
            row={{ ...row, provenance: "Needs Attention", last_updated: threeDaysAgo }}
            onViewDetails={vi.fn()}
          />
        </tbody>
      </table>
    );

    const cell = screen.getByText(/Not updated in 3 days/);
    expect(cell.textContent).toMatch(/ago \(Not updated in 3 days\)/);
    expect(cell.className).toContain("text-red-700");
  });

  it("uses singular 'day' when exactly 1 day stale", () => {
    const oneDayAgo = new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString();
    render(
      <table>
        <tbody>
          <DashboardRow
            row={{ ...row, provenance: "Needs Attention", last_updated: oneDayAgo }}
            onViewDetails={vi.fn()}
          />
        </tbody>
      </table>
    );

    expect(screen.getByText(/Not updated in 1 day\)/)).toBeInTheDocument();
  });

  it("shows neither the red highlight nor the stale text for a non-stale (Verified) row", () => {
    render(
      <table>
        <tbody>
          <DashboardRow row={{ ...row, provenance: "Verified" }} onViewDetails={vi.fn()} />
        </tbody>
      </table>
    );

    expect(screen.queryByText(/Not updated in/)).not.toBeInTheDocument();
  });

  it("shows distinct 'Not updated today' text (not blank, not '0 days') at the 0-day boundary -- color is never the only signal (code review round 2, NFR-A2)", () => {
    const justNow = new Date().toISOString();
    render(
      <table>
        <tbody>
          <DashboardRow
            row={{ ...row, provenance: "Needs Attention", last_updated: justNow }}
            onViewDetails={vi.fn()}
          />
        </tbody>
      </table>
    );

    const cell = screen.getByText(/Not updated today/);
    expect(cell.className).toContain("text-red-700");
    expect(screen.queryByText(/Not updated in 0 days/)).not.toBeInTheDocument();
  });

  it("clamps a future last_updated (clock skew) to 'Not updated today' rather than a negative count (code review round 2)", () => {
    // Several days in the future guarantees differenceInCalendarDays would be
    // clearly negative without the Math.max(0, ...) clamp -- a same-day offset
    // (e.g. 1 hour ahead) can coincidentally already read as 0 days without
    // exercising the clamp at all (round-2 review finding).
    const threeDaysFromNow = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString();
    render(
      <table>
        <tbody>
          <DashboardRow
            row={{ ...row, provenance: "Needs Attention", last_updated: threeDaysFromNow }}
            onViewDetails={vi.fn()}
          />
        </tbody>
      </table>
    );

    expect(screen.getByText(/Not updated today/)).toBeInTheDocument();
    expect(screen.queryByText(/Not updated in -/)).not.toBeInTheDocument();
  });
});
