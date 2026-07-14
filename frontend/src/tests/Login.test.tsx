import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '@/lib/auth/AuthContext';
import { Login } from '@/pages/Login';

const navigateMock = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateMock };
});

vi.mock('@/lib/api/authApi', () => ({
  login: vi.fn(),
  getCurrentUser: vi.fn().mockRejectedValue({ isAxiosError: true, response: { status: 401 } }),
}));

import { login } from '@/lib/api/authApi';

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthProvider>
        <Login />
      </AuthProvider>
    </MemoryRouter>
  );
}

async function fillAndSubmit(user: ReturnType<typeof userEvent.setup>, email: string, password: string) {
  await user.type(screen.getByLabelText(/email/i), email);
  await user.type(screen.getByLabelText(/password/i), password);
  await user.click(screen.getByRole('button', { name: /sign in/i }));
}

describe('Login', () => {
  beforeEach(() => {
    vi.mocked(login).mockReset();
    navigateMock.mockReset();
  });

  it('shows validation errors and never calls the API for an empty submission', async () => {
    const user = userEvent.setup();
    renderLogin();

    await user.click(screen.getByRole('button', { name: /sign in/i }));

    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    expect(login).not.toHaveBeenCalled();
  });

  it('shows a validation error for a malformed email and never calls the API', async () => {
    const user = userEvent.setup();
    renderLogin();

    await fillAndSubmit(user, 'not-an-email', 'demo123');

    expect(await screen.findByText(/enter a valid email/i)).toBeInTheDocument();
    expect(login).not.toHaveBeenCalled();
  });

  it('redirects an HR_ADMIN to the HR dashboard on successful login', async () => {
    vi.mocked(login).mockResolvedValueOnce({ role: 'HR_ADMIN', user_id: 'rita' });
    const user = userEvent.setup();
    renderLogin();

    await fillAndSubmit(user, 'rita@sails.example.com', 'demo123');

    await waitFor(() =>
      expect(navigateMock).toHaveBeenCalledWith('/hr/dashboard', { replace: true })
    );
  });

  it('redirects an EMPLOYEE to Content Discovery on successful login', async () => {
    vi.mocked(login).mockResolvedValueOnce({ role: 'EMPLOYEE', user_id: 'casey' });
    const user = userEvent.setup();
    renderLogin();

    await fillAndSubmit(user, 'casey@sails.example.com', 'demo123');

    await waitFor(() =>
      expect(navigateMock).toHaveBeenCalledWith('/employee/content', { replace: true })
    );
  });

  it('shows the exact backend message on invalid credentials (401), without saying which field was wrong', async () => {
    vi.mocked(login).mockRejectedValueOnce({
      isAxiosError: true,
      response: { status: 401, data: { message: 'Email or password incorrect' } },
    });
    const user = userEvent.setup();
    renderLogin();

    await fillAndSubmit(user, 'casey@sails.example.com', 'wrong-password');

    expect(await screen.findByText('Email or password incorrect')).toBeInTheDocument();
    expect(navigateMock).not.toHaveBeenCalled();
  });

  it('shows a distinct generic message on a network/5xx failure, not the credentials error', async () => {
    vi.mocked(login).mockRejectedValueOnce(new Error('Network Error'));
    const user = userEvent.setup();
    renderLogin();

    await fillAndSubmit(user, 'casey@sails.example.com', 'demo123');

    expect(await screen.findByText('Something went wrong, please try again.')).toBeInTheDocument();
    expect(screen.queryByText('Email or password incorrect')).not.toBeInTheDocument();
  });
});
