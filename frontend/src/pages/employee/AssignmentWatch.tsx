import { useEffect } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { VideoPlayer } from '@/components/VideoPlayer';

interface WatchRouteState {
  videoUrl: string;
  startSeconds: number;
}

function isWatchRouteState(value: unknown): value is WatchRouteState {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as WatchRouteState).videoUrl === 'string' &&
    typeof (value as WatchRouteState).startSeconds === 'number'
  );
}

/**
 * Thin wrapper mounting the existing <VideoPlayer> (Story 4.0) at
 * /assignments/:assignmentId/watch. Only ever reachable via a Content
 * Discovery card click, which passes videoUrl/startSeconds via router state
 * (Story 2.5, Scope Note 7 -- no second fetch for the resume position).
 * Direct navigation/refresh has no state to render from, so redirect back
 * rather than mount <VideoPlayer> with an undefined videoUrl.
 */
export function AssignmentWatch() {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state;

  useEffect(() => {
    if (!isWatchRouteState(state)) {
      navigate('/employee/content', { replace: true });
    }
  }, [state, navigate]);

  if (!isWatchRouteState(state) || !assignmentId) {
    return null;
  }

  return (
    <div className="mx-auto max-w-3xl p-8">
      <VideoPlayer
        assignmentId={assignmentId}
        videoUrl={state.videoUrl}
        startSeconds={state.startSeconds}
      />
    </div>
  );
}
