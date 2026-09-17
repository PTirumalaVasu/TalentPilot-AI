import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '@/lib/auth/AuthContext';
import { ThemeProvider } from '@/lib/theme/ThemeContext';
import { EmployeesPage } from '@/pages/hr/EmployeesPage';

// Story 8.1: EmployeesPage renders through HrAppShell, which now renders
// <ThemeToggle> (calls useTheme()) -- the shared window.matchMedia stub
// (frontend/src/tests/setup.ts) covers jsdom's lack of a real implementation
// (code review: previously duplicated here instead of centralized).

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
  createEmployee: vi.fn(),
  updateEmployee: vi.fn(),
  deleteOrArchiveEmployee: vi.fn(),
  regeneratePassword: vi.fn(),
}));

// Story 10.4: the Experience Distribution panel's bucket-count fetch --
// mocked so tests don't hit a real network call for a panel most tests
// don't otherwise care about.
vi.mock('@/lib/api/dashboardApi', () => ({
  dashboardApi: {
    getExperienceDistribution: vi.fn().mockResolvedValue({ buckets: [] }),
  },
}));

import {
  listEmployees,
  createEmployee,
  updateEmployee,
  deleteOrArchiveEmployee,
  regeneratePassword,
  type EmployeeResponse,
} from '@/lib/api/employeesApi';
import { dashboardApi } from '@/lib/api/dashboardApi';

// Story 10.2: splits a legacy-style "First Last" test literal into
// first_name/last_name on the last whitespace token, mirroring the
// production migration/seed split strategy.
function splitName(fullName: string): [string, string] {
  const idx = fullName.lastIndexOf(' ');
  if (idx === -1) return [fullName, 'Employee'];
  return [fullName.slice(0, idx), fullName.slice(idx + 1)];
}

// The grid/card Name cell renders "{Last Name}, {First Name}" -- tests
// assert against this instead of hardcoding the flipped string by hand.
function displayName(fullName: string): string {
  const [first, last] = splitName(fullName);
  return `${last}, ${first}`;
}

function makeEmployee(overrides: Partial<EmployeeResponse> = {}): EmployeeResponse {
  const name = overrides.name ?? 'Casey Employee';
  const [firstName, lastName] = splitName(name);
  return {
    id: 'emp-1',
    employee_code: 'EMP-0001',
    name,
    first_name: firstName,
    last_name: lastName,
    email: 'casey@sails.example.com',
    role: 'EMPLOYEE',
    phone: null,
    experience: null,
    experience_years: null,
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
    days_in_talent_pool: 0,
    ...overrides,
  };
}

function renderPage() {
  return render(
    <MemoryRouter>
      <ThemeProvider>
        <AuthProvider>
          <EmployeesPage />
        </AuthProvider>
      </ThemeProvider>
    </MemoryRouter>
  );
}

