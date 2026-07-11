import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { AssignmentCard } from '@/components/AssignmentCard';
import { useAuth } from '@/lib/auth/AuthContext';
import { logout } from '@/lib/api/authApi';
import { listMyAssignments } from '@/lib/api/assignmentsApi';
import type { AssignmentContentItem, MyAssignmentsResponse } from '@/types/assignments';

type LoadState =
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'loaded'; data: MyAssignmentsResponse };

export function ContentDiscovery() {
  const { signOut } = useAuth();
  const navigate = useNavigate();
  const [state, setState] = useState<LoadState>({ status: 'loading' });
  // Bumped by handleRetry to re-trigger the effect below -- keeps the
  // cancelled-on-unmount guard in one place instead of duplicating the
  // fetch/then/catch logic (and its guard) in a second function.
  const [reloadToken, setReloadToken] = useState(0);

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

  async function handleSignOut() {
    try {
      await logout();
    } catch {
      // Best-effort server-side revocation: if the request fails (network
      // error, 5xx), the user's intent to sign out is still honored
      // client-side below, matching AC6's guarantee.
    } finally {
      signOut();
      navigate('/login', { replace: true });
    }
  }

  function handleSelect(item: AssignmentContentItem) {
    if (!item.content) return;
    navigate(`/assignments/${item.assignment_id}/watch`, {
      state: { videoUrl: item.content.url, startSeconds: item.watch_position },
    });
  }

  function handleRetry() {
    setReloadToken((token) => token + 1);
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
        <Button variant="outline" onClick={handleSignOut}>
          Sign Out
        </Button>
      </header>

      <main className="px-6 py-6 max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-1">Assigned Skills</h1>
        <p className="text-sm text-gray-600 mb-6">Select a video to continue watching or start a new one</p>

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
            <div className="grid grid-cols-3 gap-4 mb-6">
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
              <section>
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
          </>
        )}
      </main>
    </div>
  );
}
