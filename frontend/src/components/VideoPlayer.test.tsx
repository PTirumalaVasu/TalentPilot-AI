import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { VideoPlayer, VIDEO_LOAD_FAILURE_MESSAGE } from '@/components/VideoPlayer';
import { CaptureService } from '@/lib/services/captureService';

/**
 * First test file for VideoPlayer.tsx (Story 4.0, reused as-is by every
 * story since). Story 2.6 AC3: video-load-failure state with retry.
 * Mocks `window.YT` at the same boundary VideoPlayerDemo.test.tsx already
 * established for this repo's YouTube IFrame API tests.
 */
vi.mock('@/lib/services/captureService', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/services/captureService')>();
  return {
    ...actual,
    // Explicit `new`-forwarding wrapper -- a bare `vi.fn(actual.CaptureService)`
    // does not reliably invoke a real ES6 class's [[Construct]] semantics when
    // the outer mock itself is invoked with `new`.
    CaptureService: vi.fn((...args: ConstructorParameters<typeof actual.CaptureService>) => new actual.CaptureService(...args)),
  };
});

describe('VideoPlayer — video load failure (Story 2.6 AC3)', () => {
  afterEach(() => {
    delete (window as any).YT;
    delete (window as any).onYouTubeIframeAPIReady;
    vi.restoreAllMocks();
  });

  function mockYTPlayer(onReadyOrError: 'ready' | 'error', errorCode = 100) {
    const fakePlayer = {
      addEventListener: vi.fn(),
      getCurrentTime: vi.fn(() => 0),
      getDuration: vi.fn(() => 200),
      getPlayerState: vi.fn(() => -1),
    };
    const PlayerCtor = vi.fn().mockImplementation((_el: unknown, opts: any) => {
      queueMicrotask(() => {
        if (onReadyOrError === 'ready') {
          opts.events.onReady({ target: fakePlayer });
        } else {
          opts.events.onError({ data: errorCode });
        }
      });
      return fakePlayer;
    });
    (window as any).YT = { Player: PlayerCtor };
    return PlayerCtor;
  }

  it('renders the literal "video couldn\'t be loaded" copy with a Try again button and role="alert" on onError', async () => {
    mockYTPlayer('error', 100);

    render(<VideoPlayer assignmentId="assign-1" videoUrl="dQw4w9WgXcQ" />);

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(VIDEO_LOAD_FAILURE_MESSAGE);
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('calls the onError prop with an Error on failure', async () => {
    mockYTPlayer('error', 100);
    const onError = vi.fn();

    render(<VideoPlayer assignmentId="assign-1" videoUrl="dQw4w9WgXcQ" onError={onError} />);

    await screen.findByRole('alert');
    expect(onError).toHaveBeenCalledTimes(1);
    expect(onError.mock.calls[0][0]).toBeInstanceOf(Error);
    expect(onError.mock.calls[0][0].message).toMatch(/video not found/i);
  });

  it('clicking Try again clears the error and re-attempts player initialization', async () => {
    const PlayerCtor = mockYTPlayer('error', 100);
    const user = userEvent.setup();

    render(<VideoPlayer assignmentId="assign-1" videoUrl="dQw4w9WgXcQ" />);

    await screen.findByRole('alert');
    expect(PlayerCtor).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole('button', { name: /try again/i }));

    expect(PlayerCtor).toHaveBeenCalledTimes(2);
  });

  it('a second failed retry re-renders the same error+retry state', async () => {
    mockYTPlayer('error', 100);
    const user = userEvent.setup();

    render(<VideoPlayer assignmentId="assign-1" videoUrl="dQw4w9WgXcQ" />);

    await screen.findByRole('alert');
    await user.click(screen.getByRole('button', { name: /try again/i }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(VIDEO_LOAD_FAILURE_MESSAGE);
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('a synchronous construction failure (initPlayer\'s own try/catch) renders the same error+retry UI', async () => {
    (window as any).YT = {
      Player: vi.fn().mockImplementation(() => {
        throw new Error('boom');
      }),
    };

    render(<VideoPlayer assignmentId="assign-1" videoUrl="dQw4w9WgXcQ" />);

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(VIDEO_LOAD_FAILURE_MESSAGE);
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('an adapter/capture-service construction failure (onPlayerReady_Internal\'s own try/catch) renders the same error+retry UI', async () => {
    vi.mocked(CaptureService).mockImplementationOnce(() => {
      throw new Error('capture service boom');
    });
    mockYTPlayer('ready');

    render(<VideoPlayer assignmentId="assign-1" videoUrl="dQw4w9WgXcQ" />);

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(VIDEO_LOAD_FAILURE_MESSAGE);
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('does not render an error/retry UI on a successful load', async () => {
    mockYTPlayer('ready');

    render(<VideoPlayer assignmentId="assign-1" videoUrl="dQw4w9WgXcQ" />);

    await screen.findByText(/capture service active/i);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /try again/i })).not.toBeInTheDocument();
  });
});
