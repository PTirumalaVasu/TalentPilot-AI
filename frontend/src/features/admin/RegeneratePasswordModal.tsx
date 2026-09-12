import { useEffect, useId, useRef, useState } from 'react';
import { Dialog } from '@/components/ui/dialog';
import { FormErrorText } from '@/components/ui/form-error-text';
import { regeneratePassword } from '@/lib/api/employeesApi';

export interface RegeneratePasswordModalProps {
  employee: { id: string; name: string } | null;
  open: boolean;
  onClose: () => void;
  onCopied: () => void;
}

type Step = 'confirm' | 'regenerating' | 'revealed';

function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response?: { data?: { message?: string } } }).response;
    if (response?.data?.message) return response.data.message;
  }
  return fallback;
}

/**
 * Regenerate Password confirm + one-time reveal modal (Story 7.6, FR-28).
 * Mirrors DeleteArchiveEmployeeModal.tsx's Dialog/requestIdRef/
 * extractErrorMessage() shape, but is a two-step flow within one modal
 * (confirm -> regenerating -> revealed) rather than a single confirm action,
 * per 05.1's Regenerate Password Panel + 05.3's Password Reveal Panel specs.
 * This is the first Password Reveal UI in the codebase -- Story 7.2's Create
 * flow shipped backend-only, so no prior frontend implementation exists to
 * reuse (see this story's Dev Notes).
 */
export function RegeneratePasswordModal({ employee, open, onClose, onCopied }: RegeneratePasswordModalProps) {
  const titleId = useId();
  const [step, setStep] = useState<Step>('confirm');
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [generatedPassword, setGeneratedPassword] = useState<string | null>(null);
  const requestIdRef = useRef(0);

  useEffect(() => {
    requestIdRef.current += 1;
    setStep('confirm');
    setSubmitError(null);
    setGeneratedPassword(null);
  }, [employee?.id, open]);

  function handleCancel() {
    requestIdRef.current += 1;
    onClose();
  }

  // No-op while a regenerate request is in flight (code review, 2026-09-12):
  // Dialog's Escape/backdrop-click dismissal isn't gated by the disabled
  // Cancel button, so without this, closing mid-request would silently
  // discard an already-completed regeneration -- the server-side password
  // change already happened, but the resolved plaintext would never reach
  // the admin (the stale-request guard in handleConfirm drops it).
  function handleNoOp() {}

  async function handleConfirm() {
    if (!employee) return;
    const requestIdAtSubmit = ++requestIdRef.current;
    setStep('regenerating');
    setSubmitError(null);
    try {
      const result = await regeneratePassword(employee.id);
      if (requestIdRef.current !== requestIdAtSubmit) return;
      setGeneratedPassword(result.generated_password);
      setStep('revealed');
    } catch (err) {
      if (requestIdRef.current !== requestIdAtSubmit) return;
      setSubmitError(extractErrorMessage(err, "Couldn't regenerate — Try again"));
      setStep('confirm');
    }
  }

  async function handleCopy() {
    if (!generatedPassword) return;
    try {
      await navigator.clipboard.writeText(generatedPassword);
      onCopied();
    } catch {
      // Silent fallback (05.3 Design Constraints): the password value is
      // already rendered as selectable text, so Rita can still select/copy
      // it manually -- never surface the failure or log the password.
    }
  }

  function handleDone() {
    requestIdRef.current += 1;
    onClose();
  }

  if (!open || !employee) return null;

  return (
    <Dialog
      open={open}
      onClose={step === 'revealed' ? handleDone : step === 'regenerating' ? handleNoOp : handleCancel}
      titleId={titleId}
      className="max-w-md"
    >
      {step !== 'revealed' ? (
        <div className="space-y-4">
          <h2 id={titleId} className="text-lg font-bold text-gray-900" data-testid="regen-password-heading">
            Regenerate password for {employee.name}?
          </h2>
          <p className="text-sm text-gray-700" data-testid="regen-password-summary">
            Their current password will stop working immediately. You&apos;ll get a new one to share with them.
          </p>

          {submitError && <FormErrorText>{submitError}</FormErrorText>}

          <div className="flex items-center justify-end gap-2 border-t border-gray-100 pt-2">
            <button
              type="button"
              disabled={step === 'regenerating'}
              onClick={handleCancel}
              className="text-sm font-medium text-gray-600 hover:underline disabled:opacity-50"
              data-testid="regen-password-btn-cancel"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={step === 'regenerating'}
              onClick={() => void handleConfirm()}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
              data-testid="regen-password-btn-confirm"
            >
              {step === 'regenerating' ? 'Working…' : 'Regenerate Password'}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <h2 id={titleId} className="text-lg font-bold text-gray-900" data-testid="password-reveal-title">
            Password regenerated
          </h2>
          <p className="text-sm text-gray-700" data-testid="password-reveal-summary">
            Share this password with {employee.name} — it won&apos;t be shown again.
          </p>
          <p
            className="select-all rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 font-mono text-sm text-gray-900"
            data-testid="password-reveal-value"
          >
            {generatedPassword}
          </p>
          <button
            type="button"
            onClick={() => void handleCopy()}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            data-testid="password-reveal-btn-copy"
          >
            Copy
          </button>
          <p className="text-xs text-gray-500" data-testid="password-reveal-recovery-note">
            Lost this before sharing it? Use &quot;Regenerate Password&quot; from the employee&apos;s row — a lost
            password is a quick fix, not a dead end.
          </p>

          <div className="flex items-center justify-end border-t border-gray-100 pt-2">
            <button
              type="button"
              onClick={handleDone}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
              data-testid="password-reveal-btn-done"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </Dialog>
  );
}
