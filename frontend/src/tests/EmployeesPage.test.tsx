import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '@/lib/auth/AuthContext';
import { EmployeesPage } from '@/pages/hr/EmployeesPage';

const navigateMock = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateMock };
});

vi.mock('@/lib/api/authApi', () => ({
  logout: vi.fn().mockResolvedValue(undefined),
  getMe: vi.fn().mockResolvedValue({
    user_id: 'rita-1',
    role: 'HR_ADMIN',
    name: 'Rita the Recruiter',
    email: 'rita@sails.example.com',
  }),
}));

vi.mock('@/lib/api/employeesApi', () => ({
  listEmployees: vi.fn(),
  updateEmployee: vi.fn(),
  deleteOrArchiveEmployee: vi.fn(),
  regeneratePassword: vi.fn(),
}));

import {
  listEmployees,
  updateEmployee,
  deleteOrArchiveEmployee,
  regeneratePassword,
  type EmployeeResponse,
} from '@/lib/api/employeesApi';

function makeEmployee(overrides: Partial<EmployeeResponse> = {}): EmployeeResponse {
  return {
    id: 'emp-1',
    employee_code: 'EMP-0001',
    name: 'Casey Employee',
    email: 'casey@sails.example.com',
    role: 'EMPLOYEE',
    phone: null,
    experience: null,
    technologies: null,
    position: 'Engineer',
    project: null,
    manager_name: null,
    location: null,
    department: 'Engineering',
    created_at: '2026-07-01T00:00:00Z',
    updated_at: '2026-07-01T00:00:00Z',
    archived_at: null,
    has_assignment_history: false,
    ...overrides,
  };
}

