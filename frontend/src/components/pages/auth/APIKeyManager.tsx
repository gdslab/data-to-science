import { AxiosResponse, isAxiosError } from 'axios';
import { useCallback, useEffect, useState } from 'react';
import {
  ChevronDownIcon,
  ChevronUpIcon,
  DocumentDuplicateIcon,
} from '@heroicons/react/24/outline';

import Alert, { Status } from '../../Alert';
import { Button } from '../../Buttons';
import Checkbox from '../../Checkbox';
import ConfirmationModal from '../../ConfirmationModal';
import { styles } from '../../FormFields';
import HintText from '../../HintText';

import api from '../../../api';

export type APIKeyScope = 'read' | 'create' | 'update' | 'delete';

export interface APIKey {
  id: string;
  api_key: string;
  created_at: string;
  last_used_at: string | null;
  name: string | null;
  scopes: APIKeyScope[];
  total_requests: number;
}

const MAX_ACTIVE_API_KEYS = 5;

const SCOPE_OPTIONS: { scope: APIKeyScope; label: string; hint: string }[] = [
  {
    scope: 'read',
    label: 'Read',
    hint: 'View projects, flights, and layers, and download files',
  },
  {
    scope: 'create',
    label: 'Create',
    hint: 'Add new records, such as field observations',
  },
  {
    scope: 'update',
    label: 'Update',
    hint: 'Modify existing records',
  },
  {
    scope: 'delete',
    label: 'Delete',
    hint: 'Remove existing records',
  },
];

function getErrorMessage(err: unknown, fallback: string): string {
  if (isAxiosError(err) && typeof err.response?.data?.detail === 'string') {
    return err.response.data.detail;
  }
  return fallback;
}

function formatDate(value: string | null): string {
  return value ? new Date(value).toLocaleDateString() : 'Never';
}

function toggleScope(
  scopes: APIKeyScope[],
  scope: APIKeyScope,
  checked: boolean,
): APIKeyScope[] {
  if (checked) {
    return SCOPE_OPTIONS.map((option) => option.scope).filter(
      (s) => s === scope || scopes.includes(s),
    );
  }
  return scopes.filter((s) => s !== scope);
}

function ScopeCheckboxes({
  idPrefix,
  scopes,
  onChange,
  disabled = false,
}: {
  idPrefix: string;
  scopes: APIKeyScope[];
  onChange: (scopes: APIKeyScope[]) => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex flex-row flex-wrap gap-4">
      {SCOPE_OPTIONS.map(({ scope, label, hint }) => {
        const checked = scopes.includes(scope);
        // keys must keep at least one scope
        const isLastChecked = checked && scopes.length === 1;
        return (
          <label
            key={scope}
            htmlFor={`${idPrefix}-${scope}`}
            className="flex items-center gap-2 text-sm"
            title={hint}
          >
            <Checkbox
              id={`${idPrefix}-${scope}`}
              checked={checked}
              disabled={disabled || isLastChecked}
              onChange={(e) =>
                onChange(toggleScope(scopes, scope, e.target.checked))
              }
            />
            {label}
          </label>
        );
      })}
    </div>
  );
}

function sameScopes(a: APIKeyScope[], b: APIKeyScope[]): boolean {
  return a.length === b.length && a.every((scope) => b.includes(scope));
}

function ScopeBadges({ scopes }: { scopes: APIKeyScope[] }) {
  return (
    <div className="flex flex-row flex-wrap gap-1">
      {SCOPE_OPTIONS.filter(({ scope }) => scopes.includes(scope)).map(
        ({ scope, label }) => (
          <span
            key={scope}
            className="px-1.5 py-0.5 text-xs font-medium rounded-sm bg-gray-100 text-gray-700"
          >
            {label}
          </span>
        ),
      )}
    </div>
  );
}

