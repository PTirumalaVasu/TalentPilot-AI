/**
 * PlayerAdapter Interface — normalized contract for video players
 * Abstracts YouTube, Vimeo, and other providers to a single interface
 * per AD-9 (Adapter Pattern for player decoupling)
 */

export type PlayerEventType = 'play' | 'pause' | 'ended' | 'timeupdate';

export interface PlayerAdapter {
  /**
   * Returns current playback position in seconds.
   * Safe to call at any time; returns 0 if not initialized or video not started.
   */
  position(): number;

  /**
   * Returns total video duration in seconds.
   * May return 0 if video metadata not yet loaded.
   */
  duration(): number;

  /**
   * Register event listener for player state changes.
   * Events: 'play' (playback started), 'pause' (paused),
   *         'ended' (reached end), 'timeupdate' (periodic position update during play)
   * Handler is called with no arguments; caller should use position() to get current state.
   */
  on(event: PlayerEventType, handler: () => void): void;

  /**
   * Flush current position to server via navigator.sendBeacon()
   * Used on tab close / visibility change to save progress without blocking unload.
   * @param position Current watch position in seconds
   * @param eventTime ISO-8601 timestamp of when position was observed client-side
   * @returns Promise resolving after sendBeacon() call (not guaranteed delivery)
   */
  sendBeacon(position: number, eventTime: string): Promise<void>;
}
