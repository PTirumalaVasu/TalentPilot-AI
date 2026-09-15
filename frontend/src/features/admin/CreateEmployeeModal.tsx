import { useEffect, useId, useRef, useState } from 'react';
import { Dialog } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { FormErrorText } from '@/components/ui/form-error-text';
import { createEmployee, type EmployeeCreatedResponse } from '@/lib/api/employeesApi';

export interface CreateEmployeeModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: (employee: EmployeeCreatedResponse) => void;
}

type Step = 'form' | 'creating' | 'revealed';

interface ConflictError {
  response?: { status?: number };
}

function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response?: { data?: { message?: string } } }).response;
    if (response?.data?.message) return response.data.message;
  }
  return fallback;
}

const EMPTY_FIELDS = {
  employee_code: '',
  name: '',
  email: '',
  position: '',
  department: '',
  phone: '',
  location: '',
  manager_name: '',
  project: '',
  technologies: '',
  experience: '',
};

/**
 * The "+ New Employee" create panel (Story 7.2's frontend half, FR-24) --
 * the backend endpoint has been done and tested since Story 7.2; this
 * component is what was actually missing. Mirrors EditEmployeeModal.tsx's
 * Dialog/requestIdRef/409-branching shape for the form step, and
 * RegeneratePasswordModal.tsx's confirm->revealed two-step shape for the
 * one-time password handoff (05.2/05.3 UX specs: success advances straight
 * to the Password Reveal step, not a separate modal).
 */
