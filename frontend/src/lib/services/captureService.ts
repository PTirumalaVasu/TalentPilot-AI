/**
 * CaptureService — Collects watch samples from PlayerAdapter and posts to backend
 * Batches samples locally, posts on interval or queue threshold
 * Handles network errors gracefully per Story 4-2
 */

import type { PlayerAdapter } from '../adapters/playerAdapter';
import axios from 'axios';

interface WatchSample {
  watch_position: number;
  event_time: string;
}

interface RetryState {
  failureCount: number;
  lastFailureTime: number;
}

export interface CaptureServiceConfig {
  assignmentId: string;
  videoUrl: string;
  postIntervalMs?: number; // Batch post frequency (default 12s)
  queueThreshold?: number; // Post when queue reaches this size (default 3)
  maxQueueSize?: number; // Max samples to hold before dropping oldest (default 50)
}

export class CaptureService {
  private adapter: PlayerAdapter;
  private config: Required<CaptureServiceConfig>;
  private queue: WatchSample[] = [];
  private postInterval: number | null = null;
  private isPosting: boolean = false;
  private retryState: RetryState = { failureCount: 0, lastFailureTime: 0 };

  constructor(adapter: PlayerAdapter, config: CaptureServiceConfig) {
    this.adapter = adapter;
    this.config = {
      assignmentId: config.assignmentId,
      videoUrl: config.videoUrl,
      postIntervalMs: config.postIntervalMs ?? 12000,
      queueThreshold: config.queueThreshold ?? 3,
      maxQueueSize: config.maxQueueSize ?? 50,
    };

    this.setupListeners();
    this.startBatchTimer();
  }

  private setupListeners(): void {
    // Listen to adapter's 'timeupdate' event (periodic during playback)
    this.adapter.on('timeupdate', () => {
      this.queueSample();
    });
  }

  private queueSample(): void {
    const sample: WatchSample = {
      watch_position: this.adapter.position(),
      event_time: new Date().toISOString(),
    };

    // Enforce max queue size (drop oldest if full)
    if (this.queue.length >= this.config.maxQueueSize) {
      this.queue.shift();
    }

    this.queue.push(sample);

    // Immediate post if queue threshold reached
    if (this.queue.length >= this.config.queueThreshold) {
      this.post();
    }
  }

  private startBatchTimer(): void {
    this.postInterval = window.setInterval(() => {
      if (this.queue.length > 0) {
        this.post();
      }
    }, this.config.postIntervalMs) as unknown as number;
  }

  private async post(): Promise<void> {
    if (this.isPosting || this.queue.length === 0) return;

    // Implement exponential backoff: wait 1s * 2^failureCount (cap at 30s)
    const now = Date.now();
    const timeSinceLastFailure = now - this.retryState.lastFailureTime;
    const backoffMs = Math.min(1000 * Math.pow(2, this.retryState.failureCount), 30000);

    if (this.retryState.failureCount > 0 && timeSinceLastFailure < backoffMs) {
      // Still in backoff window; skip this post
      return;
    }

    this.isPosting = true;
    const samplesToPost = [...this.queue];
    this.queue = []; // Clear queue immediately

    try {
      // Post the latest sample (or average a few if desired; for now, post latest)
      const latestSample = samplesToPost[samplesToPost.length - 1];

      const response = await axios.post(
        `/api/assignments/${this.config.assignmentId}/progress`,
        {
          watch_position: latestSample.watch_position,
          event_time: latestSample.event_time,
          video_url: this.config.videoUrl,
        }
      );

      this.retryState = { failureCount: 0, lastFailureTime: 0 }; // Reset on success
      console.log('CaptureService: Posted watch progress', response.status);
    } catch (err) {
      // Network error: re-queue samples for retry with backoff
      console.warn('CaptureService: Post failed, re-queuing samples with backoff', err);
      this.queue = [...samplesToPost, ...this.queue]; // Put back at front for priority
      this.retryState = {
        failureCount: this.retryState.failureCount + 1,
        lastFailureTime: now,
      };
    } finally {
      this.isPosting = false;
    }
  }

  /**
   * Flush all queued samples immediately
   * Used by visibility/unload handlers
   */
  async flush(): Promise<void> {
    await this.post();
  }

  /**
   * Clean up: stop batch timer and clear queue
   */
  destroy(): void {
    if (this.postInterval !== null) {
      clearInterval(this.postInterval);
      this.postInterval = null;
    }
    this.queue = [];
  }

  /**
   * Send beacon on tab close / visibility change
   * Does not await; uses navigator.sendBeacon() for best-effort delivery
   */
  flushViaBeacon(): void {
    if (this.queue.length === 0) return;

    const latestSample = this.queue[this.queue.length - 1];
    this.adapter.sendBeacon(latestSample.watch_position, latestSample.event_time);
  }
}