function APIKeyRow({
  apiKey,
  isExpanded,
  onToggle,
  onRevoke,
  onUpdate,
}: {
  apiKey: APIKey;
  isExpanded: boolean;
  onToggle: () => void;
  onRevoke: (apiKeyId: string) => void;
  onUpdate: (
    apiKeyId: string,
    update: { name: string | null; scopes: APIKeyScope[] },
  ) => Promise<boolean>;
}) {
  const [draftName, setDraftName] = useState(apiKey.name ?? '');
  const [draftScopes, setDraftScopes] = useState<APIKeyScope[]>(apiKey.scopes);
  const [isSaving, setIsSaving] = useState(false);

  // discard the draft whenever the saved key changes or the row is closed
  useEffect(() => {
    setDraftName(apiKey.name ?? '');
    setDraftScopes(apiKey.scopes);
  }, [apiKey, isExpanded]);

  const isDirty =
    draftName.trim() !== (apiKey.name ?? '') ||
    !sameScopes(draftScopes, apiKey.scopes);

  async function handleUpdate() {
    setIsSaving(true);
    const updated = await onUpdate(apiKey.id, {
      name: draftName.trim() || null,
      scopes: draftScopes,
    });
    setIsSaving(false);
    if (updated) onToggle();
  }

  return (
    <li className="flex flex-col gap-2 p-3 border border-gray-200 rounded-md bg-white">
      <div className="flex flex-row items-center justify-between gap-2">
        <div className="flex flex-col gap-1 min-w-0">
          <span className="font-semibold truncate">
            {apiKey.name || 'Unnamed key'}
          </span>
          <ScopeBadges scopes={apiKey.scopes} />
        </div>
        <div className="flex flex-row items-center gap-3 shrink-0">
          <HintText>Last used {formatDate(apiKey.last_used_at)}</HintText>
          <button
            type="button"
            className="flex items-center gap-1 text-sm text-accent3 hover:underline"
            aria-expanded={isExpanded}
            onClick={onToggle}
          >
            {isExpanded ? 'Close' : 'Edit'}
            {isExpanded ? (
              <ChevronUpIcon className="w-4 h-4" />
            ) : (
              <ChevronDownIcon className="w-4 h-4" />
            )}
          </button>
          <ConfirmationModal
            btnName="Revoke"
            btnType="trashIcon"
            title="Revoke this API key?"
            content="Any application using this key will immediately lose access. This cannot be undone."
            confirmText="Revoke"
            rejectText="Cancel"
            onConfirm={() => onRevoke(apiKey.id)}
          />
        </div>
      </div>
      {isExpanded && (
        <div className="flex flex-col gap-2 pt-2 border-t border-gray-200">
          <div className="flex flex-row items-center justify-between gap-2 px-2 bg-gray-200">
            <span className="font-mono text-sm truncate">{apiKey.api_key}</span>
            <button
              type="button"
              title="Copy API key"
              onClick={() => navigator.clipboard.writeText(apiKey.api_key)}
            >
              <span className="sr-only">Copy API key</span>
              <DocumentDuplicateIcon className="w-4 h-4 shrink-0" />
            </button>
          </div>
          <label className={styles.label} htmlFor={`api-key-${apiKey.id}-name`}>
            Name
          </label>
          <input
            id={`api-key-${apiKey.id}-name`}
            className={styles.inputText}
            type="text"
            maxLength={64}
            placeholder="Unnamed key"
            value={draftName}
            onChange={(e) => setDraftName(e.target.value)}
            disabled={isSaving}
          />
          <ScopeCheckboxes
            idPrefix={`api-key-${apiKey.id}`}
            scopes={draftScopes}
            onChange={setDraftScopes}
            disabled={isSaving}
          />
          {isDirty && (
            <HintText>You have unsaved changes to this key.</HintText>
          )}
          <div className="flex flex-row gap-2">
            <div className="flex-1">
              <Button
                type="button"
                size="sm"
                disabled={isSaving || !isDirty}
                onClick={handleUpdate}
              >
                {isSaving ? 'Updating...' : 'Update'}
              </Button>
            </div>
            <div className="flex-1">
              <Button
                type="button"
                size="sm"
                cancel={true}
                disabled={isSaving}
                onClick={onToggle}
              >
                Cancel
              </Button>
            </div>
          </div>
          <HintText>Created {formatDate(apiKey.created_at)}</HintText>
        </div>
      )}
    </li>
  );
}

