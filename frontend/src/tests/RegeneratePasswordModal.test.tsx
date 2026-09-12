import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RegeneratePasswordModal } from '@/features/admin/RegeneratePasswordModal';

vi.mock('@/lib/api/employeesApi', () => ({
  regeneratePassword: vi.fn(),
}));

import { regeneratePassword } from '@/lib/api/employeesApi';

// @testing-library/user-event installs its own getter-based Clipboard stub
// on navigator.clipboard the moment userEvent.setup() runs (it re-attaches
// on every setup() call, clobbering anything set beforehand) -- so a manual
// pre-setup Object.defineProperty/vi.stubGlobal override gets silently
// discarded. Spy on the real method AFTER calling setup() instead.
function regenerateResponse(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    id: 'emp-1',
    employee_code: 'EMP-0001',
    name: 'Casey Employee',
    email: 'casey@example.com',
    role: 'EMPLOYEE',
    phone: null,
    experience: null,
    technologies: null,
    position: null,
    project: null,
    manager_name: null,
    location: null,
    department: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    archived_at: null,
    has_assignment_history: false,
    generated_password: 'aB3dEfGhJkLm',
    ...overrides,
  };
}

describe('RegeneratePasswordModal', () => {
  beforeEach(() => {
    vi.mocked(regeneratePassword).mockReset();
  });

  it('renders the confirm step copy with the employee name', () => {
    render(
      <RegeneratePasswordModal employee={{ id: 'emp-1', name: 'Casey Employee' }} open onClose={vi.fn()} onCopied={vi.fn()} />
    );

    expect(screen.getByTestId('regen-password-heading')).toHaveTextContent('Regenerate password for Casey Employee?');
    expect(screen.getByTestId('regen-password-summary')).toHaveTextContent(
      'Their current password will stop working immediately'
    );
    expect(screen.queryByTestId('password-reveal-title')).not.toBeInTheDocument();
  });

  it('confirm calls the API and transitions to the revealed step with the returned password', async () => {
    vi.mocked(regeneratePassword).mockResolvedValue(regenerateResponse({ id: 'emp-42' }) as never);
    const user = userEvent.setup();
    render(
      <RegeneratePasswordModal employee={{ id: 'emp-42', name: 'Casey Employee' }} open onClose={vi.fn()} onCopied={vi.fn()} />
    );

    await user.click(screen.getByTestId('regen-password-btn-confirm'));

    expect(regeneratePassword).toHaveBeenCalledWith('emp-42');
    expect(await screen.findByTestId('password-reveal-title')).toHaveTextContent('Password regenerated');
    expect(screen.getByTestId('password-reveal-summary')).toHaveTextContent('Casey Employee');
    expect(screen.getByTestId('password-reveal-value')).toHaveTextContent('aB3dEfGhJkLm');
  });

  it('the confirm button is disabled while a regenerate request is in flight', async () => {
    let resolveRegenerate: (value: ReturnType<typeof regenerateResponse>) => void;
    vi.mocked(regeneratePassword).mockReturnValue(
      new Promise((resolve) => {
        resolveRegenerate = resolve;
      }) as never
    );
    const user = userEvent.setup();
    render(
      <RegeneratePasswordModal employee={{ id: 'emp-1', name: 'Casey Employee' }} open onClose={vi.fn()} onCopied={vi.fn()} />
    );

    await user.click(screen.getByTestId('regen-password-btn-confirm'));

    expect(screen.getByTestId('regen-password-btn-confirm')).toBeDisabled();
    expect(screen.getByTestId('regen-password-btn-cancel')).toBeDisabled();

    resolveRegenerate!(regenerateResponse());
    expect(await screen.findByTestId('password-reveal-title')).toBeInTheDocument();
  });

  it('Escape/backdrop-close is a no-op while a regenerate request is in flight (code review regression)', async () => {
    let resolveRegenerate: (value: ReturnType<typeof regenerateResponse>) => void;
    vi.mocked(regeneratePassword).mockReturnValue(
      new Promise((resolve) => {
        resolveRegenerate = resolve;
      }) as never
    );
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(
      <RegeneratePasswordModal employee={{ id: 'emp-1', name: 'Casey Employee' }} open onClose={onClose} onCopied={vi.fn()} />
    );

    await user.click(screen.getByTestId('regen-password-btn-confirm'));
    await user.keyboard('{Escape}');

    expect(onClose).not.toHaveBeenCalled();

    resolveRegenerate!(regenerateResponse());
    expect(await screen.findByTestId('password-reveal-title')).toBeInTheDocument();
  });

  it('a failed confirm shows an inline error and stays on the confirm step', async () => {
    vi.mocked(regeneratePassword).mockRejectedValue(new Error('boom'));
    const user = userEvent.setup();
    render(
      <RegeneratePasswordModal employee={{ id: 'emp-1', name: 'Casey Employee' }} open onClose={vi.fn()} onCopied={vi.fn()} />
    );

    await user.click(screen.getByTestId('regen-password-btn-confirm'));

    expect(await screen.findByText(/Couldn't regenerate/)).toBeInTheDocument();
    expect(screen.getByTestId('regen-password-heading')).toBeInTheDocument();
    expect(screen.queryByTestId('password-reveal-title')).not.toBeInTheDocument();
  });

  it('Copy writes the password to the clipboard and fires onCopied on success', async () => {
    vi.mocked(regeneratePassword).mockResolvedValue(regenerateResponse() as never);
    const onCopied = vi.fn();
    const user = userEvent.setup();
    const writeTextSpy = vi.spyOn(navigator.clipboard, 'writeText').mockResolvedValue(undefined);
    render(
      <RegeneratePasswordModal employee={{ id: 'emp-1', name: 'Casey Employee' }} open onClose={vi.fn()} onCopied={onCopied} />
    );

    await user.click(screen.getByTestId('regen-password-btn-confirm'));
    await screen.findByTestId('password-reveal-btn-copy');
    await user.click(screen.getByTestId('password-reveal-btn-copy'));

    await waitFor(() => expect(onCopied).toHaveBeenCalled());
    expect(writeTextSpy).toHaveBeenCalledWith('aB3dEfGhJkLm');
  });

  it('Copy fails silently (no thrown error, no onCopied call) when clipboard access is rejected', async () => {
    vi.mocked(regeneratePassword).mockResolvedValue(regenerateResponse() as never);
    const onCopied = vi.fn();
    const user = userEvent.setup();
    const writeTextSpy = vi.spyOn(navigator.clipboard, 'writeText').mockRejectedValue(new Error('denied'));
    render(
      <RegeneratePasswordModal employee={{ id: 'emp-1', name: 'Casey Employee' }} open onClose={vi.fn()} onCopied={onCopied} />
    );

    await user.click(screen.getByTestId('regen-password-btn-confirm'));
    await screen.findByTestId('password-reveal-btn-copy');
    await user.click(screen.getByTestId('password-reveal-btn-copy'));
    await waitFor(() => expect(writeTextSpy).toHaveBeenCalled());

    expect(onCopied).not.toHaveBeenCalled();
    expect(screen.getByTestId('password-reveal-value')).toHaveTextContent('aB3dEfGhJkLm');
  });

  it('Cancel on the confirm step calls onClose without calling the API', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(
      <RegeneratePasswordModal employee={{ id: 'emp-1', name: 'Casey Employee' }} open onClose={onClose} onCopied={vi.fn()} />
    );

    await user.click(screen.getByTestId('regen-password-btn-cancel'));

    expect(onClose).toHaveBeenCalled();
    expect(regeneratePassword).not.toHaveBeenCalled();
  });

  it('Done on the revealed step calls onClose', async () => {
    vi.mocked(regeneratePassword).mockResolvedValue(regenerateResponse() as never);
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(
      <RegeneratePasswordModal employee={{ id: 'emp-1', name: 'Casey Employee' }} open onClose={onClose} onCopied={vi.fn()} />
    );

    await user.click(screen.getByTestId('regen-password-btn-confirm'));
    await user.click(await screen.findByTestId('password-reveal-btn-done'));

    expect(onClose).toHaveBeenCalled();
  });

  it('renders nothing when employee is null', () => {
    const { container } = render(<RegeneratePasswordModal employee={null} open onClose={vi.fn()} onCopied={vi.fn()} />);
    expect(container).toBeEmptyDOMElement();
  });
});
