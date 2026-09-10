import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { FormErrorText } from '@/components/ui/form-error-text';
import { Card, CardContent } from '@/components/ui/card';
import { Toast } from '@/components/ui/toast';
import { ContentPreviewModal } from '@/features/admin/ContentPreviewModal';
import { rejectContent } from '@/lib/api/adminContentApi';
import { estimateDaysToComplete } from '@/lib/utils/duration';

export interface CurrentlyApprovedContentProps {
  contentId: string;
  title: string;
  source: 'YOUTUBE' | 'UDEMY' | 'MANUAL';
  url: string;
  durationHours: number | null;
  /**
   * Not collected by this story's dev demo page -- Story 6.10's real Skills
   * Card Grid will pass the real Skill name once it exists. Falls back to a
   * generic toast message when omitted (same judgment call as Story 6.8's
   * ManualContentEntryForm `skillName` prop).
   */
  skillName?: string;
  /**
   * Story 6.10 hook: called after a successful reject so the real panel/grid
   * can refresh. Unused by this story's own dev demo page.
   */
  onRejected?: () => void;
}

function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response?: { data?: { message?: string } } }).response;
    if (response?.data?.message) return response.data.message;
  }
  return fallback;
}

/**
 * The Content Lookup Panel's "Currently Approved" section (Story 6.9,
 * FR-23), built as a standalone component ahead of Story 6.10's real panel
 * -- matches 04.1-skills-content-sourcing.md's content-lookup-current-approved
 * / content-lookup-btn-reject object IDs. [Reject] calls Story 6.9's
 * DELETE /api/admin/content/{id}/reject, no confirmation.
 */
export function CurrentlyApprovedContent({
  contentId,
  title,
  source,
  url,
  durationHours,
  skillName,
  onRejected,
}: CurrentlyApprovedContentProps) {
  const [previewOpen, setPreviewOpen] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [rejected, setRejected] = useState(false);
  const [rejectError, setRejectError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  async function handleReject() {
    setRejecting(true);
    setRejectError(null);
    try {
      await rejectContent(contentId);
      setRejected(true);
      setToastMessage(`✓ Rejected the approved link for ${skillName || 'this skill'}`);
      onRejected?.();
    } catch (err) {
      setRejectError(extractErrorMessage(err, "Couldn't reject this — Try again"));
    } finally {
      setRejecting(false);
    }
  }

  const days = estimateDaysToComplete(durationHours);

  return (
    <div className="space-y-4">
      {!rejected && (
        <Card
          data-testid="content-lookup-current-approved"
          className="border-green-200 bg-green-50"
        >
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-medium text-gray-900">{title}</span>
              <span className="text-xs font-medium uppercase text-gray-500">{source}</span>
            </div>
            {days != null && (
              <p className="text-xs text-gray-500" data-testid="content-lookup-result-days-estimate">
                ≈ {days} day{days === 1 ? '' : 's'} to complete (at 5 hrs/day)
              </p>
            )}
            <p className="text-xs text-gray-500">Approving a new link below will also replace this.</p>
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
                variant="outline"
                onClick={handleReject}
                disabled={rejecting}
                data-testid="content-lookup-btn-reject"
              >
                {rejecting ? 'Rejecting…' : 'Reject'}
              </Button>
            </div>
            {rejectError && <FormErrorText>{rejectError}</FormErrorText>}
          </CardContent>
        </Card>
      )}

      <Toast message={toastMessage} onDismiss={() => setToastMessage(null)} />

      <ContentPreviewModal
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
        title={title}
        source={source}
        url={url}
        durationHours={durationHours}
      />
    </div>
  );
}
