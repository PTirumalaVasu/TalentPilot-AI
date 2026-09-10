import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { FormErrorText } from '@/components/ui/form-error-text';
import { Card, CardContent } from '@/components/ui/card';
import { ContentPreviewModal } from '@/features/admin/ContentPreviewModal';
import { reviewManualContent, type ManualContentCandidate } from '@/lib/api/adminContentApi';
import { parseDurationToHours, estimateDaysToComplete } from '@/lib/utils/duration';

export interface ManualContentEntryFormProps {
  skillId: string;
}

function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response?: { data?: { message?: string } } }).response;
    if (response?.data?.message) return response.data.message;
  }
  return fallback;
}

/**
 * The Content Lookup Panel's "Paste a link" tab (Story 6.7, FR-17a), built
 * as a standalone component ahead of Story 6.10's real panel -- matches
 * 04.1-skills-content-sourcing.md's content-lookup-manual-* object IDs.
 * [Approve] on the resulting candidate is intentionally disabled: it would
 * call Story 6.8's POST /api/admin/content/attach, which doesn't exist yet.
 */
export function ManualContentEntryForm({ skillId }: ManualContentEntryFormProps) {
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [duration, setDuration] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [candidate, setCandidate] = useState<ManualContentCandidate | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  async function handleReview() {
    setSubmitting(true);
    setError(null);
    setCandidate(null);
    try {
      const result = await reviewManualContent(skillId, {
        url,
        title,
        duration_hours: parseDurationToHours(duration),
      });
      setCandidate(result);
    } catch (err) {
      setError(extractErrorMessage(err, "Couldn't review this link. Check the URL and try again."));
    } finally {
      setSubmitting(false);
    }
  }

  const days = candidate ? estimateDaysToComplete(candidate.duration_hours) : null;

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        <div>
          <Label htmlFor="manual-url-input">URL</Label>
          <Input
            id="manual-url-input"
            placeholder="Paste a content link…"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={submitting}
            data-testid="content-lookup-manual-url-input"
          />
        </div>
        <div>
          <Label htmlFor="manual-title-input">Title</Label>
          <Input
            id="manual-title-input"
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={submitting}
            data-testid="content-lookup-manual-title-input"
          />
        </div>
        <div>
          <Label htmlFor="manual-duration-input">Duration (optional)</Label>
          <Input
            id="manual-duration-input"
            placeholder="Duration (optional, e.g. 2h 30m)"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            disabled={submitting}
            data-testid="content-lookup-manual-duration-input"
          />
        </div>
        <Button
          onClick={handleReview}
          disabled={submitting || !url.trim() || !title.trim()}
          data-testid="content-lookup-manual-btn-review"
        >
          {submitting ? 'Reviewing…' : 'Review link'}
        </Button>
        {error && <FormErrorText>{error}</FormErrorText>}
      </div>

      {candidate && (
        <Card data-testid="content-lookup-result-card">
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-medium text-gray-900">{candidate.title}</span>
              <span className="text-xs font-medium uppercase text-gray-500">{candidate.source}</span>
            </div>
            {days != null && (
              <p className="text-xs text-gray-500" data-testid="content-lookup-result-days-estimate">
                ≈ {days} day{days === 1 ? '' : 's'} to complete (at 5 hrs/day)
              </p>
            )}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPreviewOpen(true)}
                data-testid="content-lookup-btn-view"
              >
                View
              </Button>
              <Button
                size="sm"
                disabled
                title="Available once Story 6.8 ships"
                data-testid="content-lookup-btn-approve"
              >
                Approve
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {candidate && (
        <ContentPreviewModal
          open={previewOpen}
          onClose={() => setPreviewOpen(false)}
          title={candidate.title}
          source={candidate.source}
          url={candidate.url}
          durationHours={candidate.duration_hours}
        />
      )}
    </div>
  );
}
