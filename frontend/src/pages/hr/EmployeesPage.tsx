/** Employees tab (Story 7.3): roster view with search/filter/archived-toggle,
 * Table/Card view toggle, and 15/page pagination. All filtering/pagination is
 * client-side over one fetched roster (Scope Note 2) -- mirrors
 * SkillsPage.tsx's fetch-once-then-filter shape (Story 6.10).
 *
 * Row/card action icons (Edit, Regenerate Password, Delete/Archive -- all
 * three now wired, Stories 7.4/7.5/7.6) and "+ New Employee" render per the
 * UX spec (aria-labels required, AC5). "+ New Employee" remains stubbed --
 * its modal belongs to Story 7.2's still-unbuilt frontend half. */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { HrAppShell } from '@/components/layout/HrAppShell';
import { Toast } from '@/components/ui/toast';
import { listEmployees, type EmployeeResponse } from '@/lib/api/employeesApi';
import { EditEmployeeModal } from '@/features/admin/EditEmployeeModal';
import { DeleteArchiveEmployeeModal } from '@/features/admin/DeleteArchiveEmployeeModal';
import { RegeneratePasswordModal } from '@/features/admin/RegeneratePasswordModal';

const PAGE_SIZE = 15;
const NOT_AVAILABLE_YET = 'Not available yet — coming in a future story.';

function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response?: { data?: { message?: string } } }).response;
    if (response?.data?.message) return response.data.message;
  }
  return fallback;
}

function distinctSorted(values: (string | null)[]): string[] {
  return [...new Set(values.filter((v): v is string => Boolean(v)))].sort();
}

function StatusBadge({ archived }: { archived: boolean }) {
  return (
    <span
      className={
        'rounded-full border px-2 py-0.5 text-xs font-medium ' +
        (archived
          ? 'border-gray-200 bg-gray-100 text-gray-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400'
          : 'border-green-200 bg-green-50 text-green-700 dark:border-green-900 dark:bg-green-950 dark:text-green-400')
      }
    >
      {archived ? 'Archived' : 'Active'}
    </span>
  );
}

function RowActions({
  employee,
  onEdit,
  onRegeneratePassword,
  onDeleteOrArchive,
}: {
  employee: EmployeeResponse;
  onEdit: (employee: EmployeeResponse) => void;
  onRegeneratePassword: (employee: EmployeeResponse) => void;
  onDeleteOrArchive: (employee: EmployeeResponse) => void;
}) {
  return (
    <>
      <button
        type="button"
        onClick={() => onEdit(employee)}
        aria-label={`Edit ${employee.name}`}
        title="Edit"
        className="mr-2 px-1 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
      >
        ✎
      </button>
      <button
        type="button"
        onClick={() => onRegeneratePassword(employee)}
        aria-label={`Regenerate password for ${employee.name}`}
        title="Regenerate Password"
        className="mr-2 px-1 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
      >
        ⚿
      </button>
      <button
        type="button"
        onClick={() => onDeleteOrArchive(employee)}
        aria-label={`Delete/Archive ${employee.name}`}
        title="Delete/Archive"
        className="px-1 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
      >
        ✕
      </button>
    </>
  );
}

