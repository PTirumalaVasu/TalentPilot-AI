import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EditEmployeeModal } from '@/features/admin/EditEmployeeModal';

vi.mock('@/lib/api/employeesApi', () => ({
  updateEmployee: vi.fn(),
}));

import { updateEmployee, type EmployeeResponse } from '@/lib/api/employeesApi';

function makeEmployee(overrides: Partial<EmployeeResponse> = {}): EmployeeResponse {
  return {
    id: 'emp-1',
    employee_code: 'EMP-0001',
    name: 'Casey Employee',
    first_name: 'Casey',
    last_name: 'Employee',
    email: 'casey@sails.example.com',
    role: 'EMPLOYEE',
    phone: '555-0100',
    experience: '3 years',
    experience_years: 3,
    technologies: 'Python',
    position: 'Engineer',
    project: 'Project Phoenix',
    manager_name: 'Alex Manager',
    location: 'Remote',
    department: 'Engineering',
    created_at: '2026-07-01T00:00:00Z',
    updated_at: '2026-07-01T00:00:00Z',
    archived_at: null,
    has_assignment_history: false,
    days_in_talent_pool: 0,
    ...overrides,
  };
}

describe('EditEmployeeModal', () => {
  beforeEach(() => {
    vi.mocked(updateEmployee).mockReset();
  });

  it('renders Employee ID/Code as read-only and pre-fills every other field from the employee', () => {
    render(
      <EditEmployeeModal open employee={makeEmployee()} onClose={vi.fn()} onSaved={vi.fn()} />
    );

    expect(screen.getByTestId('edit-employee-id-readonly')).toBeDisabled();
    expect(screen.getByTestId('edit-employee-id-readonly')).toHaveValue('EMP-0001');
    expect(screen.getByTestId('edit-employee-first-name-input')).toHaveValue('Casey');
    expect(screen.getByTestId('edit-employee-last-name-input')).toHaveValue('Employee');
    expect(screen.getByTestId('edit-employee-email-input')).toHaveValue('casey@sails.example.com');
    expect(screen.getByTestId('edit-employee-phone-input')).toHaveValue('555-0100');
    expect(screen.getByTestId('edit-employee-experience-input')).toHaveValue('3 years');
    expect(screen.getByTestId('edit-employee-technologies-input')).toHaveValue('Python');
    expect(screen.getByTestId('edit-employee-position-input')).toHaveValue('Engineer');
    expect(screen.getByTestId('edit-employee-project-input')).toHaveValue('Project Phoenix');
    expect(screen.getByTestId('edit-employee-manager-name-input')).toHaveValue('Alex Manager');
    expect(screen.getByTestId('edit-employee-location-input')).toHaveValue('Remote');
    expect(screen.getByTestId('edit-employee-department-input')).toHaveValue('Engineering');
  });

  it('submits edited field values and never includes employee_code in the request payload', async () => {
    const renamed = makeEmployee({ name: 'New Name', first_name: 'New', last_name: 'Name' });
    vi.mocked(updateEmployee).mockResolvedValue(renamed);
    const onSaved = vi.fn();
    const user = userEvent.setup();
    render(
      <EditEmployeeModal open employee={makeEmployee()} onClose={vi.fn()} onSaved={onSaved} />
    );

    await user.clear(screen.getByTestId('edit-employee-first-name-input'));
    await user.type(screen.getByTestId('edit-employee-first-name-input'), 'New');
    await user.clear(screen.getByTestId('edit-employee-last-name-input'));
    await user.type(screen.getByTestId('edit-employee-last-name-input'), 'Name');
    await user.click(screen.getByTestId('edit-employee-btn-save'));

    await vi.waitFor(() => expect(updateEmployee).toHaveBeenCalled());
    const [id, payload] = vi.mocked(updateEmployee).mock.calls[0];
    expect(id).toBe('emp-1');
    expect(payload).not.toHaveProperty('employee_code');
    expect(payload.first_name).toBe('New');
    expect(payload.last_name).toBe('Name');
    expect(payload.email).toBe('casey@sails.example.com');
    expect(onSaved).toHaveBeenCalledWith(renamed);
  });

  it('shows the duplicate-email notice on a 409 and keeps the modal open', async () => {
    vi.mocked(updateEmployee).mockRejectedValue({ response: { status: 409 } });
    const onSaved = vi.fn();
    const user = userEvent.setup();
    render(
      <EditEmployeeModal open employee={makeEmployee()} onClose={vi.fn()} onSaved={onSaved} />
    );

    await user.click(screen.getByTestId('edit-employee-btn-save'));

    expect(await screen.findByTestId('edit-employee-duplicate-notice')).toHaveTextContent(
      'An employee with this email already exists.'
    );
    expect(onSaved).not.toHaveBeenCalled();
  });

  it('shows a generic error message on a non-409 failure', async () => {
    vi.mocked(updateEmployee).mockRejectedValue({ response: { status: 500, data: { message: 'boom' } } });
    const user = userEvent.setup();
    render(
      <EditEmployeeModal open employee={makeEmployee()} onClose={vi.fn()} onSaved={vi.fn()} />
    );

    await user.click(screen.getByTestId('edit-employee-btn-save'));

    expect(await screen.findByText('boom')).toBeInTheDocument();
    expect(screen.queryByTestId('edit-employee-duplicate-notice')).not.toBeInTheDocument();
  });

  it('resets fields and clears stale errors when reopened for a different employee', () => {
    const { rerender } = render(
      <EditEmployeeModal open={false} employee={null} onClose={vi.fn()} onSaved={vi.fn()} />
    );
    rerender(
      <EditEmployeeModal
        open
        employee={makeEmployee({
          id: 'emp-2',
          name: 'Morgan Mentor',
          first_name: 'Morgan',
          last_name: 'Mentor',
          employee_code: 'EMP-0002',
        })}
        onClose={vi.fn()}
        onSaved={vi.fn()}
      />
    );

    expect(screen.getByTestId('edit-employee-id-readonly')).toHaveValue('EMP-0002');
    expect(screen.getByTestId('edit-employee-first-name-input')).toHaveValue('Morgan');
    expect(screen.getByTestId('edit-employee-last-name-input')).toHaveValue('Mentor');
    expect(screen.queryByTestId('edit-employee-duplicate-notice')).not.toBeInTheDocument();
  });

  it('calls onClose when the close button is clicked', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(
      <EditEmployeeModal open employee={makeEmployee()} onClose={onClose} onSaved={vi.fn()} />
    );

    await user.click(screen.getByTestId('edit-employee-btn-close'));
    expect(onClose).toHaveBeenCalled();
  });

  it('renders nothing when closed or when no employee is provided', () => {
    const { container, rerender } = render(
      <EditEmployeeModal open={false} employee={makeEmployee()} onClose={vi.fn()} onSaved={vi.fn()} />
    );
    expect(container).toBeEmptyDOMElement();

    rerender(<EditEmployeeModal open employee={null} onClose={vi.fn()} onSaved={vi.fn()} />);
    expect(container).toBeEmptyDOMElement();
  });
});
