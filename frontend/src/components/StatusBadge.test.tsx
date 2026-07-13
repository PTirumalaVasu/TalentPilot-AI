/**
 * Regression test for a code-review finding on Story 5-2: an unknown/
 * unparseable video duration legitimately produces (status: "In Progress",
 * percentage: 0) -- StatusBadge must not infer "Not Started" from
 * percentage === 0 alone, since that silently mislabels content that has
 * genuinely been watched.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("shows 'In Progress' (not 'Not Started') when status is In Progress with an indeterminate 0% (unknown duration)", () => {
    render(<StatusBadge status="In Progress" percentage={0} />);
    expect(screen.getByText("In Progress")).toBeInTheDocument();
    expect(screen.queryByText("Not Started")).not.toBeInTheDocument();
  });

  it("shows the real percentage when status is In Progress with a known duration", () => {
    render(<StatusBadge status="In Progress" percentage={45} />);
    expect(screen.getByText("In Progress (45%)")).toBeInTheDocument();
  });

  it("still shows 'Not Started' when status is genuinely Not Started", () => {
    render(<StatusBadge status="Not Started" percentage={null} />);
    expect(screen.getByText("Not Started")).toBeInTheDocument();
  });

  it("still shows 'Completed' regardless of percentage", () => {
    render(<StatusBadge status="Completed" percentage={null} />);
    expect(screen.getByText("Completed")).toBeInTheDocument();
  });
});

describe("StatusBadge focus + announcement (Story 5-6, AC1/AC2)", () => {
  it("is reachable via real Tab-key traversal from the document body", async () => {
    render(<StatusBadge status="In Progress" percentage={45} />);
    document.body.focus();

    await userEvent.tab();

    expect(document.activeElement).toBe(screen.getByRole("status"));
  });

  it("announces '{Employee} {Skill}: {Status} {percentage}' when employeeName/skillName are provided", () => {
    render(
      <StatusBadge
        status="In Progress"
        percentage={45}
        employeeName="Casey the Continuer"
        skillName="Data Visualization"
      />
    );
    expect(screen.getByRole("status")).toHaveAttribute(
      "aria-label",
      "Casey the Continuer Data Visualization: In Progress (45%)"
    );
  });

  it("falls back to status-only aria-label when employeeName/skillName are omitted", () => {
    render(<StatusBadge status="Completed" percentage={null} />);
    expect(screen.getByRole("status")).toHaveAttribute("aria-label", "Completed");
  });

  it("mutes its own live-region behavior via aria-live=\"off\" (code review round 2: prevents double-announcement against DashboardPage's dedicated aria-live region for the same poll-driven Status change)", () => {
    render(<StatusBadge status="Completed" percentage={null} />);
    expect(screen.getByRole("status")).toHaveAttribute("aria-live", "off");
  });
});
