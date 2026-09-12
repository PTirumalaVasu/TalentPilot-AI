import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, useTheme } from '@/lib/theme/ThemeContext';
import { mockMatchMedia } from './mockMatchMedia';

function ThemeProbe() {
  const { theme, setTheme } = useTheme();
  return (
    <div>
      <span data-testid="theme-value">{theme}</span>
      <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>toggle</button>
    </div>
  );
}

describe('ThemeContext (Story 8.1)', () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('AC1: defaults to dark when no stored preference and the OS prefers dark', () => {
    mockMatchMedia(true);

    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme-value')).toHaveTextContent('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('AC1: defaults to light when no stored preference and the OS prefers light', () => {
    mockMatchMedia(false);

    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme-value')).toHaveTextContent('light');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('a previously stored light preference wins over a conflicting OS-dark preference', () => {
    mockMatchMedia(true); // OS says dark
    window.localStorage.setItem('theme', 'light');

    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme-value')).toHaveTextContent('light');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('a previously stored dark preference wins over a conflicting OS-light preference', () => {
    mockMatchMedia(false); // OS says light
    window.localStorage.setItem('theme', 'dark');

    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme-value')).toHaveTextContent('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('AC2: setTheme updates state, the <html> class, and localStorage immediately -- no reload', async () => {
    mockMatchMedia(false);
    const user = userEvent.setup();

    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>
    );

    await user.click(screen.getByRole('button', { name: 'toggle' }));

    expect(screen.getByTestId('theme-value')).toHaveTextContent('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(window.localStorage.getItem('theme')).toBe('dark');
  });

  it('a localStorage write failure does not block the in-memory theme change', async () => {
    mockMatchMedia(false);
    const user = userEvent.setup();
    const setItemSpy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('quota exceeded');
    });

    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>
    );

    await user.click(screen.getByRole('button', { name: 'toggle' }));

    expect(screen.getByTestId('theme-value')).toHaveTextContent('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);

    setItemSpy.mockRestore();
  });

  it('code review regression: a localStorage.getItem throw at mount does not crash the app -- falls back to OS preference', () => {
    mockMatchMedia(true); // OS says dark
    const getItemSpy = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('storage access blocked');
    });

    expect(() =>
      render(
        <ThemeProvider>
          <ThemeProbe />
        </ThemeProvider>
      )
    ).not.toThrow();

    expect(screen.getByTestId('theme-value')).toHaveTextContent('dark');

    getItemSpy.mockRestore();
  });

  it('code review regression: a matchMedia throw at mount does not crash the app -- falls back to light', () => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      configurable: true,
      value: vi.fn().mockImplementation(() => {
        throw new Error('matchMedia unavailable');
      }),
    });

    expect(() =>
      render(
        <ThemeProvider>
          <ThemeProbe />
        </ThemeProvider>
      )
    ).not.toThrow();

    expect(screen.getByTestId('theme-value')).toHaveTextContent('light');
  });

  it('useTheme throws outside a ThemeProvider', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => render(<ThemeProbe />)).toThrow('useTheme must be used within a ThemeProvider');

    consoleError.mockRestore();
  });
});
