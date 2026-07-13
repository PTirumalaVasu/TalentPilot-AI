/**
 * Direct unit tests for the shared staleness helper (Story 5-6 code review
 * round 2): all prior coverage was indirect through DashboardRow.test.tsx
 * (whose "clamps a future timestamp" case didn't actually exercise the
 * Math.max(0, ...) clamp -- DashboardRow's own display logic masked it) and
 * one ProvenanceDrillDownModal.test.tsx case (14 days, plural only).
 */
import { describe, it, expect } from "vitest";
import { staleDaysSince, formatStaleDaysText } from "./staleness";

describe("staleDaysSince", () => {
  it("returns 0 for a timestamp from today", () => {
    expect(staleDaysSince(new Date().toISOString())).toBe(0);
  });

  it("returns the correct positive day count for a past timestamp", () => {
    const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString();
    expect(staleDaysSince(threeDaysAgo)).toBe(3);
  });

  it("clamps a future timestamp to 0, not a negative number", () => {
    const threeDaysFromNow = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString();
    expect(staleDaysSince(threeDaysFromNow)).toBe(0);
  });

  it("returns 0 for an unparseable date string, not NaN", () => {
    expect(staleDaysSince("not-a-real-date")).toBe(0);
  });

  it("returns 0 for an empty string, not NaN", () => {
    expect(staleDaysSince("")).toBe(0);
  });
});

describe("formatStaleDaysText", () => {
  it("returns distinct, non-blank text at 0 days (never suppressible -- NFR-A2, code review round 2)", () => {
    expect(formatStaleDaysText(0)).toBe("Not updated today");
  });

  it("uses singular 'day' at exactly 1", () => {
    expect(formatStaleDaysText(1)).toBe("Not updated in 1 day");
  });

  it("uses plural 'days' for 2+", () => {
    expect(formatStaleDaysText(2)).toBe("Not updated in 2 days");
    expect(formatStaleDaysText(14)).toBe("Not updated in 14 days");
  });
});
