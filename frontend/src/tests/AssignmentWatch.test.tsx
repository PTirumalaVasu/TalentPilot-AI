import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AssignmentWatch } from '@/pages/employee/AssignmentWatch';

const navigateMock = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateMock };
});

vi.mock('@/components/VideoPlayer', () => ({
  VideoPlayer: ({ assignmentId, videoUrl, startSeconds }: { assignmentId: string; videoUrl: string; startSeconds: number }) => (
    <div data-testid="video-player-stub">
      {assignmentId} / {videoUrl} / {startSeconds}
    </div>
  ),
}));

function renderAt(path: string, state?: unknown) {
  return render(
    <MemoryRouter initialEntries={[{ pathname: path, state }]}>
      <Routes>
        <Route path="/assignments/:assignmentId/watch" element={<AssignmentWatch />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('AssignmentWatch', () => {
  it('mounts VideoPlayer with the assignmentId, videoUrl, and startSeconds from router state', () => {
    renderAt('/assignments/a1/watch', { videoUrl: 'https://www.youtube.com/watch?v=abc123', startSeconds: 300 });

    expect(screen.getByTestId('video-player-stub')).toHaveTextContent(
      'a1 / https://www.youtube.com/watch?v=abc123 / 300'
    );
  });

  it('redirects to /employee/content when router state is missing (direct navigation/refresh)', () => {
    renderAt('/assignments/a1/watch', undefined);

    expect(navigateMock).toHaveBeenCalledWith('/employee/content', { replace: true });
    expect(screen.queryByTestId('video-player-stub')).not.toBeInTheDocument();
  });
});
