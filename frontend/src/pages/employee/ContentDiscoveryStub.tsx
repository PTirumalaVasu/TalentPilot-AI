import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth/AuthContext';
import { logout } from '@/lib/api/authApi';

export function ContentDiscoveryStub() {
  const { signOut } = useAuth();
  const navigate = useNavigate();

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

  return (
    <div className="mx-auto max-w-2xl p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Content Discovery</h1>
        <Button variant="outline" onClick={handleSignOut}>
          Sign Out
        </Button>
      </div>
      <p className="text-slate-500">
        Coming in Epic 2 (Content Discovery, Story 2.5). This is a placeholder landing page for
        the EMPLOYEE role, built by Story 1.8 so the login flow has somewhere real to redirect to.
      </p>
    </div>
  );
}
