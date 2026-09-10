import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ApiKeysModal } from '@/features/admin/ApiKeysModal';

vi.mock('@/lib/api/adminApiKeysApi', () => ({
  getApiKeysStatus: vi.fn(),
  saveYoutubeKey: vi.fn(),
  removeYoutubeKey: vi.fn(),
  saveUdemyCredential: vi.fn(),
  removeUdemyCredential: vi.fn(),
}));

import {
  getApiKeysStatus,
  saveYoutubeKey,
  removeYoutubeKey,
  saveUdemyCredential,
  removeUdemyCredential,
} from '@/lib/api/adminApiKeysApi';

const NOT_CONFIGURED = {
  youtube: { configured: false },
  udemy: { configured: false, configured_by: null, configured_at: null },
};

const BOTH_CONFIGURED = {
  youtube: { configured: true },
  udemy: { configured: true, configured_by: 'Rita the Recommender', configured_at: '2026-09-10T00:00:00Z' },
};

describe('ApiKeysModal', () => {
  beforeEach(() => {
    vi.mocked(getApiKeysStatus).mockReset().mockResolvedValue(NOT_CONFIGURED);
    vi.mocked(saveYoutubeKey).mockReset().mockResolvedValue(undefined);
    vi.mocked(removeYoutubeKey).mockReset().mockResolvedValue(undefined);
    vi.mocked(saveUdemyCredential).mockReset().mockResolvedValue(undefined);
    vi.mocked(removeUdemyCredential).mockReset().mockResolvedValue(undefined);
  });

  it('does not render when closed', () => {
    render(<ApiKeysModal open={false} onClose={vi.fn()} />);
    expect(screen.queryByText('Manage API Keys')).not.toBeInTheDocument();
  });

  it('fetches and renders both rows with their status on open', async () => {
    vi.mocked(getApiKeysStatus).mockResolvedValue(BOTH_CONFIGURED);
    render(<ApiKeysModal open onClose={vi.fn()} />);

    expect(await screen.findByText('Manage API Keys')).toBeInTheDocument();
    await waitFor(() => expect(getApiKeysStatus).toHaveBeenCalled());
    expect(await screen.findByText('Connected')).toBeInTheDocument();
    expect(await screen.findByText(/Connected by Rita the Recommender/)).toBeInTheDocument();
  });

  it('shows Not connected for both rows when nothing is configured', async () => {
    render(<ApiKeysModal open onClose={vi.fn()} />);

    const notConnected = await screen.findAllByText('Not connected');
    expect(notConnected).toHaveLength(2);
  });

  it('saves the YouTube key and clears the input on success', async () => {
    const user = userEvent.setup();
    render(<ApiKeysModal open onClose={vi.fn()} />);

    // findByPlaceholderText (not get*) -- the input only mounts once the
    // async status fetch resolves, so it must be awaited/retried, not just
    // the static title text which renders before that.
    const input = await screen.findByPlaceholderText('Paste your YouTube API key');
    await user.type(input, 'my-new-key');
    await user.click(screen.getByTestId('api-keys-modal-btn-save-youtube'));

    await waitFor(() => expect(saveYoutubeKey).toHaveBeenCalledWith('my-new-key'));
    await waitFor(() => expect(input).toHaveValue(''));
  });

  it('shows an inline error and keeps the input when saving the YouTube key fails', async () => {
    vi.mocked(saveYoutubeKey).mockRejectedValue(new Error('boom'));
    const user = userEvent.setup();
    render(<ApiKeysModal open onClose={vi.fn()} />);

    const input = await screen.findByPlaceholderText('Paste your YouTube API key');
    await user.type(input, 'my-new-key');
    await user.click(screen.getByTestId('api-keys-modal-btn-save-youtube'));

    expect(await screen.findByRole('alert')).toHaveTextContent(/couldn.t save/i);
    expect(input).toHaveValue('my-new-key');
  });

  it('the Save button is disabled until the YouTube key input is non-blank', async () => {
    render(<ApiKeysModal open onClose={vi.fn()} />);

    expect(await screen.findByTestId('api-keys-modal-btn-save-youtube')).toBeDisabled();
  });

  it('requires a confirm step before removing the YouTube key', async () => {
    vi.mocked(getApiKeysStatus).mockResolvedValue({
      youtube: { configured: true },
      udemy: { configured: false, configured_by: null, configured_at: null },
    });
    const user = userEvent.setup();
    render(<ApiKeysModal open onClose={vi.fn()} />);
    await screen.findByText('Connected');

    await user.click(screen.getByRole('button', { name: /remove/i }));
    expect(removeYoutubeKey).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: /confirm/i }));
    await waitFor(() => expect(removeYoutubeKey).toHaveBeenCalled());
  });

  it('canceling the remove confirm does not call the API', async () => {
    vi.mocked(getApiKeysStatus).mockResolvedValue({
      youtube: { configured: true },
      udemy: { configured: false, configured_by: null, configured_at: null },
    });
    const user = userEvent.setup();
    render(<ApiKeysModal open onClose={vi.fn()} />);
    await screen.findByText('Connected');

    await user.click(screen.getByRole('button', { name: /remove/i }));
    await user.click(screen.getByRole('button', { name: /cancel/i }));

    expect(removeYoutubeKey).not.toHaveBeenCalled();
    expect(screen.queryByText('Remove this key?')).not.toBeInTheDocument();
  });

  it('saves the Udemy credential with both fields and clears both inputs on success', async () => {
    const user = userEvent.setup();
    render(<ApiKeysModal open onClose={vi.fn()} />);

    await user.type(await screen.findByPlaceholderText('Client ID'), 'client-1');
    await user.type(screen.getByPlaceholderText('Client secret'), 'secret-1');
    await user.click(screen.getByTestId('api-keys-modal-btn-save-udemy'));

    await waitFor(() => expect(saveUdemyCredential).toHaveBeenCalledWith('client-1', 'secret-1'));
    await waitFor(() => expect(screen.getByPlaceholderText('Client ID')).toHaveValue(''));
    expect(screen.getByPlaceholderText('Client secret')).toHaveValue('');
  });

  it('the Udemy Save button stays disabled until both fields are non-blank', async () => {
    const user = userEvent.setup();
    render(<ApiKeysModal open onClose={vi.fn()} />);

    const saveButton = await screen.findByTestId('api-keys-modal-btn-save-udemy');
    expect(saveButton).toBeDisabled();

    await user.type(screen.getByPlaceholderText('Client ID'), 'client-1');
    expect(saveButton).toBeDisabled();

    await user.type(screen.getByPlaceholderText('Client secret'), 'secret-1');
    expect(saveButton).toBeEnabled();
  });

  it('shows the shared-credential helper text under the Udemy row', async () => {
    render(<ApiKeysModal open onClose={vi.fn()} />);
    expect(
      await screen.findByText('This credential is shared across all HR Admins, not personal to your account.')
    ).toBeInTheDocument();
  });

  it('closing and reopening resets stale input from a previous session', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<ApiKeysModal open onClose={vi.fn()} />);

    await user.type(await screen.findByPlaceholderText('Paste your YouTube API key'), 'leftover-text');

    rerender(<ApiKeysModal open={false} onClose={vi.fn()} />);
    rerender(<ApiKeysModal open onClose={vi.fn()} />);

    expect(await screen.findByPlaceholderText('Paste your YouTube API key')).toHaveValue('');
  });

  it('calls onClose when the close [X] button is clicked', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<ApiKeysModal open onClose={onClose} />);
    await screen.findByText('Manage API Keys');

    // Two elements match an accessible name of "Close" (the [X] icon button
    // and the footer text button) -- target the [X] specifically by testid.
    await user.click(screen.getByTestId('api-keys-modal-btn-close'));
    expect(onClose).toHaveBeenCalled();
  });
});
