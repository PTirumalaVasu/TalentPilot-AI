import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { VideoPlayerDemo } from '@/pages/dev/VideoPlayerDemo';

/**
 * Smoke test proving Story 4.0's manual demo still works after being migrated
 * from a standalone index.html into a real route/component (Story 1.8).
 * Stubs `window.YT` so no real network/script-injection happens - same
 * boundary Story 4.0's own tests mocked at.
 */
describe('VideoPlayerDemo (Story 4.0 demo, migrated route)', () => {
  afterEach(() => {
    delete (window as any).YT;
    delete (window as any).onYouTubeIframeAPIReady;
  });

  it('renders the demo controls and default values', () => {
    render(<VideoPlayerDemo />);

    expect(screen.getByRole('heading', { name: /video player/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/youtube video id/i)).toHaveValue('dQw4w9WgXcQ');
    expect(screen.getByLabelText(/resume from/i)).toHaveValue(0);
    expect(screen.getByRole('button', { name: /load video/i })).toBeInTheDocument();
    expect(screen.getByText('Load a video to start the capture service')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /flush samples now/i })).toBeInTheDocument();
  });

  it('initializes the player + capture service on Load Video and starts reporting metrics', async () => {
    const fakePlayer = {
      addEventListener: vi.fn(),
      getCurrentTime: vi.fn(() => 42),
      getDuration: vi.fn(() => 200),
      getPlayerState: vi.fn(() => 1),
    };
    (window as any).YT = {
      Player: vi.fn().mockImplementation((_el: unknown, opts: any) => {
        queueMicrotask(() => opts.events.onReady({ target: fakePlayer }));
        return fakePlayer;
      }),
      PlayerState: { UNSTARTED: -1, ENDED: 0, PLAYING: 1, PAUSED: 2, BUFFERING: 3, CUED: 5 },
    };

    const user = userEvent.setup();
    render(<VideoPlayerDemo />);

    await user.click(screen.getByRole('button', { name: /load video/i }));

    expect(await screen.findByText(/capture service active/i)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('42s')).toBeInTheDocument(), { timeout: 2000 });
    expect(screen.getByText('200s')).toBeInTheDocument();
  });
});
