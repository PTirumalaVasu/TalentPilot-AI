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
  const iframeRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<any>(null);
  const adapterRef = useRef<YouTubeAdapter | null>(null);
  const captureServiceRef = useRef<CaptureService | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cleanupListenersRef = useRef<(() => void) | null>(null);

  useEffect(() => {
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
      // Cleanup event listeners
      if (cleanupListenersRef.current) {
        cleanupListenersRef.current();
        cleanupListenersRef.current = null;
      }
      // Cleanup services
      if (captureServiceRef.current) {
        captureServiceRef.current.destroy();
      }
      if (adapterRef.current) {
        adapterRef.current.destroy();
      }
    };
  }, []);

  const initPlayer = () => {
    if (!iframeRef.current || playerRef.current) return;

    const videoId = extractYouTubeId(videoUrl);

    try {
      playerRef.current = new window.YT.Player(iframeRef.current, {
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
          onReady: onPlayerReady_Internal,
          onError: onPlayerError_Internal,
        },
      });
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setError(`Failed to initialize player: ${errMsg}`);
      onError?.(new Error(errMsg));
    }
  };

  const onPlayerReady_Internal = () => {
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

      setIsReady(true);
      onPlayerReady?.(adapterRef.current);

      // Store globally for sendBeacon endpoint (per-instance safe via assignment ID)
      (window as any).CURRENT_ASSIGNMENT_ID = assignmentId;

      // Store cleanup function to be called in useEffect cleanup
      cleanupListenersRef.current = () => {
        document.removeEventListener('visibilitychange', handleVisibilityChange);
        window.removeEventListener('beforeunload', handleBeforeUnload);
      };
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setError(`Failed to initialize adapter: ${errMsg}`);
      onError?.(new Error(errMsg));
    }
  };

  const onPlayerError_Internal = (event: any) => {
    let errMsg = 'Unknown player error';
    if (event.data === 2) errMsg = 'Invalid parameter';
    else if (event.data === 5) errMsg = 'HTML5 player error';
    else if (event.data === 100) errMsg = 'Video not found (removed or private)';
    else if (event.data === 101 || event.data === 150)
      errMsg = 'Video cannot be played embedded';

    setError(errMsg);
    onError?.(new Error(errMsg));
  };

  return (
    <div className="video-player-container" style={{ marginBottom: '1rem' }}>
      {error && (
        <div
          style={{
            color: '#d32f2f',
            padding: '0.5rem',
            marginBottom: '0.5rem',
            border: '1px solid #d32f2f',
            borderRadius: '4px',
          }}
        >
          ⚠️ {error}
        </div>
      )}

      <div
        ref={iframeRef}
        id={`youtube-player-${assignmentId}`}
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