export function EmployeesPage() {
  const [employees, setEmployees] = useState<EmployeeResponse[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const requestIdRef = useRef(0);

  const [search, setSearch] = useState('');
  const [department, setDepartment] = useState('');
  const [position, setPosition] = useState('');
  const [showArchived, setShowArchived] = useState(false);
  const [view, setView] = useState<'table' | 'card'>('table');
  const [page, setPage] = useState(1);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [editingEmployee, setEditingEmployee] = useState<EmployeeResponse | null>(null);
  const [regeneratingEmployee, setRegeneratingEmployee] = useState<EmployeeResponse | null>(null);
  const [deletingEmployee, setDeletingEmployee] = useState<EmployeeResponse | null>(null);

  const refetch = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    setLoadError(null);
    try {
      const result = await listEmployees();
      if (requestIdRef.current !== requestId) return;
      setEmployees(result);
    } catch (err) {
      if (requestIdRef.current !== requestId) return;
      setLoadError(extractErrorMessage(err, "Couldn't load employees. Try again."));
    }
  }, []);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  function showUnavailableToast() {
    setToastMessage(NOT_AVAILABLE_YET);
  }

  // Story 7.4 AC3: a successful save refetches the roster (no full page
  // reload) rather than patching local state -- reuses the page's existing
  // refetch(), matching Story 7.3's already-established precedent.
  function handleEmployeeSaved() {
    setEditingEmployee(null);
    void refetch();
  }

  // Story 7.6 (FR-28): regenerating a password changes nothing visible in
  // the roster (no field on EmployeeResponse reflects it), so no refetch()
  // is needed here, unlike handleEmployeeSaved/handleDeleteOrArchiveCompleted.
  function handlePasswordCopied() {
    setToastMessage('Password copied to clipboard');
  }

  // Story 7.5 (FR-27): the toast copy is driven by the DELETE response's
  // `action` field, not the confirmation dialog's own prediction -- in a
  // race, the server may have decided differently since the dialog opened.
  function handleDeleteOrArchiveCompleted(action: 'deleted' | 'archived') {
    const name = deletingEmployee?.name ?? 'Employee';
    setDeletingEmployee(null);
    setToastMessage(action === 'deleted' ? `✓ '${name}' removed.` : `✓ '${name}' archived.`);
    void refetch();
  }

  // Code review (Story 7.3): options are derived from the archived-toggle-
  // respecting subset, not the full roster -- otherwise a Department/Position
  // that exists only on archived rows would appear in the dropdown while
  // "Show archived" is off, and selecting it would always yield "No
  // employees match your search" with no explanation.
  const archivedRespectingEmployees = useMemo(
    () => (employees ?? []).filter((e) => showArchived || e.archived_at === null),
    [employees, showArchived]
  );
  const departmentOptions = useMemo(
    () => distinctSorted(archivedRespectingEmployees.map((e) => e.department)),
    [archivedRespectingEmployees]
  );
  const positionOptions = useMemo(
    () => distinctSorted(archivedRespectingEmployees.map((e) => e.position)),
    [archivedRespectingEmployees]
  );

  const filtered = useMemo(() => {
    if (!employees) return [];
    const q = search.trim().toLowerCase();
    return employees.filter((e) => {
      if (q && !e.name.toLowerCase().includes(q)) return false;
      if (department && e.department !== department) return false;
      if (position && e.position !== position) return false;
      if (!showArchived && e.archived_at !== null) return false;
      return true;
    });
  }, [employees, search, department, position, showArchived]);

  // AC2: search/filter/archived-toggle reset pagination to page 1. View
  // toggle deliberately does NOT touch page (AC1 -- state is shared).
  useEffect(() => {
    setPage(1);
  }, [search, department, position, showArchived]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const pageItems = filtered.slice((currentPage - 1) * PAGE_SIZE, (currentPage - 1) * PAGE_SIZE + PAGE_SIZE);

  const activeCount = employees?.filter((e) => e.archived_at === null).length ?? 0;

  return (
    <HrAppShell>
      <main className="px-6 pb-12">
        <div className="flex flex-wrap items-center justify-between gap-3 py-3">
          <div>
            <h1 className="text-2xl font-black text-gray-900 dark:text-gray-100" data-testid="employees-tab-heading-title">
              Employees
            </h1>
            <span className="text-sm text-gray-500 dark:text-gray-400" data-testid="employees-tab-summary-count">
              {employees ? `${employees.length} employees · ${activeCount} active` : ''}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="text"
              placeholder="Search by name…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-40 rounded-lg border border-gray-300 px-3 py-2 text-sm sm:w-48 dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
              data-testid="employees-tab-search-input"
            />
            <select
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
              data-testid="employees-tab-filter-department"
              aria-label="Filter by Department"
            >
              <option value="">All Departments</option>
              {departmentOptions.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
            <select
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
              data-testid="employees-tab-filter-position"
              aria-label="Filter by Position"
            >
              <option value="">All Positions</option>
              {positionOptions.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
            <label className="flex items-center gap-1.5 px-1 text-sm text-gray-600 dark:text-gray-400" data-testid="employees-tab-toggle-archived">
              <input
                type="checkbox"
                checked={showArchived}
                onChange={(e) => setShowArchived(e.target.checked)}
                className="rounded"
              />
              Show archived
            </label>
            <div className="flex overflow-hidden rounded-lg border border-gray-300 dark:border-gray-600" data-testid="employees-tab-view-toggle">
              <button
                type="button"
                onClick={() => setView('table')}
                aria-label="Table view"
                aria-pressed={view === 'table'}
                className={'px-3 py-2 text-sm ' + (view === 'table' ? 'bg-blue-600 text-white' : 'bg-white text-gray-500 hover:bg-gray-50 dark:bg-gray-900 dark:text-gray-400 dark:hover:bg-gray-800')}
              >
                ▦
              </button>
              <button
                type="button"
                onClick={() => setView('card')}
                aria-label="Card view"
                aria-pressed={view === 'card'}
                className={'px-3 py-2 text-sm ' + (view === 'card' ? 'bg-blue-600 text-white' : 'bg-white text-gray-500 hover:bg-gray-50 dark:bg-gray-900 dark:text-gray-400 dark:hover:bg-gray-800')}
              >
                ▤
              </button>
            </div>
            <button
              type="button"
              onClick={showUnavailableToast}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600"
              data-testid="employees-tab-btn-new-employee"
            >
              + New Employee
            </button>
          </div>
        </div>

        {employees === null && !loadError && <p className="text-sm text-gray-500 dark:text-gray-400">Loading…</p>}

        {loadError && (
          <div className="space-y-2">
            <p className="text-sm text-red-600 dark:text-red-400">{loadError}</p>
            <button type="button" className="text-sm font-medium text-blue-600 hover:underline dark:text-blue-400" onClick={() => void refetch()}>
              Retry
            </button>
          </div>
        )}

        {employees !== null && !loadError && employees.length === 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400">No employees yet.</p>
        )}

        {employees !== null && !loadError && employees.length > 0 && filtered.length === 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400">No employees match your search.</p>
        )}

        {employees !== null && !loadError && filtered.length > 0 && view === 'table' && (
          <div className="overflow-x-auto">
            <table
              className="w-full min-w-[720px] overflow-hidden rounded-lg border border-gray-200 bg-white text-sm dark:border-gray-700 dark:bg-gray-900"
              data-testid="employees-table"
            >
              <thead className="bg-gray-50 text-xs uppercase tracking-wide text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                <tr>
                  <th className="px-4 py-3 text-left">ID</th>
                  <th className="px-4 py-3 text-left">Name</th>
                  <th className="px-4 py-3 text-left">Position</th>
                  <th className="px-4 py-3 text-left">Department</th>
                  <th className="px-4 py-3 text-left">Email</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {pageItems.map((employee) => (
                  <tr key={employee.id} className="border-t border-gray-100 dark:border-gray-800">
                    <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{employee.employee_code}</td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{employee.name}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{employee.position ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{employee.department ?? '—'}</td>
                    <td className="px-4 py-3 text-xs text-gray-400 dark:text-gray-500">{employee.email}</td>
                    <td className="px-4 py-3">
                      <StatusBadge archived={employee.archived_at !== null} />
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <RowActions
                        employee={employee}
                        onEdit={setEditingEmployee}
                        onRegeneratePassword={setRegeneratingEmployee}
                        onDeleteOrArchive={setDeletingEmployee}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {employees !== null && !loadError && filtered.length > 0 && view === 'card' && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid="employees-grid">
            {pageItems.map((employee) => (
              <div key={employee.id} className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-gray-100">{employee.name}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {employee.position ?? '—'} · {employee.department ?? '—'}
                    </p>
                  </div>
                  <StatusBadge archived={employee.archived_at !== null} />
                </div>
                <p className="mt-2 break-all text-xs text-gray-400 dark:text-gray-500">{employee.email}</p>
                <div className="mt-3 border-t border-gray-100 pt-3 dark:border-gray-800">
                  <RowActions
                    employee={employee}
                    onEdit={setEditingEmployee}
                    onRegeneratePassword={setRegeneratingEmployee}
                    onDeleteOrArchive={setDeletingEmployee}
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        {filtered.length > PAGE_SIZE && (
          <div
            className="mt-4 flex items-center justify-center gap-3 text-sm text-gray-600 dark:text-gray-400"
            data-testid="employees-table-pagination"
          >
            <button
              type="button"
              onClick={() => setPage(currentPage - 1)}
              disabled={currentPage === 1}
              className="disabled:opacity-30"
              aria-label="Previous page"
            >
              ‹
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setPage(p)}
                className={p === currentPage ? 'font-bold text-blue-600 dark:text-blue-400' : ''}
                aria-label={`Page ${p}`}
                aria-current={p === currentPage ? 'page' : undefined}
              >
                {p}
              </button>
            ))}
            <button
              type="button"
              onClick={() => setPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="disabled:opacity-30"
              aria-label="Next page"
            >
              ›
            </button>
          </div>
        )}
      </main>

      <Toast message={toastMessage} onDismiss={() => setToastMessage(null)} />

      <EditEmployeeModal
        open={editingEmployee !== null}
        employee={editingEmployee}
        onClose={() => setEditingEmployee(null)}
        onSaved={handleEmployeeSaved}
      />

      <RegeneratePasswordModal
        open={regeneratingEmployee !== null}
        employee={regeneratingEmployee}
        onClose={() => setRegeneratingEmployee(null)}
        onCopied={handlePasswordCopied}
      />

      <DeleteArchiveEmployeeModal
        open={deletingEmployee !== null}
        employee={deletingEmployee}
        onClose={() => setDeletingEmployee(null)}
        onCompleted={handleDeleteOrArchiveCompleted}
      />
    </HrAppShell>
  );
}
