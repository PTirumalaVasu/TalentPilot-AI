import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ManualContentEntryForm } from '@/features/admin/ManualContentEntryForm';

/**
 * Dev-only page to exercise ManualContentEntryForm (Story 6.7) ahead of the
 * real Skills tab (Story 6.10, not built yet) that will eventually render it
 * as the Content Lookup Panel's "Paste a link" tab. Mirrors
 * ApiKeysModalDemo.tsx's role -- unlike that component, this one needs a
 * real skill_id, so this page adds a small text input for one (paste in a
 * real seeded Skill's UUID, e.g. from POST /api/admin/skills).
 */
export function ManualContentEntryDemo() {
  const [skillId, setSkillId] = useState('');

  return (
    <div className="mx-auto max-w-3xl p-8">
      <h1 className="text-2xl font-bold">Manual Content Entry (dev demo)</h1>
      <p className="mb-6 text-sm text-slate-500">Story 6.7: Manual Content Link Entry</p>

      <div className="mb-6">
        <Label htmlFor="dev-skill-id-input">Skill ID</Label>
        <Input
          id="dev-skill-id-input"
          placeholder="Paste a real Skill UUID"
          value={skillId}
          onChange={(e) => setSkillId(e.target.value)}
        />
      </div>

      {skillId.trim() ? (
        <ManualContentEntryForm skillId={skillId.trim()} />
      ) : (
        <p className="text-sm text-slate-500">Enter a Skill ID above to load the form.</p>
      )}
    </div>
  );
}
