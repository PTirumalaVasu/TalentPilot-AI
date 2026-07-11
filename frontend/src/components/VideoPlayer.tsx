/**
 * VideoPlayer Component — Wraps YouTube IFrame and initializes adapter + capture service
 * Handles resume playback (startSeconds), tab-close flushing, and cleanup
 */

import React, { useEffect, useRef, useState } from 'react';
import { YouTubeAdapter } from '../lib/adapters/youtubeAdapter';
import { CaptureService } from '../lib/services/captureService';

export interface VideoPlayerProps {
  assignmentId: string;
  videoUrl: string; // YouTube video URL or ID
  startSeconds?: number; // Resume position (in seconds, will be floored to nearest second)
  onPlayerReady?: (adapter: YouTubeAdapter) => void;
  onError?: (err: Error) => void;
}

// User-facing copy for a failed video load (Story 2.6 AC3). Exported so the
// test file asserts against this constant instead of a second hardcoded
// copy of the string that could silently drift out of sync.
export const VIDEO_LOAD_FAILURE_MESSAGE = "This video couldn't be loaded.";

/**
 * Extract YouTube video ID from URL or accept raw ID
 */
function extractYouTubeId(urlOrId: string): string {
  // Handle full URLs: https://www.youtube.com/watch?v=dQw4w9WgXcQ
  const urlMatch = urlOrId.match(
    /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/
  );
  if (urlMatch) return urlMatch[1];

  // Handle short URLs or raw IDs
  return urlOrId;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  assignmentId,
  videoUrl,
  startSeconds = 0,
  onPlayerReady,
  onError,
}) => {
  // Stable outer container, always owned by React -- never passed directly
  // to YT.Player (see initPlayer). YouTube's IFrame API replaces whatever
  // element it's given with a generated <iframe>, so reusing the same node
  // across retry attempts would mean attaching a new player into an
  // already-detached element (Story 2.6 review finding). Each attempt
  // instead gets a fresh child element appended into this stable container
  // -- the same DOM-recreation approach VideoPlayerDemo.tsx's loadPlayer()
  // already uses (that component does not call .destroy() on the raw
  // player object, so it is precedent for the DOM handling only, not for
  // handleRetry's player teardown below).
  const containerRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<any>(null);
  const adapterRef = useRef<YouTubeAdapter | null>(null);
  const captureServiceRef = useRef<CaptureService | null>(null);
  const [isReady, setIsReady] = useState(false);
  // Holds the raw diagnostic message (e.g. "Video not found (removed or
  // private)") for console logging only -- the UI always shows the literal
  // VIDEO_LOAD_FAILURE_MESSAGE below, never this string (Story 2.6).
  const [error, setError] = useState<string | null>(null);

  const cleanupListenersRef = useRef<(() => void) | null>(null);
  // Bumped on every initPlayer() call (first load + every retry). Captured
  // by each attempt's onReady/onError closures so a stale callback from an
  // attempt superseded by a later retry can't overwrite newer state
  // (Story 2.6 review finding).
  const attemptIdRef = useRef(0);
  const isMountedRef = useRef(true);

  // Destroys and nulls out every player/adapter/capture-service/listener
  // ref, each independently exception-safe so one throwing .destroy() call
  // doesn't block the rest. Used on both unmount and retry -- nulling (not
  // just destroying) is critical: React StrictMode's dev-mode mount ->
  // unmount -> remount cycle re-runs initPlayer(), whose own guard
  // (`if (playerRef.current) return`) would otherwise see a stale
  // already-destroyed player and silently no-op, permanently killing the
  // capture pipeline while the UI keeps claiming it's active (Story 2.6
  // round-2 review, reproduced empirically under StrictMode).
  const destroyPlayerResources = () => {
    if (cleanupListenersRef.current) {
      try {
        cleanupListenersRef.current();
      } catch (err) {
        console.error('[VideoPlayer] Error removing listeners during teardown:', err);
      }
      cleanupListenersRef.current = null;
    }
    if (captureServiceRef.current) {
      try {
        captureServiceRef.current.destroy();
      } catch (err) {
        console.error('[VideoPlayer] Error destroying capture service:', err);
      }
      captureServiceRef.current = null;
    }
    if (adapterRef.current) {
      try {
        adapterRef.current.destroy();
      } catch (err) {
        console.error('[VideoPlayer] Error destroying adapter:', err);
      }
      adapterRef.current = null;
    }
    if (playerRef.current && typeof playerRef.current.destroy === 'function') {
      try {
        playerRef.current.destroy();
      } catch (err) {
        console.error('[VideoPlayer] Error destroying player:', err);
      }
    }
    playerRef.current = null;
  };

  useEffect(() => {
    isMountedRef.current = true;

    // Load YouTube IFrame API if not already loaded
    if (!window.YT) {
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      tag.async = true;

      window.onYouTubeIframeAPIReady = initPlayer;

      document.body.appendChild(tag);
    } else {
      initPlayer();
    }

    return () => {
      isMountedRef.current = false;
      destroyPlayerResources();
    };
  }, []);

  const initPlayer = () => {
    if (!containerRef.current || playerRef.current) return;

    const myAttempt = ++attemptIdRef.current;

    // Fresh mount target for every attempt -- see containerRef's comment.
    // The id includes the attempt number so it stays unique across
    // retries, not just accidentally non-colliding via execution order.
    containerRef.current.innerHTML = '';
    const playerHost = document.createElement('div');
    playerHost.id = `youtube-player-${assignmentId}-${myAttempt}`;
    containerRef.current.appendChild(playerHost);

    const videoId = extractYouTubeId(videoUrl);

    try {
      playerRef.current = new window.YT.Player(playerHost, {
        width: '100%',
        height: 400,
        videoId,
        playerVars: {
          autoplay: 0,
          controls: 1,
          fs: 1,
          modestbranding: 1,
          rel: 0,
          start: Math.floor(startSeconds),
        },
        events: {
          onReady: () => onPlayerReady_Internal(myAttempt),
          onError: (event: any) => onPlayerError_Internal(event, myAttempt),
        },
      });
    } catch (err) {
      if (!isMountedRef.current || myAttempt !== attemptIdRef.current) return;
      const errMsg = err instanceof Error ? err.message : String(err);
      console.error(`[VideoPlayer] Failed to initialize player: ${errMsg}`);
      setError(errMsg);
      onError?.(new Error(errMsg));
    }
  };

  // Resets all player/adapter/capture-service state and re-attempts
  // initialization from scratch (Story 2.6 AC3).
  const handleRetry = () => {
    if (!isMountedRef.current) return;
    destroyPlayerResources();
    setIsReady(false);
    setError(null);
    initPlayer();
  };

  const onPlayerReady_Internal = (myAttempt: number) => {
    if (!isMountedRef.current || myAttempt !== attemptIdRef.current) return;
    try {
      // Create adapter
      adapterRef.current = new YouTubeAdapter(playerRef.current, 7500);

      // Create capture service
      captureServiceRef.current = new CaptureService(adapterRef.current, {
        assignmentId,
        videoUrl,
        postIntervalMs: 12000,
        queueThreshold: 3,
      });

      // Setup visibility change listener for tab-close flush
      const handleVisibilityChange = () => {
        if (document.hidden && captureServiceRef.current) {
          captureServiceRef.current.flushViaBeacon();
        }
      };

      const handleBeforeUnload = () => {
        if (captureServiceRef.current) {
          captureServiceRef.current.flushViaBeacon();
        }
      };

      document.addEventListener('visibilitychange', handleVisibilityChange);
      window.addEventListener('beforeunload', handleBeforeUnload);

      // Assigned before onPlayerReady?.() below, which may throw --
      // otherwise these listeners would already be live with no recorded
      // way to remove them (Story 2.6 review, fixed as a byproduct of the
      // attempt-token restructuring).
      cleanupListenersRef.current = () => {
        document.removeEventListener('visibilitychange', handleVisibilityChange);
        window.removeEventListener('beforeunload', handleBeforeUnload);
      };

      setIsReady(true);
      onPlayerReady?.(adapterRef.current);

      // Store globally for sendBeacon endpoint (per-instance safe via assignment ID)
      (window as any).CURRENT_ASSIGNMENT_ID = assignmentId;
    } catch (err) {
      if (!isMountedRef.current || myAttempt !== attemptIdRef.current) return;
      const errMsg = err instanceof Error ? err.message : String(err);
      console.error(`[VideoPlayer] Failed to initialize adapter: ${errMsg}`);
      setError(errMsg);
      onError?.(new Error(errMsg));
    }
  };

  const onPlayerError_Internal = (event: any, myAttempt: number) => {
    if (!isMountedRef.current || myAttempt !== attemptIdRef.current) return;
    let errMsg = 'Unknown player error';
    if (event.data === 2) errMsg = 'Invalid parameter';
    else if (event.data === 5) errMsg = 'HTML5 player error';
    else if (event.data === 100) errMsg = 'Video not found (removed or private)';
    else if (event.data === 101 || event.data === 150)
      errMsg = 'Video cannot be played embedded';

    console.error(`[VideoPlayer] Player error: ${errMsg}`);
    setError(errMsg);
    onError?.(new Error(errMsg));
  };

  return (
    <div className="video-player-container" style={{ marginBottom: '1rem' }}>
      {error && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '0.75rem',
            color: '#d32f2f',
            padding: '0.5rem',
            marginBottom: '0.5rem',
            border: '1px solid #d32f2f',
            borderRadius: '4px',
          }}
        >
          <p role="alert" style={{ margin: 0 }}>
            ⚠️ {VIDEO_LOAD_FAILURE_MESSAGE}
          </p>
          <button
            type="button"
            onClick={handleRetry}
            style={{
              color: '#d32f2f',
              border: '1px solid #d32f2f',
              borderRadius: '4px',
              background: 'transparent',
              padding: '0.25rem 0.75rem',
              cursor: 'pointer',
              flexShrink: 0,
            }}
          >
            Try again
          </button>
        </div>
      )}

      <div
        ref={containerRef}
        style={{
          minHeight: '400px',
          backgroundColor: '#000',
          borderRadius: '4px',
        }}
      />

      {!isReady && !error && (
        <p style={{ marginTop: '0.5rem', color: '#666' }}>Loading player...</p>
      )}

      {isReady && !error && (
        <p style={{ marginTop: '0.5rem', color: '#666', fontSize: '0.875rem' }}>
          ✓ Capture service active (posting every 12s or on 3+ samples)
        </p>
      )}
    </div>
  );
};
