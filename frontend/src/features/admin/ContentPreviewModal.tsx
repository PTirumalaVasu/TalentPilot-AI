import { useId } from 'react';
import { Dialog } from '@/components/ui/dialog';
import { estimateDaysToComplete } from '@/lib/utils/duration';

export interface ContentPreviewModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  source: string;
  url: string;
  durationHours?: number | null;
}

// Extracts a video id from watch?v=ID, youtu.be/ID, or an already-/embed/ID
// URL -- the same three YouTube URL shapes this codebase already builds/
// consumes elsewhere (content/service.py's own
// `https://www.youtube.com/watch?v={id}` output). Checked against the
// parsed URL's actual hostname, not a substring match against the raw
// string (code review, 2026-09-10) -- a substring match misidentified any
// non-YouTube URL that merely *contained* one of these patterns (e.g. in a
// query parameter) as embeddable, silently embedding an unrelated video
// instead of showing the correct "preview not available" fallback.
function extractYoutubeId(url: string): string | null {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return null;
  }

  const host = parsed.hostname.toLowerCase();
  if (host === 'youtu.be') {
    const id = parsed.pathname.slice(1);
    return id || null;
  }
  if (host === 'youtube.com' || host === 'www.youtube.com' || host === 'm.youtube.com') {
    const watchId = parsed.searchParams.get('v');
    if (watchId) return watchId;
    const embedMatch = /^\/embed\/([\w-]+)/.exec(parsed.pathname);
    return embedMatch ? embedMatch[1] : null;
  }
  return null;
}

/**
 * The UX spec's "Watch Modal" (04.1-skills-content-sourcing.md, watch-modal-*
 * object IDs) -- a minimal, HR-Admin-facing in-app preview for a candidate
 * under review (or an already-approved link, once Story 6.10 wires that up).
 * Deliberately NOT VideoPlayerDemo.tsx/VideoPlayer.tsx: this has no Adapter,
 * no capture/progress-tracking -- those exist only for the Employee-facing
 * watch-and-resume pipeline (Story 4.x), which doesn't apply to previewing
 * an unapproved candidate. Closing unmounts the iframe entirely (not just
 * hides it), per the UX spec's "stops any playback" requirement.
 */
export function ContentPreviewModal({
  open,
  onClose,
  title,
  source,
  url,
  durationHours = null,
}: ContentPreviewModalProps) {
  const titleId = useId();
  if (!open) return null;

  const youtubeId = extractYoutubeId(url);
  const days = estimateDaysToComplete(durationHours ?? null);

  return (
    <Dialog open={open} onClose={onClose} titleId={titleId} className="max-w-2xl">
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h2 id={titleId} className="text-lg font-bold text-gray-900" data-testid="watch-modal-title">
              {title}
            </h2>
            <p className="text-xs text-gray-500" data-testid="watch-modal-meta">
              {source}
              {durationHours != null ? ` · ${durationHours}h` : ''}
              {days != null ? ` · ≈ ${days} day${days === 1 ? '' : 's'} to complete (at 5 hrs/day)` : ''}
            </p>
          </div>
          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            data-testid="watch-modal-btn-close"
          >
            ✕
          </button>
        </div>

        <div
          className="flex aspect-video items-center justify-center rounded-md bg-gray-100"
          data-testid="watch-modal-body"
        >
          {youtubeId ? (
            <iframe
              title={title}
              src={`https://www.youtube.com/embed/${youtubeId}`}
              className="h-full w-full rounded-md"
              allowFullScreen
            />
          ) : (
            <div className="p-6 text-center text-sm text-gray-600">
              <p>
                Preview not available for {source} in this prototype. Use &quot;Open in new tab&quot; below to
                watch.
              </p>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between border-t border-gray-100 pt-4">
          <a
            href={url}
            target="_blank"
            rel="noreferrer"
            className="text-sm font-medium text-blue-600 hover:underline"
            data-testid="watch-modal-open-external"
          >
            Open in new tab ↗
          </a>
          <button type="button" className="text-sm font-medium text-gray-600 hover:underline" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </Dialog>
  );
}
