import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('@/lib/api/client', () => ({
  apiClient: { post: vi.fn() },
}));

import { apiClient } from '@/lib/api/client';
import { login, logout } from '@/lib/api/authApi';

const postMock = vi.mocked(apiClient.post);

describe('authApi', () => {
  beforeEach(() => {
    postMock.mockReset();
  });

  it('login posts { email, password } to /api/auth/login and returns the response body', async () => {
    postMock.mockResolvedValueOnce({ data: { role: 'HR_ADMIN', user_id: 'rita' } });

    const result = await login('rita@sails.example.com', 'demo123');

    expect(postMock).toHaveBeenCalledWith('/api/auth/login', {
      email: 'rita@sails.example.com',
      password: 'demo123',
    });
    expect(result).toEqual({ role: 'HR_ADMIN', user_id: 'rita' });
  });

  it('logout posts to /api/auth/logout with no body', async () => {
    postMock.mockResolvedValueOnce({ status: 204 });

    await logout();

    expect(postMock).toHaveBeenCalledWith('/api/auth/logout');
  });
});
