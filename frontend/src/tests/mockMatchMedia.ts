import { vi } from 'vitest';

/**
 * Overrides the default window.matchMedia stub (frontend/src/tests/setup.ts)
 * with a specific `matches` value for tests that need per-case control
 * (e.g. simulating an OS dark/light preference). Shared by
 * ThemeContext.test.tsx and ThemeToggle.test.tsx (code review finding:
 * previously duplicated inline in both).
 */
export function mockMatchMedia(matches: boolean) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}
