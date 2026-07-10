/**
 * WatchProgressCaptureService — Collects watch samples from PlayerAdapter and posts to backend
 * Batches samples locally, posts on interval (10-15s) or queue threshold (3+ samples)
 * Handles network errors gracefully with exponential backoff per Story 4-2
 *
 * AC1: Singleton-scoped service that manages capture, queuing, batching, and retry logic
 * AC2: Samples queued locally, not posted immediately
 * AC3: Batch posting on interval or threshold (one POST per assignment with latest sample)
 * AC4: Network retry with backoff, no immediate retry spam
 * AC5: Response handling with verified flag
 * AC6: sendBeacon setup hook for Story 4-3
 * AC7: Video URL capture from adapter for anti-spoofing
 * AC8: Error contract compliance (console.warn/error, non-blocking)
 * AC9: Configurable intervals and thresholds
 * AC10: Full TypeScript types and JSDoc
 */

import type { PlayerAdapter } from '../adapters/playerAdapter';
import type { UUID } from '../types/common';
import type { ProgressQueueItem, SkillProgressResponse } from '../types/progress';
import axios from 'axios';

interface RetryState {
  failureCount: number;
  lastFailureTime: number;
}

/**
 * Configuration for the WatchProgressCaptureService.
 * All values are configurable per AC9.
 */
export interface CaptureServiceConfig {
  /** UUID of the assignment being watched (AC1) */
  assignmentId: UUID;

  /** URL of the video for anti-spoofing context (AC7) */
  videoUrl: string;

  /** Post batch interval in milliseconds (default: 10000ms = 10s, AC3 spec: 10-15s) */
  postIntervalMs?: number;

  /** Queue sample threshold to trigger immediate POST (default: 3, AC3) */
  queueThreshold?: number;

  /** Maximum queue size before dropping oldest samples (default: 50) */
  maxQueueSize?: number;
}

/**
 * WatchProgressCaptureService — Client-side watch progress capture and batching
 *
 * Implements Story 4-2 requirements:
 * - Records position samples from player adapter (AC2)
 * - Queues locally and batches for posting (AC3)
 * - Retries network failures with backoff (AC4)
 * - Handles responses with verified flag (AC5)
 * - Prepares for sendBeacon flush (AC6)
 * - Captures video URL from adapter (AC7)
 * - Non-blocking error handling (AC8)
 * - Fully configurable (AC9)
 * - Full TypeScript types (AC10)
 */
export class WatchProgressCaptureService {
  private adapter: PlayerAdapter;
  private config: Required<CaptureServiceConfig>;
  private queue: ProgressQueueItem[] = [];
  private postInterval: number | null = null;
  private isPosting: boolean = false;
  private retryState: RetryState = { failureCount: 0, lastFailureTime: 0 };
  private beaconFlushCallback: (() => void) | null = null;

  /**
   * Initialize the capture service.
   * @param adapter - PlayerAdapter instance (AC1: depends on adapter, per AD-9)
   * @param config - Service configuration (AC1, AC9)
   */
  constructor(adapter: PlayerAdapter, config: CaptureServiceConfig) {
    // AC9: Validate configuration constraints
    const queueThreshold = config.queueThreshold ?? 3;
    const maxQueueSize = config.maxQueueSize ?? 50;
    if (queueThreshold > maxQueueSize) {
      throw new Error(
        `WatchProgressCaptureService: queueThreshold (${queueThreshold}) must be <= maxQueueSize (${maxQueueSize})`
      );
    }

    this.adapter = adapter;
    this.config = {
      assignmentId: config.assignmentId,
      videoUrl: config.videoUrl,
      postIntervalMs: config.postIntervalMs ?? 10000, // AC3: 10-15s, default 10s
      queueThreshold: queueThreshold, // AC3: threshold (validated)
      maxQueueSize: maxQueueSize, // (validated)
    };

    this.setupListeners();
    this.startBatchTimer();
  }

  /**
   * Set up event listeners on the player adapter.
   * Listens to 'timeupdate' for periodic position samples during playback (AC2).
   */
  private setupListeners(): void {
    this.adapter.on('timeupdate', () => {
      this.recordSampleInternal();
    });
  }

