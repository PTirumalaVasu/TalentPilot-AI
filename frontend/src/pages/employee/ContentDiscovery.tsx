import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { AssignmentCard } from '@/components/AssignmentCard';
import { VideoPlayer } from '@/components/VideoPlayer';
import { useAuth } from '@/lib/auth/AuthContext';
import { getMe, logout, type MeResponse } from '@/lib/api/authApi';
import { listMyAssignments } from '@/lib/api/assignmentsApi';
import type { AssignmentContentItem, MyAssignmentsResponse } from '@/types/assignments';

const POLL_INTERVAL_MS = 30000;

type LoadState =
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'loaded'; data: MyAssignmentsResponse };

type ProfileState =
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'loaded'; data: MeResponse };

interface PlayingVideo {
  assignmentId: string;
  videoUrl: string;
  startSeconds: number;
  videoTitle?: string;
  skillName?: string;
}

interface UserMenuButtonProps {
  profile: ProfileState;
  open: boolean;
  onToggle: () => void;
  onSignOut: () => void;
}

// Shared by both header variants below (idle grid and inline video player) so
// the logged-in employee's own name/initial is resolved from GET /api/auth/me
// in exactly one place, rather than each header copy hardcoding a placeholder
// identity (the bug this fixes -- every employee's header used to read "Casey").
function UserMenuButton({ profile, open, onToggle, onSignOut }: UserMenuButtonProps) {
  const firstName = profile.status === 'loaded' ? profile.data.name.split(' ')[0] : '';
  const initial = profile.status === 'loaded' ? profile.data.name.charAt(0).toUpperCase() : '';

  return (
    <div className="relative">
      <button onClick={onToggle} className="flex items-center gap-2 text-sm text-gray-700">
        <span className="w-8 h-8 rounded-full bg-talentpilot-100 flex items-center justify-center text-talentpilot-700 font-medium">
          {initial}
        </span>
        {firstName}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
          <button
            onClick={onSignOut}
            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg"
          >
            Sign Out
          </button>
        </div>
      )}
    </div>
  );
}

