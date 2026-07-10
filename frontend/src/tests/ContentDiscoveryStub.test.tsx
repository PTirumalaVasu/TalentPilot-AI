import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '@/lib/auth/AuthContext';
import { ContentDiscoveryStub } from '@/pages/employee/ContentDiscoveryStub';

const navigateMock = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateMock };
});

vi.mock('@/lib/api/authApi', () => ({
  logout: vi.fn().mockResolvedValue(undefined),
}));

import { logout } from '@/lib/api/authApi';

describe('ContentDiscoveryStub sign out', () => {
  beforeEach(() => {
    vi.mocked(logout).mockClear();
    navigateMock.mockReset();
  });

  it('calls the real logout endpoint and redirects to /login', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <AuthProvider>
          <ContentDiscoveryStub />
        </AuthProvider>
      </MemoryRouter>
    );

    await user.click(screen.getByRole('button', { name: /sign out/i }));

    expect(logout).toHaveBeenCalledTimes(1);
    expect(navigateMock).toHaveBeenCalledWith('/login', { replace: true });
  });

  it('still clears state and redirects to /login when the logout request fails', async () => {
    vi.mocked(logout).mockRejectedValueOnce(new Error('network error'));
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <AuthProvider>
          <ContentDiscoveryStub />
        </AuthProvider>
      </MemoryRouter>
    );

    await user.click(screen.getByRole('button', { name: /sign out/i }));

    expect(navigateMock).toHaveBeenCalledWith('/login', { replace: true });
  });
});
