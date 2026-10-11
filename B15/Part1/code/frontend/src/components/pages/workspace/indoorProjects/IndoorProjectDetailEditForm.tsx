import { isAxiosError } from 'axios';
import { useContext, useEffect, useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useRevalidator } from 'react-router';
import { yupResolver } from '@hookform/resolvers/yup';

import AuthContext from '../../../../AuthContext';

import api from '../../../../api';
import Alert, { Status } from '../../../Alert';
import { LinkButton } from '../../../Buttons';
import { IndoorProjectAPIResponse } from './IndoorProject.d';
import { IndoorProjectFormInput, validationSchema } from './IndoorProjectForm';
import { InputField, SelectField } from '../../../FormFields';
import Table, { TableBody, TableHead } from '../../../Table';
import { useIndoorProjectContext } from './IndoorProjectContext';
import { Team } from '../../teams/Teams';

type IndoorProjectDetailEditFormProps = {
  indoorProject: IndoorProjectAPIResponse;
  teams: Team[];
};

export default function IndoorProjectDetailEditForm({
  indoorProject,
  teams,
}: IndoorProjectDetailEditFormProps) {
  const { id, ...defaultValues } = indoorProject;

  const [status, setStatus] = useState<Status | null>(null);
  const revalidator = useRevalidator();
  const { user } = useContext(AuthContext);

  const {
    state: { projectMembers },
  } = useIndoorProjectContext();

  const methods = useForm<IndoorProjectFormInput>({
    defaultValues: {
      ...defaultValues,
      startDate: defaultValues.start_date
        ? new Date(defaultValues.start_date).toISOString().split('T')[0]
        : undefined,
      endDate: defaultValues.end_date
        ? new Date(defaultValues.end_date).toISOString().split('T')[0]
        : undefined,
      teamId: indoorProject.team_id || 'no_team',
    },
    resolver: yupResolver(validationSchema),
    mode: 'onChange',
    reValidateMode: 'onChange',
  });

  const {
    formState: { isSubmitting },
    handleSubmit,
    trigger,
    reset,
  } = methods;

  // Update form when indoorProject prop changes (e.g., after upload)
  useEffect(() => {
    reset({
      title: indoorProject.title,
      description: indoorProject.description,
      startDate: indoorProject.start_date
        ? new Date(indoorProject.start_date).toISOString().split('T')[0]
        : undefined,
      endDate: indoorProject.end_date
        ? new Date(indoorProject.end_date).toISOString().split('T')[0]
        : undefined,
      teamId: indoorProject.team_id || 'no_team',
    });
  }, [indoorProject, reset]);

  const onSubmit: SubmitHandler<IndoorProjectFormInput> = async (values) => {
    setStatus(null);

    try {
      const { title, description, startDate, endDate, teamId } = values;
      const payload = {
        title,
        description,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        team_id: teamId && teamId !== 'no_team' ? teamId : null,
      };

      await api.put(`/indoor_projects/${id}`, payload);
      setStatus({
        type: 'success',
        msg: 'Indoor project updated successfully',
      });
      revalidator.revalidate();
    } catch (err) {
      if (isAxiosError(err)) {
        setStatus({
          type: 'error',
          msg: err.response?.data.detail || 'Unable to update indoor project',
        });
      } else {
        setStatus({ type: 'error', msg: 'Unable to update indoor project' });
      }
    }
  };

  // Check if current user has owner permissions
  const hasOwnerPermissions =
    projectMembers?.find((member) => member.email === user?.email)?.role ===
    'owner';

  return (
    <div className="flex flex-col gap-4">
      <FormProvider {...methods}>
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="flex justify-between">
            <div className="grid rows-auto gap-2">
              <span className="text-lg font-bold mb-0">
                {indoorProject.title}
              </span>
              <div className="block my-1 mx-0 text-gray-600 text-wrap break-all">
                {indoorProject.description}
              </div>
            </div>
          </div>

          <Table>
            <TableHead
              columns={['Title', 'Description', 'Start Date', 'End Date', 'Team']}
            />
            <TableBody
              rows={[
                {
                  key: indoorProject.id,
                  values: [
                    <div className="flex justify-center">
                      <InputField label="Title" name="title" />
                    </div>,
                    <div className="flex justify-center">
                      <InputField label="Description" name="description" />
                    </div>,
                    <div className="flex justify-center">
                      <InputField
                        label="Start Date"
                        type="date"
                        name="startDate"
                        onChange={() => setTimeout(() => trigger('endDate'), 0)}
                      />
                    </div>,
                    <div className="flex justify-center">
                      <InputField
                        label="End Date"
                        type="date"
                        name="endDate"
                        onChange={() =>
                          setTimeout(() => trigger('startDate'), 0)
                        }
                      />
                    </div>,
                    <div className="flex justify-center">
                      <SelectField
                        label="Team"
                        name="teamId"
                        required={false}
                        options={teams.map((team) => ({
                          label: team.title,
                          value: team.id,
                        }))}
                      />
                    </div>,
                  ],
                },
              ]}
            />
          </Table>

          <div className="mt-4 flex justify-between items-center">
            <button
              className="px-4 py-2 bg-blue-600 text-white font-medium rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Updating...' : 'Update Project'}
            </button>

            {hasOwnerPermissions && (
              <div className="flex flex-row gap-4">
                <LinkButton
                  url={`/indoor_projects/${indoorProject.id}/access`}
                  size="sm"
                >
                  Manage Access
                </LinkButton>
              </div>
            )}
          </div>

          {status && status.type && status.msg && (
            <div className="mt-4">
              <Alert alertType={status.type}>{status.msg}</Alert>
            </div>
          )}
        </form>
      </FormProvider>
    </div>
  );
}
