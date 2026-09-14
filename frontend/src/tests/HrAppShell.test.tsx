import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '@/lib/auth/AuthContext';
import { ThemeProvider } from '@/lib/theme/ThemeContext';
import { HrAppShell } from '@/components/layout/HrAppShell';

// Story 8.1: HrAppShell now renders <ThemeToggle>, which calls useTheme() --
// the shared window.matchMedia stub (frontend/src/tests/setup.ts) covers
// jsdom's lack of a real implementation (code review: previously duplicated
// here instead of centralized).

const navigateMock = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateMock };
});

vi.mock('@/lib/api/authApi', () => ({
  logout: vi.fn().mockResolvedValue(undefined),
  getMe: vi.fn().mockResolvedValue({
    user_id: 'rita-1',
    role: 'HR_ADMIN',
    name: 'Rita the Recruiter',
    email: 'rita@sails.example.com',
  }),
}));

import { logout } from '@/lib/api/authApi';

function renderShell(initialPath = '/hr/dashboard') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <ThemeProvider>
        <AuthProvider>
          <Routes>
            <Route path="*" element={<HrAppShell>Page content</HrAppShell>} />
          </Routes>
        </AuthProvider>
      </ThemeProvider>
    </MemoryRouter>
  );
}

describe('HrAppShell (Story 7.7)', () => {
  beforeEach(() => {
    navigateMock.mockReset();
    vi.mocked(logout).mockClear();
  });

  it('renders all four nav destinations, in order, and the page content', () => {
    renderShell();

    const links = screen.getByTestId('app-nav-sidebar').querySelectorAll('nav a');
    expect(Array.from(links).map((l) => l.textContent)).toEqual([
      'Dashboard',
      'Skill Assignments',
      'Skills',
      'Employees',
    ]);

    expect(screen.getByTestId('app-nav-link-dashboard')).toHaveAttribute('href', '/dashboard');
    expect(screen.getByTestId('app-nav-link-skill-assignments')).toHaveAttribute('href', '/hr/dashboard');
    expect(screen.getByTestId('app-nav-link-skills')).toHaveAttribute('href', '/skills');
    expect(screen.getByTestId('app-nav-link-employees')).toHaveAttribute('href', '/employees');
    expect(screen.getByText('Page content')).toBeInTheDocument();
  });

  it('marks Dashboard active with the same treatment when on the landing page route', () => {
    renderShell('/dashboard');

    const dashboardLink = screen.getByTestId('app-nav-link-dashboard');
    expect(dashboardLink).toHaveAttribute('aria-current', 'page');
    expect(dashboardLink.className).toMatch(/font-medium/);

    const skillAssignmentsLink = screen.getByTestId('app-nav-link-skill-assignments');
    expect(skillAssignmentsLink).not.toHaveAttribute('aria-current');
  });

  it('marks the current page active with aria-current and a non-color-only style', () => {
    renderShell('/employees');

    const employeesLink = screen.getByTestId('app-nav-link-employees');
    expect(employeesLink).toHaveAttribute('aria-current', 'page');
    expect(employeesLink.className).toMatch(/font-medium/);

    const dashboardLink = screen.getByTestId('app-nav-link-dashboard');
    expect(dashboardLink).not.toHaveAttribute('aria-current');
  });

  it('marks Skill Assignments active with the same treatment when on the full grid route', () => {
    renderShell('/hr/dashboard');

    const skillAssignmentsLink = screen.getByTestId('app-nav-link-skill-assignments');
    expect(skillAssignmentsLink).toHaveAttribute('aria-current', 'page');
    expect(skillAssignmentsLink.className).toMatch(/font-medium/);

    const dashboardLink = screen.getByTestId('app-nav-link-dashboard');
    expect(dashboardLink).not.toHaveAttribute('aria-current');
  });

  it('keeps the user menu in place with Sign Out behavior unchanged', async () => {
    const user = userEvent.setup();
    renderShell();

    await user.click(screen.getByRole('button', { name: /rita/i }));
    await user.click(screen.getByRole('button', { name: /sign out/i }));

    expect(logout).toHaveBeenCalled();
    expect(navigateMock).toHaveBeenCalledWith('/login', { replace: true });
  });

  it('collapses the sidebar off-screen and reveals it via the mobile hamburger, with a dismissible backdrop', async () => {
    const user = userEvent.setup();
    renderShell();

    const sidebar = screen.getByTestId('app-nav-sidebar');
    expect(sidebar.className).toMatch(/-translate-x-full/);
    expect(screen.queryByTestId('app-nav-backdrop')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /open menu/i }));
    expect(sidebar.className).toMatch(/translate-x-0/);
    expect(screen.getByTestId('app-nav-backdrop')).toBeInTheDocument();

    await user.click(screen.getByTestId('app-nav-backdrop'));
    expect(sidebar.className).toMatch(/-translate-x-full/);
    expect(screen.queryByTestId('app-nav-backdrop')).not.toBeInTheDocument();
  });

  it('closes the mobile nav when a nav link is clicked', async () => {
    const user = userEvent.setup();
    renderShell();

    await user.click(screen.getByRole('button', { name: /open menu/i }));
    expect(screen.getByTestId('app-nav-sidebar').className).toMatch(/translate-x-0/);

    await user.click(screen.getByTestId('app-nav-link-skills'));
    expect(screen.getByTestId('app-nav-sidebar').className).toMatch(/-translate-x-full/);
  });
});