export default function APIKeyManager({
  setStatus,
}: {
  setStatus: React.Dispatch<React.SetStateAction<Status | null>>;
}) {
  const [apiKeys, setAPIKeys] = useState<APIKey[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  // shown inside this component so a load failure does not surface on other
  // profile tabs that share setStatus
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  // only one key is expanded for editing at a time
  const [expandedKeyId, setExpandedKeyId] = useState<string | null>(null);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyScopes, setNewKeyScopes] = useState<APIKeyScope[]>(['read']);

  const fetchAPIKeys = useCallback(async () => {
    try {
      const response: AxiosResponse<APIKey[]> = await api.get('/api-keys');
      setAPIKeys(response.data);
      setLoadError(null);
    } catch (err) {
      setLoadError(getErrorMessage(err, 'Unable to load API keys'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAPIKeys();
  }, [fetchAPIKeys]);

  async function createAPIKey() {
    setStatus(null);
    setIsCreating(true);
    try {
      const response: AxiosResponse<APIKey> = await api.post('/api-keys', {
        name: newKeyName.trim() || null,
        scopes: newKeyScopes,
      });
      setNewKeyName('');
      setNewKeyScopes(['read']);
      await fetchAPIKeys();
      // open the new key so its value can be copied right away
      setExpandedKeyId(response.data.id);
    } catch (err) {
      setStatus({
        type: 'error',
        msg: getErrorMessage(err, 'Unable to create API key'),
      });
    } finally {
      setIsCreating(false);
    }
  }

  async function updateAPIKey(
    apiKeyId: string,
    update: { name: string | null; scopes: APIKeyScope[] },
  ): Promise<boolean> {
    setStatus(null);
    try {
      const response: AxiosResponse<APIKey> = await api.patch(
        `/api-keys/${apiKeyId}`,
        update,
      );
      setAPIKeys((keys) =>
        keys.map((key) => (key.id === apiKeyId ? response.data : key)),
      );
      setStatus({
        type: 'success',
        msg: `API key "${response.data.name || 'Unnamed key'}" updated`,
      });
      return true;
    } catch (err) {
      setStatus({
        type: 'error',
        msg: getErrorMessage(err, 'Unable to update API key'),
      });
      return false;
    }
  }

  async function revokeAPIKey(apiKeyId: string) {
    setStatus(null);
    try {
      await api.delete(`/api-keys/${apiKeyId}`);
      setAPIKeys((keys) => keys.filter((key) => key.id !== apiKeyId));
    } catch (err) {
      setStatus({
        type: 'error',
        msg: getErrorMessage(err, 'Unable to revoke API key'),
      });
    }
  }

  const readKey = apiKeys.find((key) => key.scopes.includes('read'));
  const exampleURL = `${
    window.location.origin
  }/static/projects/1/flights/1/data_products/1/mygeotiff.tif?API_KEY=${
    readKey ? readKey.api_key : 'MYKEY'
  }`;
  const atLimit = apiKeys.length >= MAX_ACTIVE_API_KEYS;

  return (
    <div className="flex flex-col gap-4">
      <span className="text-xl font-semibold">API Key Access</span>
      <p className="text-sm">
        Your API keys are sensitive credentials that can be used to access your
        data stored on {import.meta.env.VITE_BRAND_SHORT}. Please keep them
        secure and do not share them with anyone. If you suspect unauthorized
        access using an API key, revoke it using this form and create a new one.
      </p>
      <HintText>
        Each key can have any combination of four permissions. Read lets it view
        data and download files. Create lets it add new records. Update lets it
        change existing records. Delete lets it remove records. Give a key only
        the permissions it needs; for example, a key built into a mobile app
        that only submits new records should have Create alone. You can change a
        key's permissions at any time.
      </HintText>

      {isLoading ? (
        <span className="text-sm">Loading API keys...</span>
      ) : loadError ? (
        <Alert alertType="error">{loadError}</Alert>
      ) : (
        <div className="flex flex-col gap-2">
          <div className="flex flex-row items-center justify-between">
            <span className="font-semibold">Your API keys</span>
            <HintText>
              {apiKeys.length} of {MAX_ACTIVE_API_KEYS} keys
            </HintText>
          </div>
          {apiKeys.length > 0 ? (
            <ul className="flex flex-col gap-2">
              {apiKeys.map((apiKey) => (
                <APIKeyRow
                  key={apiKey.id}
                  apiKey={apiKey}
                  isExpanded={expandedKeyId === apiKey.id}
                  onToggle={() =>
                    setExpandedKeyId((id) =>
                      id === apiKey.id ? null : apiKey.id,
                    )
                  }
                  onRevoke={revokeAPIKey}
                  onUpdate={updateAPIKey}
                />
              ))}
            </ul>
          ) : (
            <span className="text-sm">You do not have any API keys.</span>
          )}
        </div>
      )}

      {atLimit ? (
        <Alert alertType="info">
          You have reached the maximum of {MAX_ACTIVE_API_KEYS} API keys. Revoke
          a key to create a new one.
        </Alert>
      ) : (
        <div className="flex flex-col gap-2 p-3 border border-gray-200 rounded-md">
          <span className="font-semibold">Create API key</span>
          <label className={styles.label} htmlFor="new-api-key-name">
            Name (optional)
          </label>
          <input
            id="new-api-key-name"
            className={styles.inputText}
            type="text"
            maxLength={64}
            placeholder="e.g. QGIS"
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
          />
          <ScopeCheckboxes
            idPrefix="new-api-key"
            scopes={newKeyScopes}
            onChange={setNewKeyScopes}
          />
          <Button
            type="button"
            size="sm"
            disabled={isCreating || newKeyScopes.length === 0}
            onClick={createAPIKey}
          >
            {isCreating ? 'Creating...' : 'Create API Key'}
          </Button>
        </div>
      )}

      <div className="flex flex-col gap-1.5">
        <span className="italic text-sm">
          Example usage (requires a key with read access):
        </span>
        <div className="p-4 text-sm bg-gray-200 overflow-x-auto">
          <span>{exampleURL}</span>
        </div>
      </div>
    </div>
  );
}
