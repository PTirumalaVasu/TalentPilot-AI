/**
 * Common type definitions used across the frontend.
 */

/**
 * UUID — Universally Unique Identifier
 * Used for all entity IDs (assignments, employees, skills, etc.)
 */
export type UUID = string & { readonly __brand: 'UUID' };

/**
 * Create a branded UUID type from a string.
 * @param value - String UUID value
 * @returns Branded UUID type
 */
export const UUID = (value: string): UUID => value as UUID;
