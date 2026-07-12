/**
 * Regression test for a code-review finding on Story 5-2: an unknown/
 * unparseable video duration legitimately produces (status: "In Progress",
 * percentage: 0) -- StatusBadge must not infer "Not Started" from
 * percentage === 0 alone, since that silently mislabels content that has
 * genuinely been watched.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
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
