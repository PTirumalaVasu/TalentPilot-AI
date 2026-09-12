import { beforeEach, describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider } from '@/lib/theme/ThemeContext';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { mockMatchMedia } from './mockMatchMedia';

describe('ThemeToggle (Story 8.1)', () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.classList.remove('dark');
    mockMatchMedia(false);
  });

  it('shows a "Switch to dark theme" label when the current theme is light', () => {
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );

    expect(screen.getByTestId('theme-toggle')).toHaveAttribute('aria-label', 'Switch to dark theme');
  });

  it('clicking switches to dark: label flips and the <html> class is applied', async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );

    await user.click(screen.getByTestId('theme-toggle'));

    expect(screen.getByTestId('theme-toggle')).toHaveAttribute('aria-label', 'Switch to light theme');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('clicking twice returns to light', async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    );

    const button = screen.getByTestId('theme-toggle');
    await user.click(button);
    await user.click(button);

    expect(button).toHaveAttribute('aria-label', 'Switch to dark theme');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });
});
