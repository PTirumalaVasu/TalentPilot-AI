import '@testing-library/jest-dom/vitest';

// jsdom has no real window.matchMedia implementation. Story 8.1's
// ThemeProvider calls it unconditionally on mount (via useTheme()'s
// ThemeToggle, rendered in HrAppShell.tsx/ContentDiscovery.tsx), so any test
// that mounts a component tree containing either would otherwise throw.
// Default stub always reports "no dark preference" -- tests that need to
// control the result per-case (ThemeContext.test.tsx, ThemeToggle.test.tsx)
// override this with their own local Object.defineProperty call, which
// works because this one is `configurable: true`. (Code review finding:
// previously this same ~15-line stub was copy-pasted into 6 test files.)
if (!window.matchMedia) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });
}
