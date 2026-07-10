# Player Adapter Pattern (AD-9)

## Overview

The **PlayerAdapter** is a normalized abstraction over different video player providers (YouTube, Vimeo, etc.). It decouples the watch-progress capture pipeline from provider-specific APIs, enabling future support for additional video sources without changing the capture service code.

## Interface

```typescript
export type PlayerEventType = 'play' | 'pause' | 'ended' | 'timeupdate';

export interface PlayerAdapter {
  position(): number;
  duration(): number;
  on(event: PlayerEventType, handler: () => void): void;
  sendBeacon(position: number, eventTime: string): Promise<void>;
}
```

### Methods

#### `position(): number`
Returns the current playback position in seconds (floored to integer).
- Safe to call at any time
- Returns 0 if not initialized or video hasn't started
- Underlying implementation may use polling or queries (caller doesn't care)

#### `duration(): number`
Returns the total video duration in seconds (floored to integer).
- Returns 0 if metadata not yet loaded
- Call after 'play' event for reliable result

#### `on(event: PlayerEventType, handler: () => void): void`
Register listener for player state events.
- **'play'**: Playback started (user pressed play or autoplay triggered)
- **'pause'**: Playback paused
- **'ended'**: Reached end of video
- **'timeupdate'**: Periodic position update (polling-based or event-driven)

Multiple handlers for the same event are supported; handlers are called in registration order.

#### `sendBeacon(position: number, eventTime: string): Promise<void>`
Flush current position to server using best-effort delivery.
- Uses `navigator.sendBeacon()` API (doesn't block unload)
- Called on tab close, visibility change, or before unload
- Returns Promise that resolves after beacon call (not guaranteed delivery)
- Gracefully degrades if `navigator.sendBeacon()` not available

## YouTube Adapter Implementation

The **YouTubeAdapter** is the current production implementation.

### Polling-Based Approach

YouTube's IFrame API does not emit periodic position-change events like Vimeo does. Instead, we poll:

```typescript
// Sample every 5-10 seconds during playback
const pollFrequency = 7500; // ms

// On 'PLAYING' state, start interval polling
setInterval(() => {
  emit('timeupdate'); // Caller uses adapter.position() to get current value
}, pollFrequency);

// On 'PAUSED' or 'ENDED' state, stop polling
clearInterval(pollingInterval);
```

### State Change Listening

```typescript
player.addEventListener('onStateChange', (event) => {
  const state = event.data;
  if (state === YT.PlayerState.PLAYING) {
    startPolling();
    emit('play');
  } else if (state === YT.PlayerState.PAUSED) {
    stopPolling();
    emit('pause');
  } else if (state === YT.PlayerState.ENDED) {
    stopPolling();
    emit('ended');
  }
});
```

### Trade-offs

| Approach | YouTube | Vimeo |
| --- | --- | --- |
| **Event-Driven** | Limited (only state changes) | ✓ Rich (timeupdate, seeked, etc.) |
| **Polling** | ✓ Works | Inefficient (unnecessary when paused) |
| **Chosen for MVP** | Polling + state events | To be determined |

**Why Polling for YouTube?**
- YouTube's state-only events don't provide continuous position updates
- Polling every 5-10s is a reasonable compromise
- Caller doesn't care about implementation; `CaptureService` treats all events uniformly

## Implementing a New Adapter (Vimeo Example)

To add Vimeo support, create a new adapter class implementing the same interface:

```typescript
// frontend/src/lib/adapters/vimeoAdapter.ts

import type { PlayerAdapter, PlayerEventType } from './playerAdapter';

export class VimeoAdapter implements PlayerAdapter {
  private player: any;
  private eventHandlers: { [key: string]: (() => void)[] } = {};

  constructor(iframeElement: HTMLIFrameElement) {
    // Initialize Vimeo Player instance
    this.player = new Vimeo.Player(iframeElement);
    this.setupEventListeners();
  }

  private setupEventListeners(): void {
    // Vimeo has rich event-driven API
    this.player.on('play', () => this.emit('play'));
    this.player.on('pause', () => this.emit('pause'));
    this.player.on('ended', () => this.emit('ended'));

    // Vimeo emits 'timeupdate' with exact position (no polling needed!)
    this.player.on('timeupdate', ({ seconds }) => {
      this.lastKnownPosition = seconds;
      this.emit('timeupdate');
    });
  }

  position(): number {
    return Math.floor(this.lastKnownPosition);
  }

  duration(): number {
    // Vimeo provides this synchronously
    return Math.floor(this.player.getDuration());
  }

  on(event: PlayerEventType, handler: () => void): void {
    if (!this.eventHandlers[event]) {
      this.eventHandlers[event] = [];
    }
    this.eventHandlers[event].push(handler);
  }

  async sendBeacon(position: number, eventTime: string): Promise<void> {
    // Same as YouTube: use navigator.sendBeacon()
    if (!navigator.sendBeacon) return;
    const payload = new FormData();
    payload.append('watch_position', String(position));
    payload.append('event_time', eventTime);
    navigator.sendBeacon(`/api/assignments/${ASSIGNMENT_ID}/progress`, payload);
  }

  private emit(event: PlayerEventType): void {
    const handlers = this.eventHandlers[event] || [];
    handlers.forEach((h) => h());
  }
}
```

Usage:

```typescript
// frontend/src/components/VideoPlayer.tsx

// Instead of:
const adapter = new YouTubeAdapter(player);

// Use Vimeo:
const adapter = new VimeoAdapter(iframeElement);

// CaptureService works unchanged
const capture = new CaptureService(adapter, config);
```

## Usage in React

```typescript
import { VideoPlayer } from '@/components/VideoPlayer';

export function MyPage() {
  return (
    <VideoPlayer
      assignmentId="assign-123"
      videoUrl="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
      startSeconds={45} // Resume at 45 seconds
      onPlayerReady={(adapter) => console.log('Ready', adapter)}
      onError={(err) => console.error('Error', err)}
    />
  );
}
```

## CaptureService Integration

The `CaptureService` listens to adapter events and manages batching/posting:

```typescript
const adapter = new YouTubeAdapter(player);
const capture = new CaptureService(adapter, {
  assignmentId: 'assign-123',
  videoUrl: 'https://...',
  postIntervalMs: 12000, // Post every 12s
  queueThreshold: 3, // Or when 3+ samples queued
});

// Listen to adapter events automatically
adapter.on('timeupdate', () => {
  // CaptureService queues sample
  // Posts on interval or threshold
});

// On tab close, flush via beacon
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    capture.flushViaBeacon();
  }
});
```

## Testing

Unit tests mock the underlying player API entirely:

```typescript
// Mock YouTube API
const mockPlayer = {
  getCurrentTime: vi.fn(() => 45.5),
  getDuration: vi.fn(() => 300),
  addEventListener: vi.fn(),
};

// Test adapter in isolation
const adapter = new YouTubeAdapter(mockPlayer);
expect(adapter.position()).toBe(45);
expect(adapter.duration()).toBe(300);
```

Integration tests use a real iframe against a fake backend.

## Architecture Notes

- **Single responsibility**: Adapter abstracts player; CaptureService handles batching/posting
- **No state coupling**: Each adapter instance is independent (one per video playback session)
- **Graceful degradation**: `sendBeacon()` logs warning if unsupported, doesn't error
- **Event ordering**: All adapters emit events in the same order (play → timeupdate → pause → ended)

---

**Story 4.0**: YouTube IFrame Adapter — Abstraction Layer for Player Events
