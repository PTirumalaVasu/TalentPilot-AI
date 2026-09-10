import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ContentPreviewModal } from '@/features/admin/ContentPreviewModal';

describe('ContentPreviewModal', () => {
  it('does not render when closed', () => {
    render(
      <ContentPreviewModal
        open={false}
        onClose={vi.fn()}
        title="A Video"
        source="MANUAL"
        url="https://example.com/a-video"
      />
    );
    expect(screen.queryByText('A Video')).not.toBeInTheDocument();
  });

  it('embeds a recognizable watch?v= YouTube URL', () => {
    render(
      <ContentPreviewModal
        open
        onClose={vi.fn()}
        title="A YouTube Video"
        source="YOUTUBE"
        url="https://www.youtube.com/watch?v=abc123XYZ"
      />
    );
    const iframe = screen.getByTitle('A YouTube Video');
    expect(iframe.tagName).toBe('IFRAME');
    expect(iframe).toHaveAttribute('src', 'https://www.youtube.com/embed/abc123XYZ');
  });

  it('embeds a recognizable youtu.be short URL', () => {
    render(
      <ContentPreviewModal
        open
        onClose={vi.fn()}
        title="A Short YouTube Link"
        source="YOUTUBE"
        url="https://youtu.be/abc123XYZ"
      />
    );
    const iframe = screen.getByTitle('A Short YouTube Link');
    expect(iframe).toHaveAttribute('src', 'https://www.youtube.com/embed/abc123XYZ');
  });

  it('does not embed a non-YouTube URL that merely contains a youtube.com/watch?v= substring', () => {
    // Code review (2026-09-10): the regex previously matched this substring
    // anywhere in the string, misidentifying a non-YouTube URL as
    // embeddable and silently embedding an unrelated video.
    render(
      <ContentPreviewModal
        open
        onClose={vi.fn()}
        title="A Redirect Link"
        source="MANUAL"
        url="https://example.com/redirect?to=youtube.com/watch?v=XXXXXXX"
      />
    );
    expect(screen.queryByTitle('A Redirect Link')).not.toBeInTheDocument();
    expect(screen.getByText(/Preview not available for MANUAL/)).toBeInTheDocument();
  });

  it('shows the fallback state and an external link for a non-embeddable URL', () => {
    render(
      <ContentPreviewModal
        open
        onClose={vi.fn()}
        title="A Manual Doc"
        source="MANUAL"
        url="https://example.com/a-doc"
      />
    );
    expect(screen.getByText(/Preview not available for MANUAL/)).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /Open in new tab/ });
    expect(link).toHaveAttribute('href', 'https://example.com/a-doc');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', expect.stringContaining('noreferrer'));
  });

  it('shows duration/days-to-complete meta when provided', () => {
    render(
      <ContentPreviewModal
        open
        onClose={vi.fn()}
        title="A Video"
        source="MANUAL"
        url="https://example.com/a-video"
        durationHours={4}
      />
    );
    expect(screen.getByText(/4h.*≈ 1 day to complete/)).toBeInTheDocument();
  });

  it('closing removes the iframe from the DOM', () => {
    const { rerender } = render(
      <ContentPreviewModal
        open
        onClose={vi.fn()}
        title="A YouTube Video"
        source="YOUTUBE"
        url="https://www.youtube.com/watch?v=abc123XYZ"
      />
    );
    expect(screen.getByTitle('A YouTube Video')).toBeInTheDocument();

    rerender(
      <ContentPreviewModal
        open={false}
        onClose={vi.fn()}
        title="A YouTube Video"
        source="YOUTUBE"
        url="https://www.youtube.com/watch?v=abc123XYZ"
      />
    );
    expect(screen.queryByTitle('A YouTube Video')).not.toBeInTheDocument();
  });
});
