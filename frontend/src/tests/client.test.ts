import { describe, it, expect, vi, beforeEach } from 'vitest';

const { responseUseMock } = vi.hoisted(() => ({ responseUseMock: vi.fn() }));

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: { response: { use: responseUseMock } },
    })),
    isAxiosError: (err: unknown) =>
      typeof err === 'object' && err !== null && (err as { isAxiosError?: boolean }).isAxiosError === true,
  },
}));

import { setUnauthorizedHandler } from '@/lib/api/client';

function getRejectedHandler(): (error: unknown) => Promise<never> {
  const [, rejected] = responseUseMock.mock.calls[0];
  return rejected;
}

describe('apiClient 401 interceptor', () => {
  beforeEach(() => {
    setUnauthorizedHandler(null);
  });

  it('invokes the registered handler when a response is a 401', async () => {
    const handler = vi.fn();
    setUnauthorizedHandler(handler);

    const rejected = getRejectedHandler();
    const error = { isAxiosError: true, response: { status: 401 } };

    await expect(rejected(error)).rejects.toBe(error);
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('does not invoke the handler for a non-401 error', async () => {
    const handler = vi.fn();
    setUnauthorizedHandler(handler);

    const rejected = getRejectedHandler();
    const error = { isAxiosError: true, response: { status: 500 } };

    await expect(rejected(error)).rejects.toBe(error);
    expect(handler).not.toHaveBeenCalled();
  });

  it('does nothing (and still rejects) when no handler is registered', async () => {
    const rejected = getRejectedHandler();
    const error = { isAxiosError: true, response: { status: 401 } };

    await expect(rejected(error)).rejects.toBe(error);
  });
});