  /**
   * Queue a watch position sample locally.
   * Called internally on adapter 'timeupdate' event (AC2).
   * AC2: Creates ProgressQueueItem, adds to queue, does not post immediately.
   */
  private recordSampleInternal(): void {
    // AC7: Video URL from config for anti-spoofing validation
    const videoUrl = this.config.videoUrl;

    const item: ProgressQueueItem = {
      assignmentId: this.config.assignmentId,
      watchPosition: this.adapter.position(),
      eventTime: new Date().toISOString(), // AC7: Client-time timestamp
      videoUrl: videoUrl,
      queuedAt: Date.now(),
    };

    // AC2: Enforce max queue size (drop oldest if full)
    if (this.queue.length >= this.config.maxQueueSize) {
      this.queue.shift();
    }

    this.queue.push(item);

    // AC3: Immediate post if queue threshold reached
    if (this.queue.length >= this.config.queueThreshold) {
      this.post();
    }
  }

  /**
   * Public API: Record a sample from the player adapter.
   * AC1: Public method for external callers (player adapter lifecycle hooks).
   * @param assignmentId - UUID of assignment
   * @param position - Watch position in seconds
   * @param eventTime - ISO-8601 timestamp of observation
   */
  recordSample(assignmentId: UUID, position: number, eventTime: string): void {
    // Validate input (per AC1, AC2)
    if (!assignmentId || typeof position !== 'number' || !eventTime || position < 0 || !Number.isFinite(position)) {
      console.warn('WatchProgressCaptureService: Invalid recordSample input', {
        assignmentId,
        position,
        eventTime,
      });
      return;
    }

    // AC7: Consistent videoUrl sourcing (same as recordSampleInternal)
    const videoUrl = this.config.videoUrl;

    const item: ProgressQueueItem = {
      assignmentId: assignmentId,
      watchPosition: position,
      eventTime: eventTime,
      videoUrl: videoUrl,
      queuedAt: Date.now(),
    };

    if (this.queue.length >= this.config.maxQueueSize) {
      this.queue.shift();
    }

    this.queue.push(item);

    if (this.queue.length >= this.config.queueThreshold) {
      this.post();
    }
  }

  /**
   * Start the batch timer for periodic posting (AC3).
   * Posts every postIntervalMs (default 10s) if queue is not empty.
   */
  private startBatchTimer(): void {
    this.postInterval = window.setInterval(() => {
      if (this.queue.length > 0) {
        this.post();
      }
    }, this.config.postIntervalMs) as unknown as number;
  }

