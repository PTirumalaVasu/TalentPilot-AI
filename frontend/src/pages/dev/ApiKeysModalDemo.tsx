import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { ApiKeysModal } from '@/features/admin/ApiKeysModal';

/**
 * Dev-only page to exercise ApiKeysModal (Story 6.5) ahead of the real
 * Skills tab (Story 6.10, not built yet) that will eventually render it
 * behind a "Manage API Keys" button. Mirrors VideoPlayerDemo.tsx's role:
 * a minimal route so a component built ahead of its consuming page can
 * still be manually verified in a real browser.
 */
export function ApiKeysModalDemo() {
  const [open, setOpen] = useState(false);

  return (
    <div className="mx-auto max-w-3xl p-8">
      <h1 className="text-2xl font-bold">API Keys Modal (dev demo)</h1>
      <p className="mb-6 text-sm text-slate-500">
        Story 6.5: Per-Admin &amp; Org-Wide Credential Storage
      </p>

      <Button onClick={() => setOpen(true)}>Open API Keys</Button>

      <ApiKeysModal open={open} onClose={() => setOpen(false)} />
    </div>
  );
}
