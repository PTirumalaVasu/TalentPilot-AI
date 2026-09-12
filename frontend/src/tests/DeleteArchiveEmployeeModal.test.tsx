import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DeleteArchiveEmployeeModal } from '@/features/admin/DeleteArchiveEmployeeModal';

vi.mock('@/lib/api/employeesApi', () => ({
  deleteOrArchiveEmployee: vi.fn(),
}));

import { deleteOrArchiveEmployee } from '@/lib/api/employeesApi';

describe('DeleteArchiveEmployeeModal', () => {
  beforeEach(() => {
    vi.mocked(deleteOrArchiveEmployee).mockReset();
  });

  it('renders the hard-delete copy and button label when has_assignment_history is false', () => {
    render(
      <DeleteArchiveEmployeeModal
        employee={{ id: 'emp-1', name: 'Casey Employee', has_assignment_history: false }}
        open
        onClose={vi.fn()}
        onCompleted={vi.fn()}
      />
    );

    expect(screen.getByTestId('delete-employee-heading')).toHaveTextContent('Remove Casey Employee?');
    expect(screen.getByTestId('delete-employee-summary-hard')).toHaveTextContent(
      "'Casey Employee' has no assignments yet"
    );
    expect(screen.queryByTestId('delete-employee-summary-archive')).not.toBeInTheDocument();
    expect(screen.getByTestId('delete-employee-btn-confirm')).toHaveTextContent('Remove Employee');
  });

  it('renders the archive copy and button label when has_assignment_history is true', () => {
    render(
      <DeleteArchiveEmployeeModal
        employee={{ id: 'emp-1', name: 'Casey Employee', has_assignment_history: true }}
        open
        onClose={vi.fn()}
        onCompleted={vi.fn()}
      />
    );

    expect(screen.getByTestId('delete-employee-summary-archive')).toHaveTextContent(
      "'Casey Employee' has assignment history"
    );
    expect(screen.queryByTestId('delete-employee-summary-hard')).not.toBeInTheDocument();
    expect(screen.getByTestId('delete-employee-btn-confirm')).toHaveTextContent('Archive Employee');
  });

  it('confirm calls the API with the right id and calls onCompleted+onClose with the response action', async () => {
    vi.mocked(deleteOrArchiveEmployee).mockResolvedValue({ action: 'archived' });
    const onCompleted = vi.fn();
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(
      <DeleteArchiveEmployeeModal
        employee={{ id: 'emp-42', name: 'Casey Employee', has_assignment_history: true }}
        open
        onClose={onClose}
        onCompleted={onCompleted}
      />
    );

    await user.click(screen.getByTestId('delete-employee-btn-confirm'));

    expect(deleteOrArchiveEmployee).toHaveBeenCalledWith('emp-42');
    expect(onCompleted).toHaveBeenCalledWith('archived');
    expect(onClose).toHaveBeenCalled();
  });

  it('cancel calls onClose without calling the API', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(
      <DeleteArchiveEmployeeModal
        employee={{ id: 'emp-1', name: 'Casey Employee', has_assignment_history: false }}
        open
        onClose={onClose}
        onCompleted={vi.fn()}
      />
    );

    await user.click(screen.getByTestId('delete-employee-btn-cancel'));

    expect(onClose).toHaveBeenCalled();
    expect(deleteOrArchiveEmployee).not.toHaveBeenCalled();
  });

  it('a rejected confirm shows an inline error and does not call onClose', async () => {
    vi.mocked(deleteOrArchiveEmployee).mockRejectedValue(new Error('boom'));
    const onClose = vi.fn();
    const onCompleted = vi.fn();
    const user = userEvent.setup();
    render(
      <DeleteArchiveEmployeeModal
        employee={{ id: 'emp-1', name: 'Casey Employee', has_assignment_history: false }}
        open
        onClose={onClose}
        onCompleted={onCompleted}
      />
    );

    await user.click(screen.getByTestId('delete-employee-btn-confirm'));

    expect(await screen.findByText(/Couldn't complete this/)).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
    expect(onCompleted).not.toHaveBeenCalled();
  });

  it('renders nothing when employee is null', () => {
    const { container } = render(
      <DeleteArchiveEmployeeModal employee={null} open onClose={vi.fn()} onCompleted={vi.fn()} />
    );
    expect(container).toBeEmptyDOMElement();
  });
});
