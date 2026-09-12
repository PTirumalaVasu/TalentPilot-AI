import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

export type Theme = 'light' | 'dark';

const STORAGE_KEY = 'theme';

function getSystemTheme(): Theme {
  // Guarded (code review finding): matchMedia can throw or be unavailable in
  // some locked-down environments (older browsers, restrictive iframe/CSP
  // sandboxes) -- since this runs at ThemeProvider's mount (the outermost
  // provider, wrapping Login too), an unguarded throw here would crash the
  // entire app at first render. Mirrors index.html's inline script, which
  // already wraps the equivalent read in try/catch.
  try {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  } catch {
    return 'light';
  }
}

/**
 * Resolution order (Story 8.1, AC1): an explicit prior choice on this
 * browser wins; otherwise fall back to the OS/browser preference. Mirrors
 * the inline script in index.html (kept in sync manually -- that script has
 * no access to this module, see index.html's own comment) so React's first
 * render never disagrees with what was already painted, avoiding a
 * hydration-time flash/mismatch.
 */
function getInitialTheme(): Theme {
  // Guarded (code review finding): localStorage.getItem can throw (private
  // browsing, storage-access-restricted contexts) -- same crash-at-mount
  // risk as getSystemTheme() above.
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') return stored;
  } catch {
    // Fall through to the OS-preference default.
  }
  return getSystemTheme();
}

interface ThemeContextValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

/**
 * In-memory + localStorage, by design (FR-30/§9): a per-browser display
 * preference, never synced to the account server-side -- no backend module
 * exists for this story at all. Mirrors AuthContext.tsx's Provider/hook
 * shape exactly.
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  // Defined inline inside useMemo (code review finding), matching
  // AuthContext.tsx's identical signIn/signOut pattern exactly -- keeps the
  // dependency array accurate ([theme] only) without needing setTheme in it
  // or a separate useCallback.
  const value = useMemo<ThemeContextValue>(
    () => ({
      theme,
      setTheme: (next: Theme) => {
        setThemeState(next);
        try {
          window.localStorage.setItem(STORAGE_KEY, next);
        } catch {
          // Best-effort persistence only (e.g. private browsing/quota) -- the
          // in-memory theme change still applies for this page load.
        }
      },
    }),
    [theme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within a ThemeProvider');
  return ctx;
}
