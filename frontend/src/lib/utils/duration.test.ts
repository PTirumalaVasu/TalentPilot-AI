/**
 * Story 6.7 (FR-17a/FR-19): manual-entry duration parsing + days-to-complete
 * estimate, added alongside the existing ISO-8601-duration helpers above.
 */
import { describe, it, expect } from 'vitest';
import { parseDurationToHours, estimateDaysToComplete } from './duration';

describe('parseDurationToHours', () => {
  it('parses "2h 30m" as 2.5 hours', () => {
    expect(parseDurationToHours('2h 30m')).toBe(2.5);
  });

  it('parses "2h" as 2 hours', () => {
    expect(parseDurationToHours('2h')).toBe(2);
  });

  it('parses "30m" as 0.5 hours', () => {
    expect(parseDurationToHours('30m')).toBe(0.5);
  });

  it('parses a bare number as hours', () => {
    expect(parseDurationToHours('2.5')).toBe(2.5);
  });

  it('is case-insensitive and tolerates surrounding whitespace', () => {
    expect(parseDurationToHours('  1H 15M  ')).toBe(1.25);
  });

  it('returns null for an empty string', () => {
    expect(parseDurationToHours('')).toBeNull();
  });

  it('returns null for unparseable text', () => {
    expect(parseDurationToHours('a while')).toBeNull();
  });
});

describe('estimateDaysToComplete', () => {
  it('rounds up: 4.1 hours -> 1 day', () => {
    expect(estimateDaysToComplete(4.1)).toBe(1);
  });

  it('exactly 5.0 hours -> 1 day', () => {
    expect(estimateDaysToComplete(5.0)).toBe(1);
  });

  it('rounds up: 5.1 hours -> 2 days', () => {
    expect(estimateDaysToComplete(5.1)).toBe(2);
  });

  it('returns null when duration is null', () => {
    expect(estimateDaysToComplete(null)).toBeNull();
  });
});
