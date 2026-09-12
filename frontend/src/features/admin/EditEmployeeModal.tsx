import { useEffect, useId, useRef, useState } from 'react';
import { Dialog } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { FormErrorText } from '@/components/ui/form-error-text';
import { updateEmployee, type EmployeeResponse } from '@/lib/api/employeesApi';

export interface EditEmployeeModalProps {
  open: boolean;
  employee: EmployeeResponse | null;
  onClose: () => void;
  onSaved: (updated: EmployeeResponse) => void;
}

function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response?: { data?: { message?: string } } }).response;
    if (response?.data?.message) return response.data.message;
  }
  return fallback;
}

interface ConflictError {
  response?: { status?: number };
}

const EMPTY_FIELDS = {
  name: '',
  email: '',
  phone: '',
  experience: '',
  technologies: '',
  position: '',
  project: '',
  manager_name: '',
  location: '',
  department: '',
};

/**
 * The "Edit Employee" panel (Story 7.4, FR-26). Employee ID/Code renders
 * read-only (UX-DR39) -- every other field from Story 7.2's field set is
 * editable, regardless of Assignment history (no lock, unlike a Skill's
 * identity-lock, FR-21/22). Mirrors NewSkillModal.tsx's Dialog/requestIdRef/
 * 409-branching pattern directly.
 */
export function EditEmployeeModal({ open, employee, onClose, onSaved }: EditEmployeeModalProps) {
  const titleId = useId();
  const [fields, setFields] = useState(EMPTY_FIELDS);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duplicateEmail, setDuplicateEmail] = useState(false);
  // Invalidates any in-flight updateEmployee() request across open/close
  // transitions -- mirrors NewSkillModal.tsx's identical guard.
  const requestIdRef = useRef(0);

  useEffect(() => {
    requestIdRef.current += 1;
    if (!open || !employee) return;
    setFields({
      name: employee.name,
      email: employee.email,
      phone: employee.phone ?? '',
      experience: employee.experience ?? '',
      technologies: employee.technologies ?? '',
      position: employee.position ?? '',
      project: employee.project ?? '',
      manager_name: employee.manager_name ?? '',
      location: employee.location ?? '',
      department: employee.department ?? '',
    });
    setError(null);
    setDuplicateEmail(false);
    setSubmitting(false);
  }, [open, employee]);

  function updateField(field: keyof typeof EMPTY_FIELDS, value: string) {
    setFields((prev) => ({ ...prev, [field]: value }));
    if (field === 'email') setDuplicateEmail(false);
  }

  async function handleSave() {
    if (!employee) return;
    const trimmedName = fields.name.trim();
    const trimmedEmail = fields.email.trim();
    if (!trimmedName || !trimmedEmail) return;

    const requestIdAtSubmit = requestIdRef.current;
    setSubmitting(true);
    setError(null);
    setDuplicateEmail(false);
    try {
      const updated = await updateEmployee(employee.id, {
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
      onSaved(updated);
    } catch (err) {
      if (requestIdRef.current !== requestIdAtSubmit) return;
      const conflictErr = err as ConflictError;
      if (conflictErr.response?.status === 409) {
        setDuplicateEmail(true);
      } else {
        setError(extractErrorMessage(err, "Couldn't save this employee — Try again"));
      }
    } finally {
      if (requestIdRef.current === requestIdAtSubmit) setSubmitting(false);
    }
  }

  if (!open || !employee) return null;

  return (
    <Dialog open={open} onClose={onClose} titleId={titleId} className="max-w-lg">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 id={titleId} className="text-lg font-bold text-gray-900" data-testid="edit-employee-header-title">
            Edit {employee.name}
          </h2>
          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
            className="text-xl leading-none text-gray-400 hover:text-gray-600"
            data-testid="edit-employee-btn-close"
          >
            ✕
          </button>
        </div>

        <div>
          <Label htmlFor="edit-employee-id-readonly">Employee ID/Code</Label>
          <Input id="edit-employee-id-readonly" value={employee.employee_code} disabled data-testid="edit-employee-id-readonly" />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="edit-employee-name-input">Name</Label>
            <Input
              id="edit-employee-name-input"
              value={fields.name}
              onChange={(e) => updateField('name', e.target.value)}
              disabled={submitting}
              data-testid="edit-employee-name-input"
            />
          </div>
          <div>
            <Label htmlFor="edit-employee-email-input">Email</Label>
            <Input
              id="edit-employee-email-input"
              type="email"
              value={fields.email}
              onChange={(e) => updateField('email', e.target.value)}
              disabled={submitting}
              data-testid="edit-employee-email-input"
            />
          </div>
          <div>
            <Label htmlFor="edit-employee-phone-input">Phone</Label>
            <Input
              id="edit-employee-phone-input"
              value={fields.phone}
              onChange={(e) => updateField('phone', e.target.value)}
              disabled={submitting}
              data-testid="edit-employee-phone-input"
            />
          </div>
          <div>
            <Label htmlFor="edit-employee-experience-input">Experience</Label>
            <Input
              id="edit-employee-experience-input"
              value={fields.experience}
              onChange={(e) => updateField('experience', e.target.value)}
              disabled={submitting}
              data-testid="edit-employee-experience-input"
            />
          </div>
          <div>
            <Label htmlFor="edit-employee-technologies-input">Technologies</Label>
            <Input
              id="edit-employee-technologies-input"
              value={fields.technologies}
              onChange={(e) => updateField('technologies', e.target.value)}
              disabled={submitting}
              data-testid="edit-employee-technologies-input"
            />
          </div>
          <div>
            <Label htmlFor="edit-employee-position-input">Position</Label>
            <Input
              id="edit-employee-position-input"
              value={fields.position}
              onChange={(e) => updateField('position', e.target.value)}
              disabled={submitting}
              data-testid="edit-employee-position-input"
            />
          </div>
          <div>
            <Label htmlFor="edit-employee-project-input">Project</Label>
            <Input
              id="edit-employee-project-input"
              value={fields.project}
              onChange={(e) => updateField('project', e.target.value)}
              disabled={submitting}
              data-testid="edit-employee-project-input"
            />
          </div>
          <div>
            <Label htmlFor="edit-employee-manager-name-input">Manager Name</Label>
            <Input
              id="edit-employee-manager-name-input"
              value={fields.manager_name}
              onChange={(e) => updateField('manager_name', e.target.value)}
              disabled={submitting}
              data-testid="edit-employee-manager-name-input"
            />
          </div>
          <div>
            <Label htmlFor="edit-employee-location-input">Location</Label>
            <Input
              id="edit-employee-location-input"
              value={fields.location}
              onChange={(e) => updateField('location', e.target.value)}
              disabled={submitting}
              data-testid="edit-employee-location-input"
            />
          </div>
          <div>
            <Label htmlFor="edit-employee-department-input">Department</Label>
            <Input
              id="edit-employee-department-input"
              value={fields.department}
              onChange={(e) => updateField('department', e.target.value)}
              disabled={submitting}
              data-testid="edit-employee-department-input"
            />
          </div>
        </div>

        {duplicateEmail && (
          <div
            className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800"
            data-testid="edit-employee-duplicate-notice"
          >
            An employee with this email already exists.
          </div>
        )}
        {error && <FormErrorText>{error}</FormErrorText>}

        <Button
          className="w-full"
          onClick={handleSave}
          disabled={submitting || !fields.name.trim() || !fields.email.trim()}
          data-testid="edit-employee-btn-save"
        >
          {submitting ? 'Saving…' : 'Save changes'}
        </Button>
      </div>
    </Dialog>
  );
}
