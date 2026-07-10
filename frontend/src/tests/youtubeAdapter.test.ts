/**
 * Unit tests for YouTubeAdapter
 * Mocks YouTube IFrame API; tests polling, event handling, and sendBeacon
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { YouTubeAdapter } from '../lib/adapters/youtubeAdapter';

// Mock navigator.sendBeacon
global.navigator = {
  ...global.navigator,
  sendBeacon: vi.fn(() => true),
};

describe('YouTubeAdapter', () => {
  let mockPlayer: any;
  let adapter: YouTubeAdapter;
  let stateChangeCallback: any = null;

  beforeEach(() => {
    // Reset sendBeacon mock
    vi.clearAllMocks();
    vi.useFakeTimers();

    // Create mock YouTube player
    mockPlayer = {
      getCurrentTime: vi.fn(() => 45.5),
      getDuration: vi.fn(() => 300), // 5 minutes
      addEventListener: vi.fn((event: string, callback: any) => {
        if (event === 'onStateChange') {
          stateChangeCallback = callback;
        }
      }),
    };

    // Mock window.YT.PlayerState
    (window as any).YT = {
      PlayerState: {
        UNSTARTED: -1,
        ENDED: 0,
        PLAYING: 1,
        PAUSED: 2,
        BUFFERING: 3,
        CUED: 5,
      },
    };

    adapter = new YouTubeAdapter(mockPlayer, 5000); // 5s polling for tests
  });

  afterEach(() => {
    adapter.destroy();
    vi.useRealTimers();
  });

  // ===== Position & Duration Tests =====

  it('should return current position from player', () => {
    const pos = adapter.position();
    expect(pos).toBe(45);
    expect(mockPlayer.getCurrentTime).toHaveBeenCalled();
  });

  it('should floor position to integer', () => {
    mockPlayer.getCurrentTime.mockReturnValue(45.9);
    expect(adapter.position()).toBe(45);
  });

  it('should return 0 for position if player not ready', () => {
    adapter.destroy();
    const noPlayerAdapter = new YouTubeAdapter(null, 5000);
    expect(noPlayerAdapter.position()).toBe(0);
    noPlayerAdapter.destroy();
  });

  it('should return duration from player', () => {
    const dur = adapter.duration();
    expect(dur).toBe(300);
    expect(mockPlayer.getDuration).toHaveBeenCalled();
  });

  it('should floor duration to integer', () => {
    mockPlayer.getDuration.mockReturnValue(300.7);
    expect(adapter.duration()).toBe(300);
  });

  it('should return 0 for duration if player not ready', () => {
    adapter.destroy();
    const noPlayerAdapter = new YouTubeAdapter(null, 5000);
    expect(noPlayerAdapter.duration()).toBe(0);
    noPlayerAdapter.destroy();
  });

  // ===== Event Listener Tests =====

  it('should fire play event when PLAYING state received', () => {
    const playHandler = vi.fn();
    adapter.on('play', playHandler);

    stateChangeCallback({ data: (window as any).YT.PlayerState.PLAYING });

    expect(playHandler).toHaveBeenCalled();
  });

  it('should fire pause event when PAUSED state received', () => {
    const pauseHandler = vi.fn();
    adapter.on('pause', pauseHandler);

    stateChangeCallback({ data: (window as any).YT.PlayerState.PAUSED });

    expect(pauseHandler).toHaveBeenCalled();
  });

  it('should fire ended event when ENDED state received', () => {
    const endedHandler = vi.fn();
    adapter.on('ended', endedHandler);

    stateChangeCallback({ data: (window as any).YT.PlayerState.ENDED });

    expect(endedHandler).toHaveBeenCalled();
  });

  it('should handle multiple listeners for same event', () => {
    const handler1 = vi.fn();
    const handler2 = vi.fn();
    adapter.on('play', handler1);
    adapter.on('play', handler2);

    stateChangeCallback({ data: (window as any).YT.PlayerState.PLAYING });

    expect(handler1).toHaveBeenCalled();
    expect(handler2).toHaveBeenCalled();
  });

  // ===== Polling Tests =====

  it('should start polling when PLAYING event received', () => {
    const timeupdateHandler = vi.fn();
    adapter.on('timeupdate', timeupdateHandler);

    // Trigger play
    stateChangeCallback({ data: (window as any).YT.PlayerState.PLAYING });

    // Initial timeupdate on play, then poll after 5s
    expect(timeupdateHandler).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(5000);
    expect(timeupdateHandler).toHaveBeenCalledTimes(2);

    vi.advanceTimersByTime(5000);
    expect(timeupdateHandler).toHaveBeenCalledTimes(3);
  });

  it('should stop polling when PAUSED event received', () => {
    const timeupdateHandler = vi.fn();
    adapter.on('timeupdate', timeupdateHandler);

    stateChangeCallback({ data: (window as any).YT.PlayerState.PLAYING });
    expect(timeupdateHandler).toHaveBeenCalledTimes(1);

    stateChangeCallback({ data: (window as any).YT.PlayerState.PAUSED });
    vi.advanceTimersByTime(5000);

    // Should not increase after pause
    expect(timeupdateHandler).toHaveBeenCalledTimes(1);
  });

  it('should stop polling when ENDED event received', () => {
    const timeupdateHandler = vi.fn();
    adapter.on('timeupdate', timeupdateHandler);

    stateChangeCallback({ data: (window as any).YT.PlayerState.PLAYING });
    stateChangeCallback({ data: (window as any).YT.PlayerState.ENDED });

    vi.advanceTimersByTime(5000);
    expect(timeupdateHandler).toHaveBeenCalledTimes(1);
  });

  it('should not double-start polling', () => {
    const timeupdateHandler = vi.fn();
    adapter.on('timeupdate', timeupdateHandler);

    // Trigger play twice
    stateChangeCallback({ data: (window as any).YT.PlayerState.PLAYING });
    stateChangeCallback({ data: (window as any).YT.PlayerState.PLAYING });

    expect(timeupdateHandler).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(5000);
    expect(timeupdateHandler).toHaveBeenCalledTimes(2); // Only one interval running
  });

  // ===== sendBeacon Tests =====

  it('should call navigator.sendBeacon with correct payload', async () => {
    (window as any).CURRENT_ASSIGNMENT_ID = 'assign-123';

    await adapter.sendBeacon(150, '2026-07-10T14:30:00Z');

    expect(navigator.sendBeacon).toHaveBeenCalledWith(
      '/api/assignments/assign-123/progress',
      expect.any(FormData)
    );
  });

  it('should gracefully handle missing sendBeacon', async () => {
    const oldSendBeacon = navigator.sendBeacon;
    (navigator.sendBeacon as any) = null;

    const consoleSpy = vi.spyOn(console, 'warn');
    await adapter.sendBeacon(150, '2026-07-10T14:30:00Z');

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('navigator.sendBeacon not supported')
    );

    navigator.sendBeacon = oldSendBeacon;
    consoleSpy.mockRestore();
  });

  it('should log warning if sendBeacon returns false', async () => {
    (navigator.sendBeacon as any).mockReturnValue(false);
    (window as any).CURRENT_ASSIGNMENT_ID = 'assign-123';

    const consoleSpy = vi.spyOn(console, 'warn');
    await adapter.sendBeacon(150, '2026-07-10T14:30:00Z');

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('sendBeacon returned false')
    );

    consoleSpy.mockRestore();
  });

  it('should handle sendBeacon errors gracefully', async () => {
    (navigator.sendBeacon as any).mockImplementation(() => {
      throw new Error('sendBeacon failed');
    });
    (window as any).CURRENT_ASSIGNMENT_ID = 'assign-123';

    const consoleSpy = vi.spyOn(console, 'error');
    await adapter.sendBeacon(150, '2026-07-10T14:30:00Z');

    expect(consoleSpy).toHaveBeenCalledWith(
      'YouTubeAdapter: sendBeacon error:',
      expect.any(Error)
    );

    consoleSpy.mockRestore();
  });

  // ===== Error Handling Tests =====

  it('should catch and log errors in event handlers', () => {
    const throwingHandler = vi.fn(() => {
      throw new Error('Handler error');
    });
    adapter.on('play', throwingHandler);

    const consoleSpy = vi.spyOn(console, 'error');
    stateChangeCallback({ data: (window as any).YT.PlayerState.PLAYING });

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('Error in play handler'),
      expect.any(Error)
    );

    consoleSpy.mockRestore();
  });

  it('should clean up timers on destroy', () => {
    const timeupdateHandler = vi.fn();
    adapter.on('timeupdate', timeupdateHandler);

    stateChangeCallback({ data: (window as any).YT.PlayerState.PLAYING });
    expect(timeupdateHandler).toHaveBeenCalledTimes(1);

    adapter.destroy();
    vi.advanceTimersByTime(5000);

    // No more updates after destroy
    expect(timeupdateHandler).toHaveBeenCalledTimes(1);
  });

  it('should clear event handlers on destroy', () => {
    const playHandler = vi.fn();
    adapter.on('play', playHandler);

    adapter.destroy();
    stateChangeCallback({ data: (window as any).YT.PlayerState.PLAYING });

    expect(playHandler).not.toHaveBeenCalled();
  });
});