export function CreateEmployeeModal({ open, onClose, onCreated }: CreateEmployeeModalProps) {
  const titleId = useId();
  const [step, setStep] = useState<Step>('form');
  const [fields, setFields] = useState(EMPTY_FIELDS);
  const [error, setError] = useState<string | null>(null);
  const [duplicate, setDuplicate] = useState(false);
  const [created, setCreated] = useState<EmployeeCreatedResponse | null>(null);
  const requestIdRef = useRef(0);

  useEffect(() => {
    requestIdRef.current += 1;
    if (!open) return;
    setStep('form');
    setFields(EMPTY_FIELDS);
    setError(null);
    setDuplicate(false);
    setCreated(null);
  }, [open]);

  function updateField(field: keyof typeof EMPTY_FIELDS, value: string) {
    setFields((prev) => ({ ...prev, [field]: value }));
    if (field === 'employee_code' || field === 'email') setDuplicate(false);
  }

  // No-op while a create request is in flight -- Dialog's Escape/backdrop
  // dismissal isn't gated by the disabled submit button, so without this,
  // closing mid-request would silently discard an already-created record's
  // one-time password (mirrors RegeneratePasswordModal.tsx's identical
  // guard, code review 2026-09-12).
  function handleNoOp() {}

  function handleCancel() {
    requestIdRef.current += 1;
    onClose();
  }

  async function handleCreate() {
    const trimmedCode = fields.employee_code.trim();
    const trimmedName = fields.name.trim();
    const trimmedEmail = fields.email.trim();
    if (!trimmedCode || !trimmedName || !trimmedEmail) return;

    const requestIdAtSubmit = ++requestIdRef.current;
    setStep('creating');
    setError(null);
    setDuplicate(false);
    try {
      const employee = await createEmployee({
        employee_code: trimmedCode,
        name: trimmedName,
        email: trimmedEmail,
        phone: fields.phone.trim() || null,
        experience: fields.experience.trim() || null,
        technologies: fields.technologies.trim() || null,
        position: fields.position.trim() || null,
        project: fields.project.trim() || null,
        manager_name: fields.manager_name.trim() || null,
        location: fields.location.trim() || null,
        department: fields.department.trim() || null,
      });
      if (requestIdRef.current !== requestIdAtSubmit) return;
      setCreated(employee);
      setStep('revealed');
    } catch (err) {
      if (requestIdRef.current !== requestIdAtSubmit) return;
      const conflictErr = err as ConflictError;
      if (conflictErr.response?.status === 409) {
        // The API distinguishes employee_code vs email conflicts
        // (EMPLOYEE_CODE_CONFLICT / EMPLOYEE_EMAIL_CONFLICT), but the UX
        // spec (05.2) deliberately collapses both into one ambiguous
        // notice at the UI layer -- the API's own granularity is for
        // callers that need it, not this form.
        setDuplicate(true);
      } else {
        setError(extractErrorMessage(err, "Couldn't create this employee — Try again"));
      }
      setStep('form');
    }
  }

  async function handleCopy() {
    if (!created) return;
    try {
      await navigator.clipboard.writeText(created.generated_password);
    } catch {
      // Silent fallback (mirrors RegeneratePasswordModal.tsx's 05.3
      // precedent): the password is already rendered as selectable text.
    }
  }

  function handleDone() {
    if (!created) return;
    requestIdRef.current += 1;
    onCreated(created);
  }

  if (!open) return null;

  return (
    <Dialog
      open={open}
      onClose={step === 'revealed' ? handleDone : step === 'creating' ? handleNoOp : handleCancel}
      titleId={titleId}
      className="max-w-lg"
    >
      {step !== 'revealed' ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 id={titleId} className="text-lg font-bold text-gray-900 dark:text-gray-100" data-testid="create-employee-modal-title">
              New Employee
            </h2>
            <button
              type="button"
              aria-label="Close"
              onClick={handleCancel}
              disabled={step === 'creating'}
              className="text-xl leading-none text-gray-400 hover:text-gray-600 disabled:opacity-50 dark:text-gray-500 dark:hover:text-gray-300"
              data-testid="create-employee-btn-close"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="create-emp-id">Employee ID/Code *</Label>
              <Input
                id="create-emp-id"
                placeholder="EMP-1006"
                value={fields.employee_code}
                onChange={(e) => updateField('employee_code', e.target.value)}
                disabled={step === 'creating'}
                aria-required="true"
                data-testid="create-emp-id"
              />
            </div>
            <div>
              <Label htmlFor="create-emp-name">Name *</Label>
              <Input
                id="create-emp-name"
                value={fields.name}
                onChange={(e) => updateField('name', e.target.value)}
                disabled={step === 'creating'}
                aria-required="true"
                data-testid="create-emp-name"
              />
            </div>
            <div>
              <Label htmlFor="create-emp-email">Email *</Label>
              <Input
                id="create-emp-email"
                type="email"
                value={fields.email}
                onChange={(e) => updateField('email', e.target.value)}
                disabled={step === 'creating'}
                aria-required="true"
                data-testid="create-emp-email"
              />
            </div>
            <div>
              <Label htmlFor="create-emp-position">Position</Label>
              <Input
                id="create-emp-position"
                value={fields.position}
                onChange={(e) => updateField('position', e.target.value)}
                disabled={step === 'creating'}
                data-testid="create-emp-position"
              />
            </div>
            <div>
              <Label htmlFor="create-emp-department">Department</Label>
              <Input
                id="create-emp-department"
                value={fields.department}
                onChange={(e) => updateField('department', e.target.value)}
                disabled={step === 'creating'}
                data-testid="create-emp-department"
              />
            </div>
            <div>
              <Label htmlFor="create-emp-phone">Phone</Label>
              <Input
                id="create-emp-phone"
                value={fields.phone}
                onChange={(e) => updateField('phone', e.target.value)}
                disabled={step === 'creating'}
                data-testid="create-emp-phone"
              />
            </div>
            <div>
              <Label htmlFor="create-emp-location">Location</Label>
              <Input
                id="create-emp-location"
                value={fields.location}
                onChange={(e) => updateField('location', e.target.value)}
                disabled={step === 'creating'}
                data-testid="create-emp-location"
              />
            </div>
            <div>
              <Label htmlFor="create-emp-manager">Manager Name</Label>
              <Input
                id="create-emp-manager"
                value={fields.manager_name}
                onChange={(e) => updateField('manager_name', e.target.value)}
                disabled={step === 'creating'}
                data-testid="create-emp-manager"
              />
            </div>
            <div>
              <Label htmlFor="create-emp-project">Project</Label>
              <Input
                id="create-emp-project"
                value={fields.project}
                onChange={(e) => updateField('project', e.target.value)}
                disabled={step === 'creating'}
                data-testid="create-emp-project"
              />
            </div>
            <div>
              <Label htmlFor="create-emp-technologies">Technologies</Label>
              <Input
                id="create-emp-technologies"
                placeholder="e.g. React, Python"
                value={fields.technologies}
                onChange={(e) => updateField('technologies', e.target.value)}
                disabled={step === 'creating'}
                data-testid="create-emp-technologies"
              />
            </div>
            <div>
              <Label htmlFor="create-emp-experience">Experience</Label>
              <Input
                id="create-emp-experience"
                placeholder="e.g. 3 years"
                value={fields.experience}
                onChange={(e) => updateField('experience', e.target.value)}
                disabled={step === 'creating'}
                data-testid="create-emp-experience"
              />
            </div>
          </div>

          {duplicate && (
            <div
              className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-300"
              data-testid="create-emp-duplicate-notice"
            >
              An employee with this ID or email already exists.
            </div>
          )}
          {error && <FormErrorText>{error}</FormErrorText>}

          <Button
            className="w-full"
            onClick={() => void handleCreate()}
            disabled={step === 'creating' || !fields.employee_code.trim() || !fields.name.trim() || !fields.email.trim()}
            data-testid="create-employee-btn-submit"
          >
            {step === 'creating' ? 'Creating…' : 'Create Employee'}
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          <h2 id={titleId} className="text-lg font-bold text-gray-900 dark:text-gray-100" data-testid="password-reveal-title">
            {created?.name} was created
          </h2>
          <p className="text-sm text-gray-700 dark:text-gray-300" data-testid="password-reveal-summary">
            Share this password with {created?.name} — it won&apos;t be shown again.
          </p>
          <p
            className="select-all rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 font-mono text-sm text-gray-900 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
            data-testid="password-reveal-value"
          >
            {created?.generated_password}
          </p>
          <button
            type="button"
            onClick={() => void handleCopy()}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
            data-testid="password-reveal-btn-copy"
          >
            Copy
          </button>
          <p className="text-xs text-gray-500 dark:text-gray-400" data-testid="password-reveal-recovery-note">
            Lost this before sharing it? Use &quot;Regenerate Password&quot; from the employee&apos;s row — a lost
            password is a quick fix, not a dead end.
          </p>

          <div className="flex items-center justify-end border-t border-gray-100 pt-2 dark:border-gray-800">
            <button
              type="button"
              onClick={handleDone}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600"
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
