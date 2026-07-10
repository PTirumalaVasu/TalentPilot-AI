/**
 * TypeScript types for skill progress tracking (Story 4-1).
 *
 * These types correspond to the backend Pydantic schemas and are used
 * for client-side watch progress capture, persistence, and resume functionality.
 */

import { UUID } from './common';

/**
 * Request payload to record a watch position update.
 *
 * Sent from the client to the backend via POST /api/assignments/{assignment_id}/progress.
 * Includes anti-spoofing validation context (video_url) and client-time event_time.
 */
export interface RecordWatchProgressRequest {
  /** UUID of the assignment being watched */
  assignment_id: UUID;

  /** Current watch position in seconds */
  watch_position: number;

  /**
   * ISO-8601 timestamp when this position was observed (client time).
   *
   * Used for event-time-ordered conditional writes:
   * - Older event_time than stored = write skipped (stale write)
   * - Newer event_time than stored = write accepted (newer event)
   * - Newer event_time, lower position = rewind (accepted)
   */
  event_time: string; // ISO-8601 timestamp

  /** Video URL for server-side anti-spoofing validation */
  video_url: string;
}

/**
 * Response with persisted watch progress record.
 *
 * Returned from the backend after a successful progress update.
 * Includes server-side verification and timing information.
 */
export interface SkillProgressResponse {
  /** Progress record ID (internal, for reference only) */
  id: UUID;

  /** Assignment ID (keyed reference) */
  assignment_id: UUID;

  /** Current watch position in seconds */
  watch_position: number;

  /**
   * Event timestamp (client time of observation).
   *
   * Preserved from the request; used for conditional-write logic and
   * ordering writes by event_time rather than position.
   */
  event_time: string; // ISO-8601 timestamp

  /**
   * True if the update passed server-side anti-spoofing checks.
   *
   * Anti-spoofing validates:
   * - Position within bounds (0 <= pos <= duration)
   * - Position advances at realistic rate (prevents instant jumps to 100%)
   * - Session tied to assignment (prevents cross-employee spoofing)
   * - Event time is recent (within 5 minutes, tolerating clock skew)
   *
   * If any check fails, verified=false but the write still persists for debugging.
   */
  verified: boolean;

  /** Server time when the record was persisted (for UI display, "last updated") */
  updated_at: string; // ISO-8601 timestamp
}

/**
 * Client-side capture result: state after a successful POST.
 *
 * Mirrors SkillProgressResponse but may include additional client-side fields
 * for retry logic, local queue management, or conflict resolution.
 */
export interface CapturedProgress extends SkillProgressResponse {
  // Future: could add fields like:
  // retry_count?: number;
  // last_retry_at?: string;
}

/**
 * Client-side queue item for batched progress posting.
 *
 * Used internally by the capture service to batch position samples
 * and queue them for posting to the backend if the network is unavailable.
 */
export interface ProgressQueueItem {
  assignment_id: UUID;
  watch_position: number;
  event_time: string;
  video_url: string;

  /** Optional: timestamp when this item was added to the queue (for aging/TTL logic) */
  queued_at?: number; // milliseconds since epoch
}
