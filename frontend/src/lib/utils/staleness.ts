/**
 * Shared "Not updated in X days" staleness text (Story 5-6, AC9 / UX-DR15).
 * Extracted from DashboardRow.tsx/ProvenanceDrillDownModal.tsx duplication
 * (code review finding) -- both previously computed differenceInCalendarDays
 * independently with no clamp against clock skew/future timestamps.
 */
import { differenceInCalendarDays } from 'date-fns';

/** Days since `isoDate`, clamped to >=0 (a future/clock-skewed timestamp
 * would otherwise produce a nonsensical negative count) and guarded against
 * an invalid/unparseable date (code review round 2: differenceInCalendarDays
 * on an invalid Date returns NaN, which would otherwise propagate as literal
 * "NaN days" into the UI). */
export function staleDaysSince(isoDate: string): number {
  const date = new Date(isoDate);
  if (isNaN(date.getTime())) return 0;
  return Math.max(0, differenceInCalendarDays(new Date(), date));
}

/** "Not updated today" / "Not updated in 1 day" / "Not updated in 3 days".
 * Code review round 2 (NFR-A2): never returns a suppressible/blank string --
 * a stale row's color highlight must always be paired with text, including
 * at the 0-day boundary (same-day staleness), not just at 1+ days. */
export function formatStaleDaysText(days: number): string {
  if (days === 0) return 'Not updated today';
  return `Not updated in ${days} day${days === 1 ? '' : 's'}`;
}