export function ContentDiscovery() {
  const { signOut } = useAuth();
  const navigate = useNavigate();
  const [state, setState] = useState<LoadState>({ status: 'loading' });
  const [profile, setProfile] = useState<ProfileState>({ status: 'loading' });
  const [playingVideo, setPlayingVideo] = useState<PlayingVideo | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const pollIntervalRef = useRef<number | null>(null);
  const isPollingRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    setState({ status: 'loading' });
    listMyAssignments()
      .then((data) => {
        if (!cancelled) setState({ status: 'loaded', data });
      })
      .catch(() => {
        if (!cancelled) setState({ status: 'error' });
      });
    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  useEffect(() => {
    let cancelled = false;
    setProfile({ status: 'loading' });
    getMe()
      .then((data) => {
        if (!cancelled) setProfile({ status: 'loaded', data });
      })
      .catch(() => {
        if (!cancelled) setProfile({ status: 'error' });
      });
    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  useEffect(() => {
    function startPolling() {
      if (pollIntervalRef.current !== null) {
        return;
      }
      console.log(`🔄 Starting employee dashboard polling every ${POLL_INTERVAL_MS / 1000} seconds`);
      pollIntervalRef.current = window.setInterval(pollAssignments, POLL_INTERVAL_MS) as unknown as number;
    }

    function stopPolling() {
      if (pollIntervalRef.current === null) {
        return;
      }
      window.clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }

    async function pollAssignments() {
      if (isPollingRef.current) {
        return;
      }
      isPollingRef.current = true;
      try {
        const data = await listMyAssignments();
        const timestamp = new Date().toLocaleTimeString();
        console.log(`[${timestamp}] Assignments poll successful, fetched ${data.assignments.length} assignments`);
        data.assignments.forEach((assignment) => {
          console.log(`  - ${assignment.skill_name}: ${assignment.status} (${assignment.status_percentage}%)`);
        });
        setState((prev) => {
          if (prev.status === 'loaded') {
            return { status: 'loaded', data };
          }
          return prev;
        });
      } catch (err) {
        console.warn("Assignment poll failed, will retry on next interval", err);
      } finally {
        isPollingRef.current = false;
      }
    }

    function handleVisibilityChange() {
      if (document.visibilityState === "hidden") {
        stopPolling();
      } else {
        startPolling();
      }
    }

    if (document.visibilityState !== "hidden") {
      startPolling();
    }
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      stopPolling();
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  async function handleSignOut() {
    try {
      await logout();
    } catch {
      // Best-effort server-side revocation
    } finally {
      signOut();
      navigate('/login', { replace: true });
    }
  }

  function handleSelect(item: AssignmentContentItem) {
    if (!item.content) return;
    setPlayingVideo({
      assignmentId: item.assignment_id,
      videoUrl: item.content.url,
      startSeconds: item.watch_position,
      videoTitle: item.content.title,
      skillName: item.skill_name,
    });
  }

  function handleCloseVideo() {
    setPlayingVideo(null);
  }

  function handleRetry() {
    setReloadToken((token) => token + 1);
  }

  // Show video player inline if one is playing
  if (playingVideo) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <span className="font-bold text-lg text-gray-900">TalentPilot-AI</span>
            <nav className="flex gap-6 text-sm">
              <button
                onClick={handleCloseVideo}
                className="text-gray-600 hover:text-gray-900 pb-3 -mb-3 transition-colors"
              >
                Assignments
              </button>
              <span className="text-talentpilot-600 font-medium border-b-2 border-talentpilot-600 pb-3 -mb-3">Continue Watching</span>
            </nav>
          </div>
          <UserMenuButton
            profile={profile}
            open={userMenuOpen}
            onToggle={() => setUserMenuOpen(!userMenuOpen)}
            onSignOut={() => {
              setUserMenuOpen(false);
              handleSignOut();
            }}
          />
        </header>

        <main className="px-6 py-6 max-w-5xl mx-auto">
          <button
            onClick={handleCloseVideo}
            className="mb-4 text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            ← Back to Assignments
          </button>
          <div className="mx-auto max-w-3xl">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">{playingVideo.videoTitle || playingVideo.skillName}</h1>
            <VideoPlayer
              assignmentId={playingVideo.assignmentId}
              videoUrl={playingVideo.videoUrl}
              startSeconds={playingVideo.startSeconds}
            />
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <span className="font-bold text-lg text-gray-900">TalentPilot-AI</span>
          <nav className="flex gap-6 text-sm">
            <span className="text-talentpilot-600 font-medium">Assignments</span>
            <span className="text-gray-400">Continue Watching</span>
          </nav>
        </div>
        <UserMenuButton
          profile={profile}
          open={userMenuOpen}
          onToggle={() => setUserMenuOpen(!userMenuOpen)}
          onSignOut={() => {
            setUserMenuOpen(false);
            handleSignOut();
          }}
        />
      </header>

      <main className="px-6 py-6 max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Assigned Skills</h1>
          <p className="text-sm text-gray-600 mt-2">Select a video to continue watching or start a new one</p>

          {/* Employee Info Card */}
          {state.status === 'loaded' && (
            <div className="bg-gradient-to-r from-blue-50 to-blue-50 rounded-lg px-5 py-4 border border-blue-200 mt-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-gray-600 uppercase tracking-wide mb-1">Name</p>
                  <p className="text-sm font-semibold text-gray-900">
                    {profile.status === 'loaded' ? profile.data.name : '—'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 uppercase tracking-wide mb-1">Role</p>
                  <p className="text-sm font-semibold text-gray-900">Individual Contributor</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 uppercase tracking-wide mb-1">Email</p>
                  <p className="text-sm font-semibold text-gray-900">
                    {profile.status === 'loaded' ? profile.data.email : '—'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 uppercase tracking-wide mb-1">Skills Assigned</p>
                  <p className="text-sm font-semibold text-blue-600">{state.data.total}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {state.status === 'loading' && (
          <div data-testid="content-discovery-loading" className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-40 bg-gray-100 rounded-lg animate-pulse" />
            ))}
          </div>
        )}

        {state.status === 'error' && (
          <div className="text-center py-12 border-2 border-dashed border-red-200 rounded-lg">
            <p className="text-red-700 mb-3">Couldn't load your assignments.</p>
            <Button onClick={handleRetry}>Try again</Button>
          </div>
        )}

        {state.status === 'loaded' && state.data.total === 0 && (
          <div className="text-center py-12 border-2 border-dashed border-gray-200 rounded-lg">
            <p className="text-gray-500">Nothing in progress right now.</p>
            <p className="text-sm text-gray-400 mt-1">View your assignments once one is assigned.</p>
          </div>
        )}

        {state.status === 'loaded' && state.data.total > 0 && (
          <>
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-1 font-medium">Total</p>
                <p className="text-3xl font-bold text-gray-900">{state.data.total}</p>
              </div>
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-1 font-medium">In Progress</p>
                <p className="text-3xl font-bold text-blue-600">{state.data.in_progress_count}</p>
              </div>
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-1 font-medium">To Start</p>
                <p className="text-3xl font-bold text-gray-600">{state.data.to_start_count}</p>
              </div>
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-1 font-medium">Completed</p>
                <p className="text-3xl font-bold text-green-600">{state.data.completed_count}</p>
              </div>
            </div>

            {state.data.in_progress_count > 0 && (
              <section className="mb-8">
                <h2 className="text-lg font-bold text-gray-900 mb-4">
                  In Progress <span className="text-sm text-gray-500">({state.data.in_progress_count})</span>
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {state.data.assignments
                    .filter((item) => item.group === 'IN_PROGRESS')
                    .map((item) => (
                      <AssignmentCard key={item.assignment_id} item={item} onSelect={handleSelect} />
                    ))}
                </div>
              </section>
            )}

            {state.data.to_start_count > 0 && (
              <section className="mb-8">
                <h2 className="text-lg font-bold text-gray-900 mb-4">
                  To Start <span className="text-sm text-gray-500">({state.data.to_start_count})</span>
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {state.data.assignments
                    .filter((item) => item.group === 'TO_START')
                    .map((item) => (
                      <AssignmentCard key={item.assignment_id} item={item} onSelect={handleSelect} />
                    ))}
                </div>
              </section>
            )}

            {state.data.completed_count > 0 && (
              <section>
                <h2 className="text-lg font-bold text-gray-900 mb-4">
                  Completed <span className="text-sm text-gray-500">({state.data.completed_count})</span>
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {state.data.assignments
                    .filter((item) => item.group === 'COMPLETED')
                    .map((item) => (
                      <AssignmentCard key={item.assignment_id} item={item} onSelect={handleSelect} />
                    ))}
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}
