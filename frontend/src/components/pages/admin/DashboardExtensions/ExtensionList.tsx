import { useEffect } from 'react';
import { useRevalidator } from 'react-router';

import { Status } from '../../../Alert';

import api from '../../../../api';

export type Extension = {
  id: string;
  description: string;
  name: string;
};

export type ExtensionListProps = {
  extensions: Extension[];
  selectedExtensions: string[];
  setStatus: React.Dispatch<React.SetStateAction<Status | null>>;
  teamId?: string;
  userId?: string;
};

export default function ExtensionList({
  extensions,
  selectedExtensions,
  setStatus,
  teamId,
  userId,
}: ExtensionListProps) {
  const revalidator = useRevalidator();

  useEffect(() => {
    setStatus(null);
  }, [setStatus]);

  if (!teamId && !userId) {
    console.error('Must provide team or user id');
    return;
  }

  async function handleOnChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (teamId) {
      // send api request to toggle on extension for team
      try {
        const payload = {
          team_id: teamId,
          extension_id: e.target.value,
          is_active: e.target.checked,
        };
        const response = await api.put('/admin/extensions/team', payload);
        if (response.status === 200) {
          revalidator.revalidate();
        } else {
          // update status
          setStatus({ type: 'error', msg: 'Unable to change extension' });
        }
      } catch (err) {
        console.error(err);
        setStatus({ type: 'error', msg: 'Unable to change extension' });
      }
    }
    if (userId) {
      // send api request to toggle on extension for user
      try {
        const payload = {
          user_id: userId,
          extension_id: e.target.value,
          is_active: e.target.checked,
        };
        const response = await api.put('/admin/extensions/user', payload);
        if (response.status === 200) {
          revalidator.revalidate();
        } else {
          // update status
          setStatus({ type: 'error', msg: 'Unable to change extension' });
        }
      } catch (err) {
        console.error(err);
        setStatus({ type: 'error', msg: 'Unable to change extension' });
      }
    }
  }

  return (
    <div className="flex justify-center gap-4">
      {extensions.map((extension) => (
        <div key={extension.id} className="flex items-center">
          <input
            type="checkbox"
            id={extension.id}
            name={extension.name}
            value={extension.id}
            className="w-4 h-4 text-accent2 accent-slate-600 bg-gray-100 border-gray-300 rounded-sm focus:ring-accent2/70 focus:ring-2"
            onChange={handleOnChange}
            checked={selectedExtensions.includes(extension.name)}
          />
          <label
            htmlFor={extension.id}
            className="ms-2 text-sm font-medium text-gray-900"
            title={extension.description}
          >
            {extension.name}
          </label>
        </div>
      ))}
    </div>
  );
}
