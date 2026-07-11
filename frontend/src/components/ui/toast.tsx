import * as React from 'react';
import { cn } from '@/lib/utils';

export interface ToastProps {
  /** Rendered when non-null; auto-dismisses via `onDismiss` after `durationMs`. */
  message: string | null;
  onDismiss: () => void;
  durationMs?: number;
  className?: string;
}

const DEFAULT_DURATION_MS = 4000;

/**
 * Hand-rolled toast primitive (Story 3.5, first in the repo) — no new
 * dependency, per Story 1.8/3.4's established pattern. `role="status"` +
 * `aria-live="polite"` so the success message is announced to assistive
 * tech, not just visually rendered (NFR-A4).
 */
export function Toast({ message, onDismiss, durationMs = DEFAULT_DURATION_MS, className }: ToastProps) {
  // Same rationale as Dialog's onCloseRef: keeps the effect's dependency
  // array free of an unstable callback identity, so it only re-runs when
  // `message`/`durationMs` actually change, not on every parent re-render.
  const onDismissRef = React.useRef(onDismiss);
  onDismissRef.current = onDismiss;

  React.useEffect(() => {
    if (!message) return;
    const timer = window.setTimeout(() => onDismissRef.current(), durationMs);
    return () => window.clearTimeout(timer);
  }, [message, durationMs]);

  if (!message) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        'fixed inset-x-0 bottom-6 z-50 mx-auto w-fit max-w-[90vw] rounded-lg bg-gray-900 px-4 py-2 text-sm text-white shadow-lg',
        className
      )}
    >
      {message}
    </div>
  );
}
