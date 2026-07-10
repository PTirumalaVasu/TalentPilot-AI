import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { setUnauthorizedHandler } from '@/lib/api/client';
import type { Role } from '@/lib/api/authApi';

type AuthState =
  | { status: 'unauthenticated' }
  | { status: 'authenticated'; role: Role; userId: string };

interface AuthContextValue {
  auth: AuthState;
  signIn: (role: Role, userId: string) => void;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * In-memory only, by design (see Story 1.8 Dev Notes "Cookie-based session,
 * not token-in-state"): the HttpOnly cookie the backend sets IS the session.
 * This context exists purely so the frontend can (a) decide the post-login
 * redirect target and (b) react to a 401 arriving at any point, without
 * duplicating the backend's own session/revocation logic client-side.
 *
 * Known, accepted limitation: because there is no `GET /api/auth/me` (or
 * equivalent) endpoint on the backend to silently verify an existing cookie,
 * a hard page refresh always resets this to `unauthenticated` and bounces to
 * `/login`, even if the cookie is technically still valid. No story/AC in
 * this project requires "stay logged in across a refresh" (a persistent
 * session is explicitly out of scope - see Story 1.8 AC7), so this is the
 * safe, honest behavior rather than inventing a fake client-side check.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState<AuthState>({ status: 'unauthenticated' });

  useEffect(() => {
    setUnauthorizedHandler(() => setAuth({ status: 'unauthenticated' }));
    return () => setUnauthorizedHandler(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      auth,
      signIn: (role, userId) => setAuth({ status: 'authenticated', role, userId }),
      signOut: () => setAuth({ status: 'unauthenticated' }),
    }),
    [auth]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