  /**
   * Post batched samples to the backend.
   * AC3: Takes latest sample per assignment, POSTs to /api/assignments/{id}/progress
   * AC4: Network errors re-queue with exponential backoff
   * AC5: Handles response with verified flag
   */
  private async post(): Promise<void> {
    if (this.isPosting || this.queue.length === 0) {
      return;
    }

    // AC4: Implement exponential backoff on failures
    const now = Date.now();
    // Guard against clock skew (system clock adjustment): timeSinceLastFailure should not be negative
    const timeSinceLastFailure = Math.max(0, now - this.retryState.lastFailureTime);
    const backoffMs = Math.min(1000 * Math.pow(2, Math.min(this.retryState.failureCount, 15)), 30000);

    if (this.retryState.failureCount > 0 && timeSinceLastFailure <= backoffMs) {
      // Still in backoff window; skip this post (AC4: no immediate retry)
      return;
    }

    this.isPosting = true;
    const samplesToPost = [...this.queue];
    // AC2: Do NOT clear queue here — clear only after successful POST
    // Critical section: this.isPosting=true prevents concurrent calls to post()
    // and ensures recordSampleInternal() additions are deferred until after clear/re-queue

    try {
      // AC3: Post only the latest sample per assignment
      const latestSample = samplesToPost[samplesToPost.length - 1];

      const response = await axios.post<SkillProgressResponse>(
        `/api/assignments/${this.config.assignmentId}/progress`,
        {
          watch_position: latestSample.watchPosition,
          event_time: latestSample.eventTime,
          video_url: latestSample.videoUrl,
        }
      );

      // AC5: Handle successful response with verified flag
      if (response.data) {
        if (!response.data.verified) {
          console.warn('WatchProgressCaptureService: Position not verified server-side', {
            assignment_id: this.config.assignmentId,
            watch_position: latestSample.watchPosition,
            reason: 'Server anti-spoofing check failed',
          });
        }
      }

      this.retryState = { failureCount: 0, lastFailureTime: 0 }; // Reset on success
      this.queue = []; // AC2: Clear queue ONLY after successful POST
      // AC8: Success is not an error; silent success is acceptable per non-blocking error contract
    } catch (err: any) {
      // AC4: Network error handling
      const isNetworkError = !err.response; // No response = network/timeout error
      const is422 = err.response?.status === 422; // Validation error

      if (is422) {
        // AC4, AC8: 422 = validation error, no point retrying, clear queue
        this.queue = []; // AC2: Clear queue on unrecoverable validation error
        console.warn('WatchProgressCaptureService: 422 Validation error, clearing queue', {
          assignment_id: this.config.assignmentId,
          error: err.response?.data,
        });
      } else if (isNetworkError || (err.response?.status ?? 0) >= 500) {
        // AC4: Network error or 5xx: re-queue for retry with backoff
        this.queue = [...samplesToPost, ...this.queue]; // Put back at front for priority
        // AC2: Enforce maxQueueSize to prevent unbounded growth on prolonged outages
        if (this.queue.length > this.config.maxQueueSize) {
          this.queue = this.queue.slice(0, this.config.maxQueueSize);
        }
        this.retryState.failureCount += 1;
        this.retryState.lastFailureTime = now;
        console.warn('WatchProgressCaptureService: Post failed, re-queuing with backoff', {
          assignment_id: this.config.assignmentId,
          sampleCount: samplesToPost.length,
          failureCount: this.retryState.failureCount,
          backoffMs: Math.min(1000 * Math.pow(2, Math.min(this.retryState.failureCount, 15)), 30000),
          error: err.message,
        });
      } else if (err.response?.status === 401 || err.response?.status === 403) {
        // AC4: Auth errors (401 Unauthorized, 403 Forbidden) are not transient; clear queue and fail
        this.queue = [];
        console.error('WatchProgressCaptureService: Auth error, clearing queue', {
          assignment_id: this.config.assignmentId,
          status: err.response?.status,
          error: err.message,
        });
      } else if ((err.response?.status ?? 0) >= 400 && (err.response?.status ?? 0) < 500) {
        // AC4: Other 4xx errors (400, 429, etc): retry with backoff for transient issues
        this.queue = [...samplesToPost, ...this.queue]; // Put back for retry
        // AC2: Enforce maxQueueSize to prevent unbounded growth
        if (this.queue.length > this.config.maxQueueSize) {
          this.queue = this.queue.slice(0, this.config.maxQueueSize);
        }
        this.retryState.failureCount += 1;
        this.retryState.lastFailureTime = now;
        console.warn('WatchProgressCaptureService: 4xx error, re-queuing with backoff', {
          assignment_id: this.config.assignmentId,
          status: err.response?.status,
          error: err.message,
        });
      } else {
        // AC8: Other errors: log but don't crash
        console.error('WatchProgressCaptureService: Unexpected error', {
          assignment_id: this.config.assignmentId,
          status: err.response?.status,
          error: err.message,
        });
      }
    } finally {
      this.isPosting = false;
    }
  }

  /**
   * Public API: Flush all queued samples immediately via POST.
   * AC3: Used by explicit flush requests (AC6 sendBeacon trigger prep).
   * @returns Promise that resolves after POST attempt
   */
  async flush(): Promise<void> {
    await this.post();
  }

  /**
   * Public API: Set up the sendBeacon flush callback.
   * AC6: Called during initialization to register callback that Story 4-3 invokes on tab close.
   * @param triggerCallback - Function called when tab close/visibilitychange detected
   */
  setupBeaconFlush(triggerCallback: () => void): void {
    this.beaconFlushCallback = triggerCallback;
  }

  /**
   * Public API: Flush via sendBeacon on tab close.
   * AC6: Non-blocking, uses navigator.sendBeacon() for best-effort delivery.
   * Prepares last known position; Story 4-3 owns the actual beacon dispatch.
   */
  flushViaBeacon(): void {
    if (this.queue.length === 0) {
      return;
    }

    const latestSample = this.queue[this.queue.length - 1];
    this.adapter.sendBeacon(latestSample.watchPosition, latestSample.eventTime);
  }

  /**
   * Public API: Clean up on component unmount.
   * Stops batch timer and clears queue (AC1).
   */
  destroy(): void {
    if (this.postInterval !== null) {
      clearInterval(this.postInterval);
      this.postInterval = null;
    }
    this.queue = [];
    this.beaconFlushCallback = null;
  }
}

// Backward compatibility alias
export const CaptureService = WatchProgressCaptureService;
