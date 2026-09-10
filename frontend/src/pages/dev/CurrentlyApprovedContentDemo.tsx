import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { CurrentlyApprovedContent } from '@/features/admin/CurrentlyApprovedContent';

const SOURCES = ['YOUTUBE', 'UDEMY', 'MANUAL'] as const;
type Source = (typeof SOURCES)[number];

/**
 * Dev-only page to exercise CurrentlyApprovedContent (Story 6.9) ahead of
 * the real Skills tab (Story 6.10, not built yet) that will eventually
 * render it as the Content Lookup Panel's "Currently Approved" section.
 * Mirrors ManualContentEntryDemo.tsx's exact shape -- this component is
 * props-driven, not self-fetching (no read endpoint exists yet for "give me
 * a Skill's current admin-approved Content"), so paste in a real
 * admin-attached Content's fields (e.g. from a POST /api/admin/content/attach
 * response, or a psql lookup).
 */
export function CurrentlyApprovedContentDemo() {
  const [contentId, setContentId] = useState('');
  const [title, setTitle] = useState('');
  const [source, setSource] = useState<Source>('MANUAL');
  const [url, setUrl] = useState('');
  const [duration, setDuration] = useState('');
  const [skillName, setSkillName] = useState('');

  const durationHours = duration.trim() ? Number(duration) : null;

  return (
    <div className="mx-auto max-w-3xl p-8">
      <h1 className="text-2xl font-bold">Currently Approved Content (dev demo)</h1>
      <p className="mb-6 text-sm text-slate-500">Story 6.9: Reject the Currently Approved Content Link</p>

      <div className="mb-6 space-y-3">
        <div>
          <Label htmlFor="dev-content-id-input">Content ID</Label>
          <Input
            id="dev-content-id-input"
            placeholder="Paste a real admin-attached Content UUID"
            value={contentId}
            onChange={(e) => setContentId(e.target.value)}
          />
        </div>
        <div>
          <Label htmlFor="dev-title-input">Title</Label>
          <Input id="dev-title-input" value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <div>
          <Label htmlFor="dev-source-select">Source</Label>
          <select
            id="dev-source-select"
            className="flex h-9 w-full rounded-md border border-gray-300 bg-white px-3 text-sm"
            value={source}
            onChange={(e) => setSource(e.target.value as Source)}
          >
            {SOURCES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div>
          <Label htmlFor="dev-url-input">URL</Label>
          <Input id="dev-url-input" value={url} onChange={(e) => setUrl(e.target.value)} />
        </div>
        <div>
          <Label htmlFor="dev-duration-input">Duration hours (optional)</Label>
          <Input id="dev-duration-input" value={duration} onChange={(e) => setDuration(e.target.value)} />
        </div>
        <div>
          <Label htmlFor="dev-skill-name-input">Skill name (optional)</Label>
          <Input id="dev-skill-name-input" value={skillName} onChange={(e) => setSkillName(e.target.value)} />
        </div>
      </div>

      {contentId.trim() ? (
        <CurrentlyApprovedContent
          contentId={contentId.trim()}
          title={title.trim() || 'Untitled'}
          source={source}
          url={url.trim()}
          durationHours={durationHours}
          skillName={skillName.trim() || undefined}
        />
      ) : (
        <p className="text-sm text-slate-500">Enter a Content ID above to load the card.</p>
      )}
    </div>
  );
}
