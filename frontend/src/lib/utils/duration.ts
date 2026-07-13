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

export function computePercentWatched(watchPosition: number, durationSeconds: number | null): number | null {
  if (durationSeconds === null || durationSeconds <= 0) return null;
  return Math.min(100, Math.round((watchPosition / durationSeconds) * 100));
}