describe('EmployeesPage', () => {
  beforeEach(() => {
    vi.mocked(listEmployees).mockReset();
    vi.mocked(updateEmployee).mockReset();
    vi.mocked(deleteOrArchiveEmployee).mockReset();
    vi.mocked(regeneratePassword).mockReset();
    vi.mocked(dashboardApi.getExperienceDistribution).mockReset();
    vi.mocked(dashboardApi.getExperienceDistribution).mockResolvedValue({ buckets: [] });
  });

  it('renders one row per fetched employee in Table view by default', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'Casey Employee' }),
      makeEmployee({ id: 'emp-2', name: 'Morgan Mentor', employee_code: 'EMP-0002' }),
    ]);
    renderPage();

    expect(await screen.findByText(displayName('Casey Employee'))).toBeInTheDocument();
    expect(screen.getByText(displayName('Morgan Mentor'))).toBeInTheDocument();
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
    await screen.findByText(displayName('Casey Employee'));

    await user.type(screen.getByTestId('employees-tab-search-input'), 'Morgan');
    expect(screen.queryByText(displayName('Casey Employee'))).not.toBeInTheDocument();
    expect(screen.getByText(displayName('Morgan Mentor'))).toBeInTheDocument();

    await user.clear(screen.getByTestId('employees-tab-search-input'));
    expect(screen.getByText(displayName('Casey Employee'))).toBeInTheDocument();
    expect(screen.getByText(displayName('Morgan Mentor'))).toBeInTheDocument();
  });

  it('Department and Position filters compose with search', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'Casey Employee', department: 'Engineering', position: 'Engineer' }),
      makeEmployee({ id: 'emp-2', name: 'Morgan Mentor', employee_code: 'EMP-0002', department: 'Sales', position: 'Rep' }),
    ]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('Casey Employee'));

    await user.selectOptions(screen.getByTestId('employees-tab-filter-department'), 'Engineering');
    expect(screen.getByText(displayName('Casey Employee'))).toBeInTheDocument();
    expect(screen.queryByText(displayName('Morgan Mentor'))).not.toBeInTheDocument();

    await user.selectOptions(screen.getByTestId('employees-tab-filter-department'), '');
    await user.selectOptions(screen.getByTestId('employees-tab-filter-position'), 'Rep');
    expect(screen.queryByText(displayName('Casey Employee'))).not.toBeInTheDocument();
    expect(screen.getByText(displayName('Morgan Mentor'))).toBeInTheDocument();
  });

  it('an employee with a blank optional field stays findable via name search', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'No Department Nancy', department: null, position: null }),
    ]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('No Department Nancy'));

    await user.type(screen.getByTestId('employees-tab-search-input'), 'Nancy');
    expect(screen.getByText(displayName('No Department Nancy'))).toBeInTheDocument();
  });

  it('Show archived reveals archived employees with an Archived badge; disabling hides them again', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'Active Casey', archived_at: null }),
      makeEmployee({ id: 'emp-2', name: 'Archived Alex', employee_code: 'EMP-0002', archived_at: '2026-08-01T00:00:00Z' }),
    ]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('Active Casey'));

    expect(screen.queryByText(displayName('Archived Alex'))).not.toBeInTheDocument();

    await user.click(screen.getByRole('checkbox', { name: /show archived/i }));
    expect(screen.getByText(displayName('Archived Alex'))).toBeInTheDocument();
    expect(screen.getAllByText('Archived')).toHaveLength(1);

    await user.click(screen.getByRole('checkbox', { name: /show archived/i }));
    expect(screen.queryByText(displayName('Archived Alex'))).not.toBeInTheDocument();
  });

  it('Table <-> Card toggle preserves search/filter/page state', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'Casey Employee' }),
      makeEmployee({ id: 'emp-2', name: 'Morgan Mentor', employee_code: 'EMP-0002' }),
    ]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('Casey Employee'));

    await user.type(screen.getByTestId('employees-tab-search-input'), 'Morgan');
    await user.click(screen.getByLabelText('Card view'));

    expect(screen.getByTestId('employees-grid')).toBeInTheDocument();
    expect(screen.getByTestId('employees-tab-search-input')).toHaveValue('Morgan');
    expect(screen.getByText(displayName('Morgan Mentor'))).toBeInTheDocument();
    expect(screen.queryByText(displayName('Casey Employee'))).not.toBeInTheDocument();
  });

  it('paginates at 15/page and a filter change resets to page 1', async () => {
    const many = Array.from({ length: 20 }, (_, i) =>
      makeEmployee({ id: `emp-${i}`, employee_code: `EMP-${String(i).padStart(4, '0')}`, name: `Employee ${i}` })
    );
    vi.mocked(listEmployees).mockResolvedValue(many);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('Employee 0'));

    expect(screen.getByTestId('employees-table-pagination')).toBeInTheDocument();
    expect(screen.queryByText(displayName('Employee 15'))).not.toBeInTheDocument();

    await user.click(screen.getByLabelText('Page 2'));
    expect(await screen.findByText(displayName('Employee 15'))).toBeInTheDocument();
    expect(screen.queryByText(displayName('Employee 0'))).not.toBeInTheDocument();

    await user.type(screen.getByTestId('employees-tab-search-input'), 'Employee 1');
    expect(await screen.findByText(displayName('Employee 1'))).toBeInTheDocument();
  });

  it('every row action button carries a descriptive aria-label naming the action and the employee', async () => {
    vi.mocked(listEmployees).mockResolvedValue([makeEmployee({ name: 'Casey Employee' })]);
    renderPage();
    await screen.findByText(displayName('Casey Employee'));

    expect(screen.getByLabelText('Edit Casey Employee')).toBeInTheDocument();
    expect(screen.getByLabelText('Regenerate password for Casey Employee')).toBeInTheDocument();
    expect(screen.getByLabelText('Delete Casey Employee')).toBeInTheDocument();
  });

  it('Story 10.3 (AC1): an employee with assignment history gets an Archive icon/label, not Delete', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ name: 'Casey Employee', has_assignment_history: true }),
    ]);
    renderPage();
    await screen.findByText(displayName('Casey Employee'));

    expect(screen.getByLabelText('Archive Casey Employee')).toBeInTheDocument();
    expect(screen.queryByLabelText('Delete Casey Employee')).not.toBeInTheDocument();
  });

  it('Story 10.3 (AC4): Delete/Archive render as permanently-tinted pills, distinct from Edit/Regenerate\'s neutral hover-only style', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'Casey Employee', has_assignment_history: false }),
      makeEmployee({ id: 'emp-2', name: 'Morgan Mentor', employee_code: 'EMP-0002', has_assignment_history: true }),
    ]);
    renderPage();
    await screen.findByText(displayName('Casey Employee'));

    expect(screen.getByLabelText('Delete Casey Employee')).toHaveClass('bg-red-50');
    expect(screen.getByLabelText('Archive Morgan Mentor')).toHaveClass('bg-amber-50');
    expect(screen.getByLabelText('Edit Casey Employee')).not.toHaveClass('bg-red-50', 'bg-amber-50');
    expect(screen.getByLabelText('Regenerate password for Casey Employee')).not.toHaveClass('bg-red-50', 'bg-amber-50');
  });

  it('Story 10.3 (AC2): clicking the Archive icon opens the same confirm modal as Delete, unchanged behavior', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'Casey Employee', has_assignment_history: true }),
    ]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('Casey Employee'));

    await user.click(screen.getByLabelText('Archive Casey Employee'));

    expect(await screen.findByTestId('delete-employee-heading')).toHaveTextContent('Remove Casey Employee?');
    expect(screen.getByTestId('delete-employee-summary-archive')).toBeInTheDocument();
    expect(screen.getByTestId('delete-employee-btn-confirm')).toHaveTextContent('Archive Employee');
  });

  it('Story 7.2: + New Employee creates a record, reveals the password once, then refetches and toasts', async () => {
    const original = makeEmployee({ id: 'emp-1', name: 'Casey Employee' });
    const created = makeEmployee({ id: 'emp-2', name: 'Jamie Hire', employee_code: 'EMP-1006' });
    vi.mocked(listEmployees).mockResolvedValueOnce([original]).mockResolvedValueOnce([original, created]);
    vi.mocked(createEmployee).mockResolvedValue({ ...created, generated_password: 'aB3dEfGhJkLm' });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('Casey Employee'));

    await user.click(screen.getByTestId('employees-tab-btn-new-employee'));
    expect(await screen.findByTestId('create-employee-modal-title')).toHaveTextContent('New Employee');

    await user.type(screen.getByTestId('create-emp-id'), 'EMP-1006');
    await user.type(screen.getByTestId('create-emp-first-name'), 'Jamie');
    await user.type(screen.getByTestId('create-emp-last-name'), 'Hire');
    await user.type(screen.getByTestId('create-emp-email'), 'jamie@sails.example.com');
    await user.click(screen.getByTestId('create-employee-btn-submit'));

    expect(await screen.findByTestId('password-reveal-value')).toHaveTextContent('aB3dEfGhJkLm');
    expect(createEmployee).toHaveBeenCalledWith(
      expect.objectContaining({
        employee_code: 'EMP-1006',
        first_name: 'Jamie',
        last_name: 'Hire',
        email: 'jamie@sails.example.com',
      })
    );

    await user.click(screen.getByTestId('password-reveal-btn-done'));

    await vi.waitFor(() => expect(screen.queryByTestId('password-reveal-value')).not.toBeInTheDocument());
    expect(await screen.findByText("✓ 'Jamie Hire' created.")).toBeInTheDocument();
    expect(await screen.findByText(displayName('Jamie Hire'))).toBeInTheDocument();
    expect(listEmployees).toHaveBeenCalledTimes(2);
  });

  it('Story 7.2: a duplicate ID/email 409 shows an inline notice, not the generic error banner', async () => {
    vi.mocked(listEmployees).mockResolvedValue([makeEmployee({ name: 'Casey Employee' })]);
    vi.mocked(createEmployee).mockRejectedValue({ response: { status: 409 } });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('Casey Employee'));

    await user.click(screen.getByTestId('employees-tab-btn-new-employee'));
    await user.type(screen.getByTestId('create-emp-id'), 'EMP-0001');
    await user.type(screen.getByTestId('create-emp-first-name'), 'Duplicate');
    await user.type(screen.getByTestId('create-emp-last-name'), 'Hire');
    await user.type(screen.getByTestId('create-emp-email'), 'casey@sails.example.com');
    await user.click(screen.getByTestId('create-employee-btn-submit'));

    expect(await screen.findByTestId('create-emp-duplicate-notice')).toHaveTextContent(
      'An employee with this ID or email already exists.'
    );
  });

  it('Story 7.6: clicking a row\'s Regenerate Password button opens the real modal pre-filled with that employee', async () => {
    vi.mocked(listEmployees).mockResolvedValue([makeEmployee({ name: 'Casey Employee' })]);
    vi.mocked(regeneratePassword).mockResolvedValue({
      ...makeEmployee({ name: 'Casey Employee' }),
      generated_password: 'aB3dEfGhJkLm',
    });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('Casey Employee'));

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
    await screen.findByText(displayName('Casey Employee'));

    await user.click(screen.getByLabelText('Delete Casey Employee'));

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
    await screen.findByText(displayName('Casey Employee'));

    await user.click(screen.getByLabelText('Delete Casey Employee'));
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
    await screen.findByText(displayName('Casey Employee'));

    await user.click(screen.getByLabelText('Delete Casey Employee'));
    await screen.findByTestId('delete-employee-heading');
    await user.click(screen.getByTestId('delete-employee-btn-confirm'));

    expect(await screen.findByText("✓ 'Casey Employee' archived.")).toBeInTheDocument();
  });

  it('Story 7.5: a failed delete/archive shows an inline error and keeps the modal open', async () => {
    vi.mocked(listEmployees).mockResolvedValue([makeEmployee({ name: 'Casey Employee' })]);
    vi.mocked(deleteOrArchiveEmployee).mockRejectedValue(new Error('boom'));
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('Casey Employee'));

    await user.click(screen.getByLabelText('Delete Casey Employee'));
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
    await screen.findByText(displayName('Casey Employee'));

    await user.click(screen.getByLabelText('Edit Casey Employee'));

    expect(await screen.findByTestId('edit-employee-header-title')).toHaveTextContent('Edit Casey Employee');
    expect(screen.getByTestId('edit-employee-id-readonly')).toHaveValue('EMP-0001');
    expect(screen.getByTestId('edit-employee-id-readonly')).toBeDisabled();
    expect(screen.getByTestId('edit-employee-first-name-input')).toHaveValue('Casey');
    expect(screen.getByTestId('edit-employee-last-name-input')).toHaveValue('Employee');
    expect(screen.getByTestId('edit-employee-email-input')).toHaveValue('casey@sails.example.com');
  });

  it('Story 7.4 AC3: a successful save closes the modal and the roster reflects the new value without a full page reload', async () => {
    const original = makeEmployee({ name: 'Casey Employee', employee_code: 'EMP-0001' });
    const renamed = { ...original, name: 'Casey Renamed', first_name: 'Casey', last_name: 'Renamed' };
    vi.mocked(listEmployees).mockResolvedValueOnce([original]).mockResolvedValueOnce([renamed]);
    vi.mocked(updateEmployee).mockResolvedValue(renamed);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('Casey Employee'));

    await user.click(screen.getByLabelText('Edit Casey Employee'));
    await screen.findByTestId('edit-employee-header-title');
    await user.click(screen.getByTestId('edit-employee-btn-save'));

    await vi.waitFor(() => expect(screen.queryByTestId('edit-employee-header-title')).not.toBeInTheDocument());
    expect(await screen.findByText(displayName('Casey Renamed'))).toBeInTheDocument();
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
    expect(table).toHaveClass('min-w-[1080px]');
  });

  it('Story 10.2: renders Project/Location/Technologies columns and a plain Days in Talent Pool value under the threshold', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({
        name: 'Casey Employee',
        project: 'Project Phoenix',
        location: 'Remote',
        technologies: 'Python, React',
        days_in_talent_pool: 10,
      }),
    ]);
    renderPage();
    await screen.findByText(displayName('Casey Employee'));

    expect(screen.getByText('Project Phoenix')).toBeInTheDocument();
    expect(screen.getByText('Remote')).toBeInTheDocument();
    expect(screen.getByText('Python, React')).toBeInTheDocument();
    expect(screen.getByText('10d')).toBeInTheDocument();
  });

  it('Story 10.2 (FR-35): flags Days in Talent Pool past the 90-day threshold with an icon and red text', async () => {
    vi.mocked(listEmployees).mockResolvedValue([makeEmployee({ name: 'Casey Employee', days_in_talent_pool: 91 })]);
    renderPage();
    await screen.findByText(displayName('Casey Employee'));

    const flagged = screen.getByText(/91d/);
    expect(flagged).toHaveTextContent('⚠ 91d');
    expect(flagged).toHaveClass('text-red-600');
  });

  it('Story 10.2 (FR-35): does not flag Days in Talent Pool at exactly the 90-day threshold', async () => {
    vi.mocked(listEmployees).mockResolvedValue([makeEmployee({ name: 'Casey Employee', days_in_talent_pool: 90 })]);
    renderPage();
    await screen.findByText(displayName('Casey Employee'));

    const unflagged = screen.getByText('90d');
    expect(unflagged).not.toHaveTextContent('⚠');
    expect(unflagged).not.toHaveClass('text-red-600');
  });

  it('Story 10.2 AC5: the search box also matches Project, Location, and Technologies', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'Casey Employee', project: 'Project Phoenix', location: 'Austin', technologies: 'Go' }),
      makeEmployee({ id: 'emp-2', name: 'Morgan Mentor', employee_code: 'EMP-0002', project: 'Atlas', location: 'Remote', technologies: 'Python, React' }),
    ]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('Casey Employee'));

    await user.type(screen.getByTestId('employees-tab-search-input'), 'Phoenix');
    expect(screen.getByText(displayName('Casey Employee'))).toBeInTheDocument();
    expect(screen.queryByText(displayName('Morgan Mentor'))).not.toBeInTheDocument();

    await user.clear(screen.getByTestId('employees-tab-search-input'));
    await user.type(screen.getByTestId('employees-tab-search-input'), 'remote');
    expect(screen.queryByText(displayName('Casey Employee'))).not.toBeInTheDocument();
    expect(screen.getByText(displayName('Morgan Mentor'))).toBeInTheDocument();

    await user.clear(screen.getByTestId('employees-tab-search-input'));
    await user.type(screen.getByTestId('employees-tab-search-input'), 'Python');
    expect(screen.queryByText(displayName('Casey Employee'))).not.toBeInTheDocument();
    expect(screen.getByText(displayName('Morgan Mentor'))).toBeInTheDocument();
  });

  it("Story 10.2 AC6: the acting HR Admin's own row shows a blank Days in Talent Pool and a (you) label instead of Delete/Archive", async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({
        id: 'rita-1',
        name: 'Sails Admin',
        days_in_talent_pool: 500,
        project: 'Internal',
        location: 'HQ',
        technologies: 'N/A',
      }),
      makeEmployee({
        id: 'emp-2',
        name: 'Morgan Mentor',
        employee_code: 'EMP-0002',
        project: 'Project Atlas',
        location: 'Austin',
        technologies: 'Go',
        days_in_talent_pool: 5,
      }),
    ]);
    renderPage();
    await screen.findByText(displayName('Sails Admin'));

    expect(screen.getByText('—')).toBeInTheDocument();
    expect(screen.getByTestId('employees-row-you-rita-1')).toHaveTextContent('(you)');
    expect(screen.queryByLabelText('Delete Sails Admin')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Archive Sails Admin')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Edit Sails Admin')).toBeInTheDocument();
    expect(screen.getByLabelText('Regenerate password for Sails Admin')).toBeInTheDocument();
  });

  it('Story 10.2 AC6: the acting HR Admin\'s own row drops out once a filter is active, but stays in the unfiltered view', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'rita-1', name: 'Sails Admin' }),
      makeEmployee({ id: 'emp-2', name: 'Morgan Mentor', employee_code: 'EMP-0002' }),
    ]);
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('Sails Admin'));

    await user.type(screen.getByTestId('employees-tab-search-input'), 'Morgan');
    expect(screen.queryByText(displayName('Sails Admin'))).not.toBeInTheDocument();
    expect(screen.getByText(displayName('Morgan Mentor'))).toBeInTheDocument();

    await user.clear(screen.getByTestId('employees-tab-search-input'));
    expect(screen.getByText(displayName('Sails Admin'))).toBeInTheDocument();
  });

  // --- Story 10.4: Experience Distribution panel (FR-36) ---------------------

  // Code review (Story 10.4): the real, canonical 7-bucket set (matching
  // backend/app/dashboard/service.py::EXPERIENCE_BUCKETS exactly) -- the
  // original tests only ever mocked a subset, never exercising the full
  // bucket set these components actually render against in production.
  const FULL_BUCKET_SET = [
    { label: '0–4 yrs', min_years: 0, max_years: 4, count: 1 },
    { label: '5–7 yrs', min_years: 5, max_years: 7, count: 0 },
    { label: '8–9 yrs', min_years: 8, max_years: 9, count: 1 },
    { label: '10–11 yrs', min_years: 10, max_years: 11, count: 0 },
    { label: '12–14 yrs', min_years: 12, max_years: 14, count: 0 },
    { label: '15–19 yrs', min_years: 15, max_years: 19, count: 0 },
    { label: '20+ yrs', min_years: 20, max_years: null, count: 0 },
  ];

  it('renders a bucket chip per bucket with its server-computed count, and clicking one filters the roster', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'Casey Employee', experience_years: 3 }),
      makeEmployee({ id: 'emp-2', name: 'Morgan Mentor', employee_code: 'EMP-0002', experience_years: 9 }),
    ]);
    vi.mocked(dashboardApi.getExperienceDistribution).mockResolvedValue({ buckets: FULL_BUCKET_SET });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('Casey Employee'));

    // All 7 buckets render, in order, with their server-computed counts.
    expect(screen.getByTestId('experience-distribution-bucket-0')).toHaveTextContent('0–4 yrs (1)');
    expect(screen.getByTestId('experience-distribution-bucket-2')).toHaveTextContent('8–9 yrs (1)');
    expect(screen.getByTestId('experience-distribution-bucket-6')).toHaveTextContent('20+ yrs (0)');
    expect(screen.queryByTestId('experience-distribution-clear')).not.toBeInTheDocument();

    await user.click(screen.getByTestId('experience-distribution-bucket-2'));
    expect(screen.queryByText(displayName('Casey Employee'))).not.toBeInTheDocument();
    expect(screen.getByText(displayName('Morgan Mentor'))).toBeInTheDocument();
    expect(screen.getByTestId('experience-distribution-bucket-2')).toHaveAttribute('aria-pressed', 'true');

    await user.click(screen.getByTestId('experience-distribution-clear'));
    expect(screen.getByText(displayName('Casey Employee'))).toBeInTheDocument();
    expect(screen.getByText(displayName('Morgan Mentor'))).toBeInTheDocument();
    expect(screen.queryByTestId('experience-distribution-clear')).not.toBeInTheDocument();
  });

  it('an Employee with no experience_years is excluded when a bucket filter is active', async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'No Experience Nancy', experience_years: null }),
      makeEmployee({ id: 'emp-2', name: 'Morgan Mentor', employee_code: 'EMP-0002', experience_years: 3 }),
    ]);
    vi.mocked(dashboardApi.getExperienceDistribution).mockResolvedValue({ buckets: FULL_BUCKET_SET });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('No Experience Nancy'));

    await user.click(screen.getByTestId('experience-distribution-bucket-0'));
    expect(screen.queryByText(displayName('No Experience Nancy'))).not.toBeInTheDocument();
    expect(screen.getByText(displayName('Morgan Mentor'))).toBeInTheDocument();
  });

  it('an archived Employee matching the active bucket stays excluded even with "Show archived" on (code review)', async () => {
    // Code review (Story 10.4): the bucket's own displayed count comes from
    // the active roster only (server-side) -- an archived row matching the
    // same range must never appear in the filtered list, even if the HR
    // Admin has separately toggled "Show archived" on, or the list and the
    // chip's count would disagree.
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'emp-1', name: 'Archived Alex', employee_code: 'EMP-0002', experience_years: 3, archived_at: '2026-08-01T00:00:00Z' }),
      makeEmployee({ id: 'emp-2', name: 'Morgan Mentor', experience_years: 3 }),
    ]);
    vi.mocked(dashboardApi.getExperienceDistribution).mockResolvedValue({ buckets: FULL_BUCKET_SET });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('Morgan Mentor'));

    await user.click(screen.getByRole('checkbox', { name: /show archived/i }));
    await user.click(screen.getByTestId('experience-distribution-bucket-0'));

    expect(screen.queryByText(displayName('Archived Alex'))).not.toBeInTheDocument();
    expect(screen.getByText(displayName('Morgan Mentor'))).toBeInTheDocument();
  });

  it("Story 10.2 AC6 (extended by 10.4): the acting HR Admin's own row drops out once a bucket filter is active", async () => {
    vi.mocked(listEmployees).mockResolvedValue([
      makeEmployee({ id: 'rita-1', name: 'Sails Admin', experience_years: null }),
      makeEmployee({ id: 'emp-2', name: 'Morgan Mentor', employee_code: 'EMP-0002', experience_years: 3 }),
    ]);
    vi.mocked(dashboardApi.getExperienceDistribution).mockResolvedValue({ buckets: FULL_BUCKET_SET });
    const user = userEvent.setup();
    renderPage();
    await screen.findByText(displayName('Sails Admin'));

    await user.click(screen.getByTestId('experience-distribution-bucket-0'));
    expect(screen.queryByText(displayName('Sails Admin'))).not.toBeInTheDocument();
    expect(screen.getByText(displayName('Morgan Mentor'))).toBeInTheDocument();

    await user.click(screen.getByTestId('experience-distribution-clear'));
    expect(screen.getByText(displayName('Sails Admin'))).toBeInTheDocument();
  });
});
