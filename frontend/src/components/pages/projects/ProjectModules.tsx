import { AxiosResponse, isAxiosError } from 'axios';
import { useContext, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { CheckIcon } from '@heroicons/react/24/outline';

import { AlertBar } from '../../Alert';
import Table, { TableBody, TableHead } from '../../Table';
import { ProjectModule } from './Project';
import { useProjectContext } from './ProjectContext';

import api from '../../../api';
import { classNames } from '../../utils';

export default function ProjectModules() {
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const { projectRole, projectModules, projectModulesDispatch } =
    useProjectContext();
  const params = useParams();

  useEffect(() => {
    // limit access to project owners
    if (projectRole && projectRole === 'owner') {
      setIsLoading(false);
    }
  }, [projectRole]);

  async function updateModuleEnabled(moduleName: string, enabled: boolean) {
    if (!projectModules) return;

    try {
      const response: AxiosResponse<ProjectModule> = await api.put(
        `/projects/${params.projectId}/modules/${moduleName}`,
        { enabled }
      );
      if (response.status === 200) {
        // Update the modules in context
        projectModulesDispatch({
          type: 'set',
          payload: projectModules.map((module) =>
            module.module_name === moduleName
              ? { ...module, enabled: response.data.enabled }
              : module
          ),
        });
      }
    } catch (err) {
      if (isAxiosError(err)) {
        setError(err.response?.data.detail);
      } else {
        setError('Unable to update module status');
      }
    }
  }

  if (isLoading) {
    return <div className="p-4">Loading...</div>;
  }

  if (!projectModules) {
    return <div className="p-4">Unable to find project modules</div>;
  }

  return (
    <div className="flex flex-col p-4">
      <div>
        <h1>Project Modules</h1>
        <p className="text-gray-600 mb-4">
          Enable or disable modules for this project. Required modules cannot be
          disabled.
        </p>
      </div>
      <div className="overflow-x-auto">
        <div className="grow min-h-0 min-w-[800px]">
          <Table>
            <TableHead
              align="left"
              columns={['Module', 'Description', 'Required', 'Status']}
            />
            <div className="overflow-y-auto max-h-96 xl:max-h-[420px] 2xl:max-h-[512px]">
              <TableBody
                align="left"
                rows={projectModules.map((module) => ({
                  key: module.module_name,
                  values: [
                    <span className="font-medium">
                      {module.label || module.module_name}
                    </span>,
                    <span className="text-gray-600">
                      {module.description || 'No description available'}
                    </span>,
                    <span>{module.required ? 'Yes' : 'No'}</span>,
                    <div className="flex items-center justify-between gap-6">
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={module.enabled}
                          onChange={(e) =>
                            updateModuleEnabled(
                              module.module_name,
                              e.target.checked
                            )
                          }
                          disabled={module.required}
                          className="h-4 w-4 rounded border-gray-300 text-accent3 focus:ring-accent3"
                        />
                        <span
                          className={classNames(
                            module.enabled ? 'text-green-600' : 'text-gray-500',
                            'font-medium'
                          )}
                        >
                          {module.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                      </div>
                    </div>,
                  ],
                }))}
              />
            </div>
          </Table>
        </div>
      </div>
      {error ? <AlertBar alertType="error">{error}</AlertBar> : null}
    </div>
  );
}
