import { useEffect, useId, useRef, useState } from 'react';
import { Dialog } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { FormErrorText } from '@/components/ui/form-error-text';
import {
  getApiKeysStatus,
  removeUdemyCredential,
  removeYoutubeKey,
  saveUdemyCredential,
  saveYoutubeKey,
  type ApiKeysStatus,
} from '@/lib/api/adminApiKeysApi';

export interface ApiKeysModalProps {
  open: boolean;
  onClose: () => void;
}

function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response?: { data?: { message?: string } } }).response;
    if (response?.data?.message) return response.data.message;
  }
  return fallback;
}

function formatConnectedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

/**
 * "Manage API Keys" modal (Story 6.5, FR-16) -- per-Admin YouTube key +
 * org-wide Udemy credential, matching 04.1-skills-content-sourcing.md's
 * object IDs (api-keys-modal-*). Self-contained: fetches its own status on
 * open, no data props. Built on the existing Dialog primitive exactly as
 * DeleteAssignmentModal.tsx/ProvenanceDrillDownModal.tsx do -- Story 6.10
 * (the real Skills tab) will render this directly once its "Manage API
 * Keys" button exists.
 */
export function ApiKeysModal({ open, onClose }: ApiKeysModalProps) {
  const titleId = useId();
  const requestIdRef = useRef(0);
  // Guards every async setState below against a future consumer that
  // conditionally unmounts this component (rather than only toggling
  // `open`, this story's own usage never does) -- code review, 2026-09-10.
  const isMountedRef = useRef(true);
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [status, setStatus] = useState<ApiKeysStatus | null>(null);

  const [youtubeKeyInput, setYoutubeKeyInput] = useState('');
  const [youtubeSaving, setYoutubeSaving] = useState(false);
  const [youtubeError, setYoutubeError] = useState<string | null>(null);
  const [youtubeRemoveConfirm, setYoutubeRemoveConfirm] = useState(false);
  const [youtubeRemoving, setYoutubeRemoving] = useState(false);

  const [udemyClientId, setUdemyClientId] = useState('');
  const [udemyClientSecret, setUdemyClientSecret] = useState('');
  const [udemySaving, setUdemySaving] = useState(false);
  const [udemyError, setUdemyError] = useState<string | null>(null);
  const [udemyRemoveConfirm, setUdemyRemoveConfirm] = useState(false);
  const [udemyRemoving, setUdemyRemoving] = useState(false);

  async function refreshStatus(requestId: number) {
    try {
      const result = await getApiKeysStatus();
      if (!isMountedRef.current || requestIdRef.current !== requestId) return;
      setStatus(result);
      setLoadError(null);
    } catch (err) {
      if (!isMountedRef.current || requestIdRef.current !== requestId) return;
      setLoadError(extractErrorMessage(err, "Couldn't load API key status. Try again."));
    } finally {
      if (isMountedRef.current && requestIdRef.current === requestId) setLoading(false);
    }
  }

  // Resets all per-field transient state and re-fetches status every time
  // the modal opens -- mirrors DeleteAssignmentModal.tsx's reset-on-open
  // effect (Story 5.7 code review finding: without this, state from a
  // previous open/cancel leaks into the next one).
  useEffect(() => {
    const requestId = ++requestIdRef.current;
    setYoutubeKeyInput('');
    setYoutubeError(null);
    setYoutubeRemoveConfirm(false);
    setUdemyClientId('');
    setUdemyClientSecret('');
    setUdemyError(null);
    setUdemyRemoveConfirm(false);

    if (!open) return;
    setLoading(true);
    setLoadError(null);
    void refreshStatus(requestId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  async function handleSaveYoutube() {
    if (!youtubeKeyInput.trim()) return;
    setYoutubeSaving(true);
    setYoutubeError(null);
    try {
      await saveYoutubeKey(youtubeKeyInput.trim());
      if (!isMountedRef.current) return;
      setYoutubeKeyInput('');
      await refreshStatus(requestIdRef.current);
    } catch (err) {
      if (!isMountedRef.current) return;
      setYoutubeError(extractErrorMessage(err, "Couldn't save the YouTube key. Try again."));
    } finally {
      if (isMountedRef.current) setYoutubeSaving(false);
    }
  }

  async function handleConfirmRemoveYoutube() {
    setYoutubeRemoving(true);
    setYoutubeError(null);
    try {
      await removeYoutubeKey();
      if (!isMountedRef.current) return;
      setYoutubeRemoveConfirm(false);
      await refreshStatus(requestIdRef.current);
    } catch (err) {
      if (!isMountedRef.current) return;
      setYoutubeError(extractErrorMessage(err, "Couldn't remove the YouTube key. Try again."));
    } finally {
      if (isMountedRef.current) setYoutubeRemoving(false);
    }
  }

  async function handleSaveUdemy() {
    if (!udemyClientId.trim() || !udemyClientSecret.trim()) return;
    setUdemySaving(true);
    setUdemyError(null);
    try {
      await saveUdemyCredential(udemyClientId.trim(), udemyClientSecret.trim());
      if (!isMountedRef.current) return;
      setUdemyClientId('');
      setUdemyClientSecret('');
      await refreshStatus(requestIdRef.current);
    } catch (err) {
      if (!isMountedRef.current) return;
      setUdemyError(extractErrorMessage(err, "Couldn't save the Udemy credential. Try again."));
    } finally {
      if (isMountedRef.current) setUdemySaving(false);
    }
  }

  async function handleConfirmRemoveUdemy() {
    setUdemyRemoving(true);
    setUdemyError(null);
    try {
      await removeUdemyCredential();
      if (!isMountedRef.current) return;
      setUdemyRemoveConfirm(false);
      await refreshStatus(requestIdRef.current);
    } catch (err) {
      if (!isMountedRef.current) return;
      setUdemyError(extractErrorMessage(err, "Couldn't remove the Udemy credential. Try again."));
    } finally {
      if (isMountedRef.current) setUdemyRemoving(false);
    }
  }

  if (!open) return null;

  return (
    <Dialog open={open} onClose={onClose} titleId={titleId} className="max-w-xl">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 id={titleId} className="text-lg font-bold text-gray-900 dark:text-gray-100" data-testid="api-keys-modal-header-title">
            Manage API Keys
          </h2>
          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
            data-testid="api-keys-modal-btn-close"
          >
            ✕
          </button>
        </div>

        {loading && <p className="text-sm text-gray-500 dark:text-gray-400">Loading…</p>}
        {loadError && (
          <div className="space-y-2">
            <FormErrorText>{loadError}</FormErrorText>
            <Button variant="outline" size="sm" onClick={() => void refreshStatus(++requestIdRef.current)}>
              Retry
            </Button>
          </div>
        )}

        {!loading && !loadError && status && (
          <>
            {/* YouTube row */}
            <div className="space-y-2 border-b border-gray-100 pb-4 dark:border-gray-800" data-testid="api-keys-modal-youtube-row">
              <div className="flex items-center justify-between">
                <Label htmlFor="youtube-key-input">YouTube (your personal key)</Label>
                <span className="text-xs text-gray-500 dark:text-gray-400" data-testid="api-keys-modal-youtube-status">
                  {status.youtube.configured ? 'Connected' : 'Not connected'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Input
                  id="youtube-key-input"
                  type="password"
                  placeholder="Paste your YouTube API key"
                  value={youtubeKeyInput}
                  onChange={(e) => setYoutubeKeyInput(e.target.value)}
                  disabled={youtubeSaving || youtubeRemoving}
                />
                <Button
                  size="sm"
                  // youtubeRemoving guards against racing a Save against an
                  // in-flight Remove for the same credential (code review,
                  // 2026-09-10) -- without it, the final DB/UI state depended
                  // on which request happened to land last, not user intent.
                  disabled={youtubeSaving || youtubeRemoving || !youtubeKeyInput.trim()}
                  onClick={handleSaveYoutube}
                  data-testid="api-keys-modal-btn-save-youtube"
                >
                  {youtubeSaving ? 'Saving…' : 'Save'}
                </Button>
                {status.youtube.configured && !youtubeRemoveConfirm && (
                  <button
                    type="button"
                    className="text-sm font-medium text-red-600 hover:underline disabled:opacity-50 dark:text-red-400"
                    disabled={youtubeSaving}
                    onClick={() => setYoutubeRemoveConfirm(true)}
                    data-testid="api-keys-modal-btn-remove-youtube"
                  >
                    Remove
                  </button>
                )}
              </div>
              {youtubeRemoveConfirm && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-gray-700 dark:text-gray-300">Remove this key?</span>
                  <button
                    type="button"
                    className="font-medium text-red-600 hover:underline disabled:opacity-50 dark:text-red-400"
                    disabled={youtubeRemoving}
                    onClick={handleConfirmRemoveYoutube}
                  >
                    {youtubeRemoving ? 'Removing…' : 'Confirm'}
                  </button>
                  <button
                    type="button"
                    className="text-gray-600 hover:underline disabled:opacity-50 dark:text-gray-400"
                    disabled={youtubeRemoving}
                    onClick={() => setYoutubeRemoveConfirm(false)}
                  >
                    Cancel
                  </button>
                </div>
              )}
              {youtubeError && <FormErrorText>{youtubeError}</FormErrorText>}
            </div>

            {/* Udemy row */}
            <div className="space-y-2" data-testid="api-keys-modal-udemy-row">
              <div className="flex items-center justify-between">
                <Label htmlFor="udemy-client-id-input">Udemy (organization-wide)</Label>
                <span className="text-xs text-gray-500 dark:text-gray-400" data-testid="api-keys-modal-udemy-status">
                  {status.udemy.configured
                    ? `Connected by ${status.udemy.configured_by ?? 'an HR Admin'}${
                        status.udemy.configured_at ? `, ${formatConnectedAt(status.udemy.configured_at)}` : ''
                      }`
                    : 'Not connected'}
                </span>
              </div>
              <Input
                id="udemy-client-id-input"
                placeholder="Client ID"
                value={udemyClientId}
                onChange={(e) => setUdemyClientId(e.target.value)}
                disabled={udemySaving || udemyRemoving}
              />
              <div className="flex items-center gap-2">
                <Input
                  id="udemy-client-secret-input"
                  type="password"
                  placeholder="Client secret"
                  value={udemyClientSecret}
                  onChange={(e) => setUdemyClientSecret(e.target.value)}
                  disabled={udemySaving || udemyRemoving}
                />
                <Button
                  size="sm"
                  // udemyRemoving guards against the same Save-vs-Remove
                  // race as the YouTube row above.
                  disabled={udemySaving || udemyRemoving || !udemyClientId.trim() || !udemyClientSecret.trim()}
                  onClick={handleSaveUdemy}
                  data-testid="api-keys-modal-btn-save-udemy"
                >
                  {udemySaving ? 'Saving…' : 'Save'}
                </Button>
                {status.udemy.configured && !udemyRemoveConfirm && (
                  <button
                    type="button"
                    className="text-sm font-medium text-red-600 hover:underline disabled:opacity-50 dark:text-red-400"
                    disabled={udemySaving}
                    onClick={() => setUdemyRemoveConfirm(true)}
                    data-testid="api-keys-modal-btn-remove-udemy"
                  >
                    Remove
                  </button>
                )}
              </div>
              {udemyRemoveConfirm && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-gray-700 dark:text-gray-300">Remove this credential?</span>
                  <button
                    type="button"
                    className="font-medium text-red-600 hover:underline disabled:opacity-50 dark:text-red-400"
                    disabled={udemyRemoving}
                    onClick={handleConfirmRemoveUdemy}
                  >
                    {udemyRemoving ? 'Removing…' : 'Confirm'}
                  </button>
                  <button
                    type="button"
                    className="text-gray-600 hover:underline disabled:opacity-50 dark:text-gray-400"
                    disabled={udemyRemoving}
                    onClick={() => setUdemyRemoveConfirm(false)}
                  >
                    Cancel
                  </button>
                </div>
              )}
              {udemyError && <FormErrorText>{udemyError}</FormErrorText>}
              <p className="text-xs text-gray-500 dark:text-gray-400">
                This credential is shared across all HR Admins, not personal to your account.
              </p>
            </div>
          </>
        )}

        <div className="flex justify-end border-t border-gray-100 pt-4 dark:border-gray-800">
          <button type="button" className="text-sm font-medium text-gray-600 hover:underline dark:text-gray-400" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </Dialog>
  );
}
