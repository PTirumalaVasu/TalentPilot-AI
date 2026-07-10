import { useEffect, useRef, useState } from 'react';
import { YouTubeAdapter } from '@/lib/adapters/youtubeAdapter';
import { CaptureService } from '@/lib/services/captureService';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

/**
 * Story 4.0's manual YouTube player + capture-service demo, migrated from the
 * old standalone `index.html` into a real route (Story 1.8) now that the app
 * has a router. Behavior is preserved 1:1 from the original vanilla-JS script:
 * load a video by ID, poll position/duration/progress, manually flush samples.
 */
export function VideoPlayerDemo() {
  const [videoId, setVideoId] = useState('dQw4w9WgXcQ');
  const [resumeAt, setResumeAt] = useState(0);
  const [position, setPosition] = useState(0);
  const [duration, setDuration] = useState(0);
  const [statusText, setStatusText] = useState('Idle');
  const [captureStatus, setCaptureStatus] = useState(
    'Load a video to start the capture service'
  );

  const playerContainerRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<any>(null);
  const adapterRef = useRef<YouTubeAdapter | null>(null);
  const captureRef = useRef<CaptureService | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const listenersRef = useRef<{ visibilitychange: () => void; beforeunload: () => void } | null>(
    null
  );

  function removeCaptureListeners() {
    if (!listenersRef.current) return;
    document.removeEventListener('visibilitychange', listenersRef.current.visibilitychange);
    window.removeEventListener('beforeunload', listenersRef.current.beforeunload);
    listenersRef.current = null;
  }

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      removeCaptureListeners();
      captureRef.current?.destroy();
      adapterRef.current?.destroy();
    };
  }, []);

  function onPlayerReady(player: any) {
    playerRef.current = player;
    adapterRef.current = new YouTubeAdapter(player, 7500);
    captureRef.current = new CaptureService(adapterRef.current, {
      assignmentId: 'demo-assign-001',
      videoUrl: `https://youtube.com/watch?v=${videoId}`,
      postIntervalMs: 12000,
      queueThreshold: 3,
    });

    removeCaptureListeners();
    const handleVisibilityChange = () => {
      if (document.hidden) captureRef.current?.flushViaBeacon();
    };
    const handleBeforeUnload = () => captureRef.current?.flushViaBeacon();
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('beforeunload', handleBeforeUnload);
    listenersRef.current = {
      visibilitychange: handleVisibilityChange,
      beforeunload: handleBeforeUnload,
    };

    setCaptureStatus(
      'Capture service active (polling every 7.5s, posting every 12s or on 3+ samples)'
    );

    if (intervalRef.current) clearInterval(intervalRef.current);
    intervalRef.current = setInterval(() => {
      if (!adapterRef.current) return;
      const pos = adapterRef.current.position();
      const dur = adapterRef.current.duration();
      setPosition(pos);
      setDuration(dur);

      const state = player.getPlayerState?.();
      const states: Record<number, string> = {
        [-1]: 'Unstarted',
        0: 'Ended',
        1: 'Playing',
        2: 'Paused',
        3: 'Buffering',
        5: 'Cued',
      };
      setStatusText(states[state] ?? 'Unknown');
    }, 500);
  }

  function loadPlayer() {
    if (!videoId) return;

    captureRef.current?.destroy();
    adapterRef.current?.destroy();
    if (playerContainerRef.current) playerContainerRef.current.innerHTML = '';

    const iframeHost = document.createElement('div');
    iframeHost.id = 'yt-player-demo';
    playerContainerRef.current?.appendChild(iframeHost);

    const createPlayer = () => {
      new (window as any).YT.Player(iframeHost, {
        width: '100%',
        height: 400,
        videoId,
        playerVars: { autoplay: 0, controls: 1, start: Math.floor(resumeAt) },
        events: { onReady: (e: any) => onPlayerReady(e.target) },
      });
    };

    if (!(window as any).YT) {
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      tag.async = true;
      (window as any).onYouTubeIframeAPIReady = createPlayer;
      document.body.appendChild(tag);
    } else {
      createPlayer();
    }
  }

  async function flushNow() {
    if (!captureRef.current) return;
    await captureRef.current.flush();
  }

  const progressPct = duration > 0 ? Math.round((position / duration) * 100) : 0;

  return (
    <div className="mx-auto max-w-3xl p-8">
      <h1 className="text-2xl font-bold">TalentPilot Video Player (dev demo)</h1>
      <p className="mb-6 text-sm text-slate-500">
        Story 4.0: YouTube IFrame Adapter &amp; Watch Progress Capture
      </p>

      <div className="mb-6 space-y-3">
        <div>
          <Label htmlFor="videoId">YouTube Video ID</Label>
          <Input id="videoId" value={videoId} onChange={(e) => setVideoId(e.target.value)} />
        </div>
        <div>
          <Label htmlFor="resumeAt">Resume From (seconds)</Label>
          <Input
            id="resumeAt"
            type="number"
            min={0}
            value={resumeAt}
            onChange={(e) => setResumeAt(Number(e.target.value) || 0)}
          />
        </div>
        <Button onClick={loadPlayer}>Load Video</Button>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-md border border-slate-200 p-3">
          <div className="text-xs text-slate-500">Current Position</div>
          <div className="text-lg font-semibold">{position}s</div>
        </div>
        <div className="rounded-md border border-slate-200 p-3">
          <div className="text-xs text-slate-500">Duration</div>
          <div className="text-lg font-semibold">{duration}s</div>
        </div>
        <div className="rounded-md border border-slate-200 p-3">
          <div className="text-xs text-slate-500">Progress %</div>
          <div className="text-lg font-semibold">{progressPct}%</div>
        </div>
        <div className="rounded-md border border-slate-200 p-3">
          <div className="text-xs text-slate-500">Status</div>
          <div className="text-lg font-semibold">{statusText}</div>
        </div>
      </div>

      <div ref={playerContainerRef} className="mb-6" />

      <div className="mb-2 rounded-md bg-slate-100 p-3 text-sm">{captureStatus}</div>
      <Button variant="outline" onClick={flushNow}>
        Flush Samples Now
      </Button>
    </div>
  );
}
