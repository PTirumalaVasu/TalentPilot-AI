/**
 * YouTubeAdapter — Implements PlayerAdapter over YouTube IFrame API
 * Uses polling-based position capture (5-10s intervals) + onStateChange events
 * per AD-9 and technical-third-party-video-embeds research
 */

import type { PlayerAdapter, PlayerEventType } from './playerAdapter';

declare global {
  interface Window {
    YT: any;
    onYouTubeIframeAPIReady: () => void;
  }
}

interface EventHandlers {
  [key: string]: (() => void)[];
}

export class YouTubeAdapter implements PlayerAdapter {
  private player: any;
  private pollingInterval: number | null = null;
  private eventHandlers: EventHandlers = {};
  private pollFrequency: number; // ms, randomized between 5000-10000

  constructor(player: any, pollFrequency = 7500) {
    this.player = player;
    this.pollFrequency = pollFrequency;
    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    if (!this.player || !this.player.addEventListener) return;

    // Listen to YouTube player state changes (PLAYING, PAUSED, ENDED, BUFFERING, etc.)
    this.player.addEventListener('onStateChange', (event: any) => {
      const state = event.data;
      const YT = window.YT;

      // Validate YouTube API is fully initialized before using PlayerState
      if (!YT || !YT.PlayerState) {
        console.warn('YouTubeAdapter: YouTube API not fully initialized');
        return;
      }

      // PLAYING (1): start polling
      if (state === YT.PlayerState.PLAYING) {
        this.startPolling();
        this.emit('play');
      }
      // PAUSED (2)
      else if (state === YT.PlayerState.PAUSED) {
        this.stopPolling();
        this.emit('pause');
      }
      // ENDED (0)
      else if (state === YT.PlayerState.ENDED) {
        this.stopPolling();
        this.emit('ended');
      }
    });
  }

  private startPolling(): void {
    if (this.pollingInterval !== null) return; // Already polling

    // Emit immediate 'timeupdate' and schedule periodic updates
    this.emit('timeupdate');

    this.pollingInterval = window.setInterval(() => {
      this.emit('timeupdate');
    }, this.pollFrequency) as unknown as number;
  }

  private stopPolling(): void {
    if (this.pollingInterval !== null) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }

  private emit(event: PlayerEventType): void {
    const handlers = this.eventHandlers[event] || [];
    handlers.forEach((handler) => {
      try {
        handler();
      } catch (err) {
        console.error(`YouTubeAdapter: Error in ${event} handler:`, err);
      }
    });
  }

  position(): number {
    if (!this.player || !this.player.getCurrentTime) return 0;
    try {
      return Math.floor(this.player.getCurrentTime());
    } catch {
      return 0;
    }
  }

  duration(): number {
    if (!this.player || !this.player.getDuration) return 0;
    try {
      return Math.floor(this.player.getDuration());
    } catch {
      return 0;
    }
  }

  on(event: PlayerEventType, handler: () => void): void {
    if (!this.eventHandlers[event]) {
      this.eventHandlers[event] = [];
    }
    this.eventHandlers[event].push(handler);
  }

  async sendBeacon(position: number, eventTime: string): Promise<void> {
    // Graceful degradation if sendBeacon not available
    if (!navigator.sendBeacon) {
      console.warn('YouTubeAdapter: navigator.sendBeacon not supported, skipping beacon');
      return;
    }

    try {
      const endpoint = `/api/assignments/${(window as any).CURRENT_ASSIGNMENT_ID}/progress`;
      const payload = new FormData();
      payload.append('watch_position', String(position));
      payload.append('event_time', eventTime);

      // AD-5: Include video URL for server-side anti-spoofing validation
      try {
        const videoUrl = this.player?.getVideoUrl?.();
        if (videoUrl) {
          payload.append('video_url', videoUrl);
        }
      } catch (err) {
        // Video URL not available, continue without it (not critical)
        console.debug('YouTubeAdapter: Could not retrieve video URL for beacon');
      }

      const success = navigator.sendBeacon(endpoint, payload);
      if (!success) {
        console.warn('YouTubeAdapter: sendBeacon returned false (queue full?), data may not be sent');
      }
    } catch (err) {
      console.error('YouTubeAdapter: sendBeacon error:', err);
    }
  }

  /**
   * Clean up: stop polling and clear event handlers
   * Call this when component unmounts
   */
  destroy(): void {
    this.stopPolling();
    this.eventHandlers = {};
  }
}
