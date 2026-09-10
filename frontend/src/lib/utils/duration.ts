/**
 * Best-effort ISO-8601 duration parsing (Story 2.5, Scope Note 6).
 * `metadata.duration` is a raw YouTube-API string (e.g. "PT28M33S"),
 * present only for source="YOUTUBE" content. Percent-watched is display-only
 * -- omit it rather than guess when duration is missing/unparseable.
 */

const ISO8601_DURATION_RE = /^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$/;

export function parseIso8601DurationSeconds(duration: unknown): number | null {
  if (typeof duration !== 'string') return null;
  const match = ISO8601_DURATION_RE.exec(duration);
  if (!match) return null;
  const hours = Number(match[1] ?? 0);
  const minutes = Number(match[2] ?? 0);
  const seconds = Number(match[3] ?? 0);
  return hours * 3600 + minutes * 60 + seconds;
}

export function formatDurationMinutes(durationSeconds: number | null): string | null {
  if (durationSeconds === null || durationSeconds <= 0) return null;
  const minutes = Math.round(durationSeconds / 60);
  return `${minutes} minute${minutes === 1 ? '' : 's'}`;
}

/**
 * Story 6.7 (FR-17a): best-effort parse of the manual-entry duration field's
 * free text (UX spec: "Duration (optional, e.g. 2h 30m)") into hours for the
 * backend's `duration_hours: float | None`. Unparseable/empty input returns
 * null rather than a guessed value (FR-17a's own "no data beats a guessed
 * one" consequence) -- the days-to-complete estimate is simply omitted.
 */
const HOURS_MINUTES_RE = /^(?:(\d+(?:\.\d+)?)\s*h)?\s*(?:(\d+(?:\.\d+)?)\s*m)?$/i;

export function parseDurationToHours(text: string): number | null {
  const trimmed = text.trim();
  if (!trimmed) return null;

  const bareNumber = Number(trimmed);
  if (Number.isFinite(bareNumber) && /^\d+(\.\d+)?$/.test(trimmed)) {
    return bareNumber;
  }

  const match = HOURS_MINUTES_RE.exec(trimmed);
  if (!match || (!match[1] && !match[2])) return null;

  const hours = match[1] ? Number(match[1]) : 0;
  const minutes = match[2] ? Number(match[2]) : 0;
  return hours + minutes / 60;
}

/**
 * Story 6.7/FR-19: `ceil(duration_hours / 5)`, a fixed system-wide pace of
 * 5 hours/day. Pure display derivation -- never persisted (the backend only
 * ever stores `duration_hours`, per FR-19's own consequence).
 */
export function estimateDaysToComplete(durationHours: number | null): number | null {
  if (durationHours === null) return null;
  return Math.ceil(durationHours / 5);
}
