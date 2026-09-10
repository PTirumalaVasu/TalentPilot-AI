import { useEffect, useId, useRef, useState } from 'react';
import { Dialog } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { FormErrorText } from '@/components/ui/form-error-text';
import { createSkill, type SkillResponse } from '@/lib/api/skillsApi';

export interface NewSkillModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: (skill: SkillResponse, searchTerm: string) => void;
  /** enteredName: the name typed into this modal that triggered the 409 -- carried over as the Content Lookup Panel's pre-filled search term (UX-DR31). */
  onUseExisting: (existingSkillId: string, existingName: string, enteredName: string) => void;
}

interface ConflictError {
  response?: {
    status?: number;
    data?: { message?: string; extra?: { existing_skill?: { id: string; name: string } } };
  };
}

function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response?: { data?: { message?: string } } }).response;
    if (response?.data?.message) return response.data.message;
  }
  return fallback;
}

/**
 * The "New Skill" panel (Story 6.2, FR-20; create-only per the UX spec's
 * same-day revision -- editing lives in ContentLookupPanel instead). On
 * success, hands off to Story 6.10's Content Lookup Panel with the entered
 * name pre-filled as the search term (UX-DR31). A 409 duplicate offers
 * "Use existing skill" (Scope Note 11) -- unlike ContentLookupPanel's own
 * rename-conflict, which has no such redirect.
 */
export function NewSkillModal({ open, onClose, onCreated, onUseExisting }: NewSkillModalProps) {
  const titleId = useId();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duplicate, setDuplicate] = useState<{ id: string; name: string } | null>(null);
  // Invalidates any in-flight createSkill() request whenever the modal's
  // open state transitions (in either direction) -- without this, closing
  // the modal (or it reopening for a different flow) while a create is
  // still pending let the eventual resolution still call onCreated/set the
  // duplicate notice, unexpectedly reopening ContentLookupPanel after the
  // admin believed they'd cancelled. Mirrors DeleteSkillModal/ApiKeysModal's
  // identical requestIdRef/isMountedRef guard (code review, 2026-09-10).
  const requestIdRef = useRef(0);

  useEffect(() => {
    requestIdRef.current += 1;
    if (!open) return;
    setName('');
    setDescription('');
    setError(null);
    setDuplicate(null);
    setSubmitting(false);
  }, [open]);

  async function handleCreate() {
    const trimmedName = name.trim();
    if (!trimmedName) return;
    const requestIdAtSubmit = requestIdRef.current;
    setSubmitting(true);
    setError(null);
    setDuplicate(null);
    try {
      const skill = await createSkill({ name: trimmedName, description: description.trim() || null });
      if (requestIdRef.current !== requestIdAtSubmit) return;
      onCreated(skill, trimmedName);
    } catch (err) {
      if (requestIdRef.current !== requestIdAtSubmit) return;
      const conflictErr = err as ConflictError;
      if (conflictErr.response?.status === 409) {
        const existing = conflictErr.response.data?.extra?.existing_skill;
        if (existing) {
          setDuplicate(existing);
        } else {
          setError(extractErrorMessage(err, "Couldn't create this skill — Try again"));
        }
      } else {
        setError(extractErrorMessage(err, "Couldn't create this skill — Try again"));
      }
    } finally {
      if (requestIdRef.current === requestIdAtSubmit) setSubmitting(false);
    }
  }

  if (!open) return null;

  return (
    <Dialog open={open} onClose={onClose} titleId={titleId} className="max-w-md">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 id={titleId} className="text-lg font-bold text-gray-900" data-testid="new-skill-header-title">
            New Skill
          </h2>
          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
            className="text-xl leading-none text-gray-400 hover:text-gray-600"
            data-testid="new-skill-btn-close"
          >
            ✕
          </button>
        </div>

        <div>
          <Label htmlFor="new-skill-name-input">Skill name</Label>
          <Input
            id="new-skill-name-input"
            placeholder="e.g. Docker Fundamentals"
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              // Clear a stale duplicate notice on edit -- otherwise its
              // "Use existing skill" link keeps pointing at the original
              // conflicting Skill even after the name no longer matches it
              // (code review, 2026-09-10).
              setDuplicate(null);
            }}
            disabled={submitting}
            data-testid="new-skill-name-input"
          />
        </div>
        <div>
          <Label htmlFor="new-skill-description-input">Description (optional)</Label>
          <textarea
            id="new-skill-description-input"
            rows={2}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={submitting}
            data-testid="new-skill-description-input"
          />
        </div>

        {duplicate && (
          <div
            className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800"
            data-testid="new-skill-duplicate-notice"
          >
            A skill named &apos;{name.trim()}&apos; already exists.{' '}
            <button
              type="button"
              className="font-medium underline"
              onClick={() => onUseExisting(duplicate.id, duplicate.name, name.trim())}
            >
              Use existing skill
            </button>
          </div>
        )}
        {error && <FormErrorText>{error}</FormErrorText>}

        <Button
          className="w-full"
          onClick={handleCreate}
          disabled={submitting || !name.trim()}
          data-testid="new-skill-btn-create"
        >
          {submitting ? 'Creating…' : 'Create & find content'}
        </Button>
      </div>
    </Dialog>
  );
}