function renderPage() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <EmployeesPage />
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('EmployeesPage', () => {
  beforeEach(() => {
    vi.mocked(listEmployees).mockReset();
    vi.mocked(updateEmployee).mockReset();
    vi.mocked(deleteOrArchiveEmployee).mockReset();
    vi.mocked(regeneratePassword).mockReset();
  });

  it('renders one row per fetched employee in Table view by default', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'Casey Employee' }),
      makeEmployee({ id: 'emp-2', name: 'Morgan Mentor', employee_code: 'EMP-0002' }),
    ]);
    renderPage();

    expect(await screen.findByText('Casey Employee')).toBeInTheDocument();
    expect(screen.getByText('Morgan Mentor')).toBeInTheDocument();
    expect(screen.getByTestId('employees-tab-summary-count')).toHaveTextContent('2 employees · 2 active');
    expect(screen.getByTestId('employees-table')).toBeInTheDocument();
  });

  it('shows the empty state when there are no employees', async () => {
    vi.mocked(listEmployees).mockResolvedValue([]);
    renderPage();

    expect(await screen.findByText('No employees yet.')).toBeInTheDocument();
  });

  it('shows a retryable error banner when the fetch fails', async () => {
    vi.mocked(listEmployees).mockRejectedValueOnce(new Error('boom')).mockResolvedValueOnce([]);
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByText(/Couldn't load employees/)).toBeInTheDocument();
    await user.click(screen.getByText('Retry'));

    expect(await screen.findByText('No employees yet.')).toBeInTheDocument();
  });

  it('filters by name search, clearing restores the full list', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'Casey Employee' }),
      makeEmployee({ id: 'emp-2', name: 'Morgan Mentor', employee_code: 'EMP-0002' }),
    ]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Casey Employee');

    await user.type(screen.getByTestId('employees-tab-search-input'), 'Morgan');
    expect(screen.queryByText('Casey Employee')).not.toBeInTheDocument();
    expect(screen.getByText('Morgan Mentor')).toBeInTheDocument();

    await user.clear(screen.getByTestId('employees-tab-search-input'));
    expect(screen.getByText('Casey Employee')).toBeInTheDocument();
    expect(screen.getByText('Morgan Mentor')).toBeInTheDocument();
  });

  it('Department and Position filters compose with search', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'Casey Employee', department: 'Engineering', position: 'Engineer' }),
      makeEmployee({ id: 'emp-2', name: 'Morgan Mentor', employee_code: 'EMP-0002', department: 'Sales', position: 'Rep' }),
    ]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Casey Employee');

    await user.selectOptions(screen.getByTestId('employees-tab-filter-department'), 'Engineering');
    expect(screen.getByText('Casey Employee')).toBeInTheDocument();
    expect(screen.queryByText('Morgan Mentor')).not.toBeInTheDocument();

    await user.selectOptions(screen.getByTestId('employees-tab-filter-department'), '');
    await user.selectOptions(screen.getByTestId('employees-tab-filter-position'), 'Rep');
    expect(screen.queryByText('Casey Employee')).not.toBeInTheDocument();
    expect(screen.getByText('Morgan Mentor')).toBeInTheDocument();
  });

  it('an employee with a blank optional field stays findable via name search', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'No Department Nancy', department: null, position: null }),
    ]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('No Department Nancy');

    await user.type(screen.getByTestId('employees-tab-search-input'), 'Nancy');
    expect(screen.getByText('No Department Nancy')).toBeInTheDocument();
  });

  it('Show archived reveals archived employees with an Archived badge; disabling hides them again', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'Active Casey', archived_at: null }),
      makeEmployee({ id: 'emp-2', name: 'Archived Alex', employee_code: 'EMP-0002', archived_at: '2026-08-01T00:00:00Z' }),
    ]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Active Casey');

    expect(screen.queryByText('Archived Alex')).not.toBeInTheDocument();

    await user.click(screen.getByRole('checkbox', { name: /show archived/i }));
    expect(screen.getByText('Archived Alex')).toBeInTheDocument();
    expect(screen.getAllByText('Archived')).toHaveLength(1);

    await user.click(screen.getByRole('checkbox', { name: /show archived/i }));
    expect(screen.queryByText('Archived Alex')).not.toBeInTheDocument();
  });

  it('Table <-> Card toggle preserves search/filter/page state', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'Casey Employee' }),
      makeEmployee({ id: 'emp-2', name: 'Morgan Mentor', employee_code: 'EMP-0002' }),
    ]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Casey Employee');

    await user.type(screen.getByTestId('employees-tab-search-input'), 'Morgan');
    await user.click(screen.getByLabelText('Card view'));

    expect(screen.getByTestId('employees-grid')).toBeInTheDocument();
    expect(screen.getByTestId('employees-tab-search-input')).toHaveValue('Morgan');
    expect(screen.getByText('Morgan Mentor')).toBeInTheDocument();
    expect(screen.queryByText('Casey Employee')).not.toBeInTheDocument();
  });

  it('paginates at 15/page and a filter change resets to page 1', async () => {
    const many = Array.from({ length: 20 }, (_, i) =>
      makeEmployee({ id: `emp-${i}`, employee_code: `EMP-${String(i).padStart(4, '0')}`, name: `Employee ${i}` })
    );
    vi.mocked(listEmployees).mockResolvedValue(many);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Employee 0');

    expect(screen.getByTestId('employees-table-pagination')).toBeInTheDocument();
    expect(screen.queryByText('Employee 15')).not.toBeInTheDocument();

    await user.click(screen.getByLabelText('Page 2'));
    expect(await screen.findByText('Employee 15')).toBeInTheDocument();
    expect(screen.queryByText('Employee 0')).not.toBeInTheDocument();

    await user.type(screen.getByTestId('employees-tab-search-input'), 'Employee 1');
    expect(await screen.findByText('Employee 1')).toBeInTheDocument();
  });

  it('every row action button carries a descriptive aria-label naming the action and the employee', async () => {
    vi.mocked(listEmployees).mockResolvedValue([makeEmployee({ name: 'Casey Employee' })]);
    renderPage();
    await screen.findByText('Casey Employee');

    expect(screen.getByLabelText('Edit Casey Employee')).toBeInTheDocument();
    expect(screen.getByLabelText('Regenerate password for Casey Employee')).toBeInTheDocument();
    expect(screen.getByLabelText('Delete/Archive Casey Employee')).toBeInTheDocument();
  });

  it('+ New Employee shows a "not available yet" toast (Story 7.2\'s frontend half is still stubbed)', async () => {
    vi.mocked(listEmployees).mockResolvedValue([makeEmployee({ name: 'Casey Employee' })]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Casey Employee');

    await user.click(screen.getByTestId('employees-tab-btn-new-employee'));
    expect(await screen.findByText(/not available yet/i)).toBeInTheDocument();
  });

  it('Story 7.6: clicking a row\'s Regenerate Password button opens the real modal pre-filled with that employee', async () => {
    vi.mocked(listEmployees).mockResolvedValue([makeEmployee({ name: 'Casey Employee' })]);
    vi.mocked(regeneratePassword).mockResolvedValue({
      ...makeEmployee({ name: 'Casey Employee' }),
      generated_password: 'aB3dEfGhJkLm',
    });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Casey Employee');

    await user.click(screen.getByLabelText('Regenerate password for Casey Employee'));

    expect(await screen.findByTestId('regen-password-heading')).toHaveTextContent(
      'Regenerate password for Casey Employee?'
    );

    await user.click(screen.getByTestId('regen-password-btn-confirm'));
    expect(await screen.findByTestId('password-reveal-value')).toHaveTextContent('aB3dEfGhJkLm');

    await user.click(screen.getByTestId('password-reveal-btn-copy'));
    expect(await screen.findByText('Password copied to clipboard')).toBeInTheDocument();
  });

  it('Story 7.5: clicking a row\'s Delete/Archive button opens the real confirm modal pre-filled with that employee', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ name: 'Casey Employee', has_assignment_history: false }),
    ]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Casey Employee');

    await user.click(screen.getByLabelText('Delete/Archive Casey Employee'));

    expect(await screen.findByTestId('delete-employee-heading')).toHaveTextContent('Remove Casey Employee?');
    expect(screen.getByTestId('delete-employee-summary-hard')).toBeInTheDocument();
    expect(screen.getByTestId('delete-employee-btn-confirm')).toHaveTextContent('Remove Employee');
  });

  it('Story 7.5: a completed hard-delete refetches the roster and shows the "removed" toast', async () => {
    const original = makeEmployee({ id: 'emp-1', name: 'Casey Employee', has_assignment_history: false });
    vi.mocked(listEmployees).mockResolvedValueOnce([original]).mockResolvedValueOnce([]);
    vi.mocked(deleteOrArchiveEmployee).mockResolvedValue({ action: 'deleted' });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Casey Employee');

    await user.click(screen.getByLabelText('Delete/Archive Casey Employee'));
    await screen.findByTestId('delete-employee-heading');
    await user.click(screen.getByTestId('delete-employee-btn-confirm'));

    await vi.waitFor(() => expect(screen.queryByTestId('delete-employee-heading')).not.toBeInTheDocument());
    expect(deleteOrArchiveEmployee).toHaveBeenCalledWith('emp-1');
    expect(await screen.findByText("✓ 'Casey Employee' removed.")).toBeInTheDocument();
    expect(listEmployees).toHaveBeenCalledTimes(2);
  });

  it('Story 7.5: a completed archive shows the "archived" toast, driven by the response action not the dialog prediction', async () => {
    // has_assignment_history: false predicted "removed" in the dialog, but
    // the server's response says it archived instead (a race) -- the toast
    // must reflect the response, not the stale prediction.
    const original = makeEmployee({ id: 'emp-1', name: 'Casey Employee', has_assignment_history: false });
    vi.mocked(listEmployees).mockResolvedValue([original]);
    vi.mocked(deleteOrArchiveEmployee).mockResolvedValue({ action: 'archived' });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Casey Employee');

    await user.click(screen.getByLabelText('Delete/Archive Casey Employee'));
    await screen.findByTestId('delete-employee-heading');
    await user.click(screen.getByTestId('delete-employee-btn-confirm'));

    expect(await screen.findByText("✓ 'Casey Employee' archived.")).toBeInTheDocument();
  });

  it('Story 7.5: a failed delete/archive shows an inline error and keeps the modal open', async () => {
    vi.mocked(listEmployees).mockResolvedValue([makeEmployee({ name: 'Casey Employee' })]);
    vi.mocked(deleteOrArchiveEmployee).mockRejectedValue(new Error('boom'));
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Casey Employee');

    await user.click(screen.getByLabelText('Delete/Archive Casey Employee'));
    await screen.findByTestId('delete-employee-heading');
    await user.click(screen.getByTestId('delete-employee-btn-confirm'));

    expect(await screen.findByText(/Couldn't complete this/)).toBeInTheDocument();
    expect(screen.getByTestId('delete-employee-heading')).toBeInTheDocument();
  });

  it('Story 7.4: clicking a row\'s Edit button opens the modal pre-filled with that employee\'s current values', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ name: 'Casey Employee', employee_code: 'EMP-0001', email: 'casey@sails.example.com' }),
    ]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Casey Employee');

    await user.click(screen.getByLabelText('Edit Casey Employee'));

    expect(await screen.findByTestId('edit-employee-header-title')).toHaveTextContent('Edit Casey Employee');
    expect(screen.getByTestId('edit-employee-id-readonly')).toHaveValue('EMP-0001');
    expect(screen.getByTestId('edit-employee-id-readonly')).toBeDisabled();
    expect(screen.getByTestId('edit-employee-name-input')).toHaveValue('Casey Employee');
    expect(screen.getByTestId('edit-employee-email-input')).toHaveValue('casey@sails.example.com');
  });

  it('Story 7.4 AC3: a successful save closes the modal and the roster reflects the new value without a full page reload', async () => {
    const original = makeEmployee({ name: 'Casey Employee', employee_code: 'EMP-0001' });
    vi.mocked(listEmployees)
      .mockResolvedValueOnce([original])
      .mockResolvedValueOnce([{ ...original, name: 'Casey Renamed' }]);
    vi.mocked(updateEmployee).mockResolvedValue({ ...original, name: 'Casey Renamed' });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText('Casey Employee');

    await user.click(screen.getByLabelText('Edit Casey Employee'));
    await screen.findByTestId('edit-employee-header-title');
    await user.click(screen.getByTestId('edit-employee-btn-save'));

    await vi.waitFor(() => expect(screen.queryByTestId('edit-employee-header-title')).not.toBeInTheDocument());
    expect(await screen.findByText('Casey Renamed')).toBeInTheDocument();
    expect(listEmployees).toHaveBeenCalledTimes(2);
  });

  it('AC6: Table view scrolls horizontally within its own container instead of compressing columns', async () => {
    // jsdom can't measure real layout/overflow, so this asserts the classes
    // that produce the scroll behavior (overflow-x-auto wrapper + a table
    // with a fixed min-width) are actually present, rather than claiming the
    // AC is "covered" purely by visual inspection (code review, Story 7.3).
    vi.mocked(listEmployees).mockResolvedValue([makeEmployee({ name: 'Casey Employee' })]);
    renderPage();
    const table = await screen.findByTestId('employees-table');

    expect(table.parentElement).toHaveClass('overflow-x-auto');
    expect(table).toHaveClass('min-w-[720px]');
  });
});
