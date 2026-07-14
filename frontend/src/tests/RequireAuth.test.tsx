import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route, useNavigate } from 'react-router-dom';

const { responseUseMock, getMock } = vi.hoisted(() => ({
  responseUseMock: vi.fn(),
  getMock: vi.fn(() => Promise.reject({ isAxiosError: true, response: { status: 401 } })),
}));

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: { response: { use: responseUseMock } },
      get: getMock,
    })),
    isAxiosError: (err: unknown) =>
      typeof err === 'object' &&
      err !== null &&
      (err as { isAxiosError?: boolean }).isAxiosError === true,
  },
}));

import { AuthProvider, useAuth } from '@/lib/auth/AuthContext';
import { RequireAuth } from '@/lib/auth/RequireAuth';

function getInterceptorRejectedHandler(): (error: unknown) => Promise<never> {
  const [, rejected] = responseUseMock.mock.calls[0];
  return rejected;
}

function LoginMarker() {
  return <div>LOGIN PAGE</div>;
}

function ProtectedMarker() {
  const { signOut } = useAuth();
  return (
    <div>
      <p>PROTECTED CONTENT</p>
      <button onClick={() => signOut()}>sign out</button>
    </div>
  );
}

function SignInAndGo() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  return (
    <button
      onClick={() => {
        signIn('EMPLOYEE', 'casey');
        navigate('/protected');
      }}
    >
      sign in and go
    </button>
  );
}

function renderApp(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<SignInAndGo />} />
          <Route path="/login" element={<LoginMarker />} />
          <Route
            path="/protected"
            element={
              <RequireAuth>
                <ProtectedMarker />
              </RequireAuth>
            }
          />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('RequireAuth', () => {
  beforeEach(() => {
    getMock.mockReset();
    getMock.mockImplementation(() =>
      Promise.reject({ isAxiosError: true, response: { status: 401 } })
    );
  });

  it('restores an authenticated session from a valid cookie on mount (refresh persistence)', async () => {
    getMock.mockResolvedValueOnce({ data: { role: 'EMPLOYEE', user_id: 'casey' } });

    renderApp('/protected');

    expect(await screen.findByText('PROTECTED CONTENT')).toBeInTheDocument();
    expect(screen.queryByText('LOGIN PAGE')).not.toBeInTheDocument();
  });

  it('renders neither the login redirect nor protected content while the startup check is pending', async () => {
    let resolveGet!: (value: { data: { role: string; user_id: string } }) => void;
    getMock.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveGet = resolve;
        })
    );

    renderApp('/protected');

    expect(screen.queryByText('LOGIN PAGE')).not.toBeInTheDocument();
    expect(screen.queryByText('PROTECTED CONTENT')).not.toBeInTheDocument();

    await act(async () => {
      resolveGet({ data: { role: 'EMPLOYEE', user_id: 'casey' } });
    });

    expect(await screen.findByText('PROTECTED CONTENT')).toBeInTheDocument();
  });

  it('redirects an unauthenticated visit straight to /login, never rendering protected content', async () => {
    renderApp('/protected');

    expect(await screen.findByText('LOGIN PAGE')).toBeInTheDocument();
    expect(screen.queryByText('PROTECTED CONTENT')).not.toBeInTheDocument();
  });

  it('allows access once authenticated', async () => {
    const user = userEvent.setup();
    renderApp('/');

    await user.click(screen.getByRole('button', { name: /sign in and go/i }));

    expect(await screen.findByText('PROTECTED CONTENT')).toBeInTheDocument();
  });

  it('redirects away the instant auth state goes unauthenticated via explicit sign-out', async () => {
    const user = userEvent.setup();
    renderApp('/');

    await user.click(screen.getByRole('button', { name: /sign in and go/i }));
    expect(await screen.findByText('PROTECTED CONTENT')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /sign out/i }));

    expect(await screen.findByText('LOGIN PAGE')).toBeInTheDocument();
    expect(screen.queryByText('PROTECTED CONTENT')).not.toBeInTheDocument();
  });

  it('redirects away when a real 401 arrives mid-session via apiClient’s own interceptor', async () => {
    const user = userEvent.setup();
    renderApp('/');

    await user.click(screen.getByRole('button', { name: /sign in and go/i }));
    expect(await screen.findByText('PROTECTED CONTENT')).toBeInTheDocument();

    // Exercise the real chain: client.ts's actual interceptor (registered at
    // module load, captured here) invokes the real unauthorizedHandler that
    // AuthProvider registered, which flips context state, which RequireAuth
    // reacts to on its next render — not a shortcut through signOut()/state
    // directly, the way the "explicit sign-out" test above does.
    const rejected = getInterceptorRejectedHandler();
    const error = { isAxiosError: true, response: { status: 401 } };
    await act(async () => {
      await expect(rejected(error)).rejects.toBe(error);
    });

    expect(await screen.findByText('LOGIN PAGE')).toBeInTheDocument();
    expect(screen.queryByText('PROTECTED CONTENT')).not.toBeInTheDocument();
  });
});
