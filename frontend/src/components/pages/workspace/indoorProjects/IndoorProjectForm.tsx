import { AxiosResponse, isAxiosError } from 'axios';
import React, { useEffect, useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useNavigate } from 'react-router';
import * as Yup from 'yup';
import { yupResolver } from '@hookform/resolvers/yup';

import api from '../../../../api';
import Alert, { Status } from '../../../Alert';
import { Button } from '../../../Buttons';
import { InputField, SelectField } from '../../../FormFields';

import { IndoorProjectAPIResponse } from './IndoorProject';
import { Team } from '../../teams/Teams';

export async function loader() {
  const response = await api.get('/teams', { params: { owner_only: true } });
  if (response) {
    const teams = response.data;
    teams.unshift({
      title: 'No team',
      id: 'no_team',
      is_owner: false,
      description: '',
      exts: [],
    });
    return teams;
  } else {
    return [];
  }
}

export type IndoorProjectFormInput = {
  title: string;
  description: string;
  startDate?: Date | string;
  endDate?: Date | string;
  teamId?: string;
};

const defaultValues = {
  title: '',
  description: '',
  teamId: 'no_team',
};

export const validationSchema = Yup.object({
  title: Yup.string()
    .max(255, 'Must be less than 255 characters')
    .required('Title is required'),
  description: Yup.string()
    .max(300, 'Must be less than 300 characters')
    .required('Description is required'),
  startDate: Yup.mixed<Date | string>()
    .transform((value, originalValue) =>
      originalValue === '' ? undefined : value
    )
    .test('date-max', 'Start date must be before end date', function (value) {
      const { endDate } = this.parent;
      if (!value || !endDate) return true;
      const startDateObj = typeof value === 'string' ? new Date(value) : value;
      const endDateObj =
        typeof endDate === 'string' ? new Date(endDate) : endDate;
      return startDateObj <= endDateObj;
    })
    .optional(),
  endDate: Yup.mixed<Date | string>()
    .transform((value, originalValue) =>
      originalValue === '' ? undefined : value
    )
    .test('date-min', 'End date must be after start date', function (value) {
      const { startDate } = this.parent;
      if (!value || !startDate) return true;
      const endDateObj = typeof value === 'string' ? new Date(value) : value;
      const startDateObj =
        typeof startDate === 'string' ? new Date(startDate) : startDate;
      return endDateObj >= startDateObj;
    })
    .optional(),
  teamId: Yup.string().optional(),
});

export default function IndoorProjectForm({
  setModalOpen,
}: {
  setModalOpen: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const [status, setStatus] = useState<Status | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);

  const navigate = useNavigate();

  const methods = useForm<IndoorProjectFormInput>({
    defaultValues,
    resolver: yupResolver(validationSchema),
    mode: 'onChange',
    reValidateMode: 'onChange',
  });

  const {
    formState: { isSubmitting },
    reset,
    handleSubmit,
  } = methods;

  const onSubmit: SubmitHandler<IndoorProjectFormInput> = async (values) => {
    try {
      const { title, description, teamId } = values;
      const payload = {
        title,
        description,
        team_id: teamId && teamId !== 'no_team' ? teamId : null,
      };

      const response: AxiosResponse<IndoorProjectAPIResponse> = await api.post(
        `/indoor_projects`,
        payload
      );

      if (response && response.status == 201) {
        navigate(`/indoor_projects/${response.data.id}`);
        setModalOpen(false);
      } else {
        setStatus({ type: 'error', msg: 'Unable to create indoor project' });
      }
    } catch (err) {
      if (isAxiosError(err)) {
        setStatus({
          type: 'error',
          msg: err.response?.data.detail || 'Unable to create indoor project',
        });
      } else {
        setStatus({ type: 'error', msg: 'Unable to create indoor project' });
      }
    }
  };

  useEffect(() => {
    async function loadTeams() {
      try {
        const teams = await loader();
        if (teams) setTeams(teams);
      } catch {
        setTeams([]);
      }
    }
    loadTeams();
  }, []);

  useEffect(() => {
    reset();
  }, [reset]);

  return (
    <div className="my-8 mx-4">
      <div className="mx-4 my-2">
        <h1>New Indoor Project</h1>
        <FormProvider {...methods}>
          <form
            className="flex flex-col gap-4"
            onSubmit={handleSubmit(onSubmit)}
          >
            <InputField label="Title" name="title" />
            <InputField label="Description" name="description" />
            <SelectField
              label="Team (Optional)"
              name="teamId"
              required={false}
              options={teams.map((team) => ({
                label: team.title,
                value: team.id,
              }))}
            />
            <div className="mt-4 flex flex-col gap-2">
              <Button type="submit" disabled={isSubmitting}>
                {!isSubmitting ? 'Create' : 'Creating...'}
              </Button>
              {status && status.type && status.msg && (
                <Alert alertType={status.type}>{status.msg}</Alert>
              )}
            </div>
          </form>
        </FormProvider>
      </div>
    </div>
  );
}
