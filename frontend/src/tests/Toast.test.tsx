import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Toast } from '@/components/ui/toast';

describe('Toast', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders nothing when message is null', () => {
    render(<Toast message={null} onDismiss={vi.fn()} />);
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('renders the message with role=status/aria-live=polite for assistive-tech announcement', () => {
    render(<Toast message="✓ Skill assigned to Casey — Data Visualization" onDismiss={vi.fn()} />);
    const toast = screen.getByRole('status');
    expect(toast).toHaveAttribute('aria-live', 'polite');
    expect(toast).toHaveTextContent('✓ Skill assigned to Casey — Data Visualization');
  });

  it('calls onDismiss after durationMs elapses', () => {
    const onDismiss = vi.fn();
    render(<Toast message="Saved" onDismiss={onDismiss} durationMs={4000} />);

    vi.advanceTimersByTime(3999);
    expect(onDismiss).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it('does not fire a stale dismiss timer after the message changes', () => {
    const onDismiss = vi.fn();
    const { rerender } = render(<Toast message="First" onDismiss={onDismiss} durationMs={4000} />);

    vi.advanceTimersByTime(2000);
    rerender(<Toast message="Second" onDismiss={onDismiss} durationMs={4000} />);
    vi.advanceTimersByTime(2000);

    // 4000ms have elapsed in total, but only 2000ms since "Second" mounted —
    // the first timer must have been cleared, not left to fire early.
    expect(onDismiss).not.toHaveBeenCalled();
  });
});
