/** Shared HR Admin left-pane navigation shell (Story 7.7, FR-29).
 *
 * Replaces the top-header nav previously duplicated across
 * Dashboard.tsx/SkillsPage.tsx/EmployeesPage.tsx: a persistent left sidebar
 * (Dashboard/Skills/Employees) collapsing to a hamburger-triggered overlay
 * below the 768px breakpoint (UX-DR40), plus a slim top bar carrying only
 * the theme toggle (Story 8.1) and user menu -- unchanged in position/behavior
 * (AC2). */
import { useState, type ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth/AuthContext';
import { logout } from '@/lib/api/authApi';
import { ThemeToggle } from '@/components/ui/theme-toggle';

const NAV_LINKS = [
  { to: '/hr/dashboard', label: 'Dashboard', testId: 'app-nav-link-dashboard' },
  { to: '/skills', label: 'Skills', testId: 'app-nav-link-skills' },
  { to: '/employees', label: 'Employees', testId: 'app-nav-link-employees' },
];

export function HrAppShell({ children }: { children: ReactNode }) {
  const { signOut } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

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

  return (
    <div className="flex min-h-screen bg-gray-50 font-sans dark:bg-gray-950">
      {mobileNavOpen && (
        <div
          data-testid="app-nav-backdrop"
          onClick={() => setMobileNavOpen(false)}
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
        />
      )}

      <aside
        data-testid="app-nav-sidebar"
        className={
          'fixed inset-y-0 left-0 z-40 flex w-56 shrink-0 transform flex-col border-r border-gray-200 bg-white transition-transform duration-200 md:static md:translate-x-0 dark:border-gray-700 dark:bg-gray-900 ' +
          (mobileNavOpen ? 'translate-x-0' : '-translate-x-full')
        }
      >
        <div className="flex items-center justify-between border-b border-gray-100 px-5 py-5 dark:border-gray-800">
          <div className="flex items-center gap-2 text-lg font-bold text-gray-900 dark:text-gray-100">TalentPilot-AI</div>
          <button
            type="button"
            onClick={() => setMobileNavOpen(false)}
            className="text-xl text-gray-400 hover:text-gray-600 md:hidden dark:text-gray-500 dark:hover:text-gray-300"
            aria-label="Close menu"
          >
            &times;
          </button>
        </div>
        <nav className="flex-1 space-y-1 px-3 py-4 text-sm">
          {NAV_LINKS.map((link) => {
            const active = location.pathname === link.to;
            return (
              <Link
                key={link.to}
                to={link.to}
                data-testid={link.testId}
                aria-current={active ? 'page' : undefined}
                onClick={() => setMobileNavOpen(false)}
                className={
                  'block rounded-lg px-3 py-2 transition-colors ' +
                  (active
                    ? 'bg-blue-50 font-medium text-blue-700 dark:bg-blue-950 dark:text-blue-300'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-100')
                }
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3 md:justify-end md:px-6 dark:border-gray-700 dark:bg-gray-900">
          <button
            type="button"
            onClick={() => setMobileNavOpen(true)}
            className="text-gray-600 hover:text-gray-900 md:hidden dark:text-gray-400 dark:hover:text-gray-100"
            aria-label="Open menu"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 12h18M3 6h18M3 18h18" />
            </svg>
          </button>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300"
              >
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 font-medium text-blue-700 dark:bg-blue-900 dark:text-blue-300">
                  R
                </span>
                Rita
              </button>
              {userMenuOpen && (
                <div className="absolute right-0 z-10 mt-2 w-40 rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-900">
                  <button
                    onClick={() => {
                      setUserMenuOpen(false);
                      void handleSignOut();
                    }}
                    className="block w-full rounded-lg px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
                  >
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {children}
      </div>
    </div>
  );
}
