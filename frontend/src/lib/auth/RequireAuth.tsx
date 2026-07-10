import type { ReactElement } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/lib/auth/AuthContext';

/**
 * Route guard mirroring Story 1.6's backend "no flash of protected content"
 * guarantee on the frontend: since auth state is synchronous in-memory
 * (see AuthContext), an unauthenticated visit redirects before the wrapped
 * element ever renders - there is no intermediate render where it's shown.
 */
export function RequireAuth({ children }: { children: ReactElement }) {
  const { auth } = useAuth();
  const location = useLocation();

  if (auth.status !== 'authenticated') {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}
