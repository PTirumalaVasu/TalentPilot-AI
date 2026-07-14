import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { setUnauthorizedHandler } from '@/lib/api/client';
import { getCurrentUser, type Role } from '@/lib/api/authApi';

type AuthState =
  | { status: 'loading' }
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
 * On mount, `GET /api/auth/me` is used to silently resolve that cookie back
 * into auth state (e.g. after a hard refresh), instead of assuming
 * `unauthenticated` until the user logs in again.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState<AuthState>({ status: 'loading' });

  useEffect(() => {
    setUnauthorizedHandler(() => setAuth({ status: 'unauthenticated' }));
    return () => setUnauthorizedHandler(null);
  }, []);

  useEffect(() => {
    let cancelled = false;
    getCurrentUser()
      .then(({ role, user_id }) => {
        setAuth((prev) =>
          cancelled || prev.status !== 'loading'
            ? prev
            : { status: 'authenticated', role, userId: user_id }
        );
      })
      .catch(() => {
        setAuth((prev) => (cancelled || prev.status !== 'loading' ? prev : { status: 'unauthenticated' }));
      });
    return () => {
      cancelled = true;
    };
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
