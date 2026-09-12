import { useTheme } from '@/lib/theme/ThemeContext';

/** Hand-rolled, matching this codebase's no-icon-library convention
 * (HrAppShell.tsx's hamburger, DashboardPage.tsx's TrashIcon) --
 * `fill="currentColor"` so the button's `text-*` classes actually reach
 * the glyph. */
function MoonIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
    </svg>
  );
}

function SunIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path
        fillRule="evenodd"
        d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 9a1 1 0 100 2h1a1 1 0 100-2h-1zM4.464 4.343a1 1 0 011.414 1.414l-.707.707A1 1 0 013.757 5.05l.707-.707zM3 9a1 1 0 000 2h1a1 1 0 100-2H3zm3.757 6.657a1 1 0 011.414 0 1 1 0 010 1.414l-.707.707a1 1 0 11-1.414-1.414l.707-.707zM10 16a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1z"
        clipRule="evenodd"
      />
    </svg>
  );
}

/**
 * Theme toggle (Story 8.1, AC2). Placed alongside the user-menu in
 * HrAppShell.tsx and ContentDiscovery.tsx's header, per the epics AC's own
 * placement anchor -- not on Login (no user-menu to sit alongside there).
 */
export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button
      type="button"
      data-testid="theme-toggle"
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      className="flex h-9 w-9 items-center justify-center rounded-full text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-200"
    >
      {isDark ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}
