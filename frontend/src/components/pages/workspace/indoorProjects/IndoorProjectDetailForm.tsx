import { isAxiosError } from 'axios';
import { useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';

import api from '../../../../api';
import Alert, { Status } from '../../../Alert';
import { IndoorProjectAPIResponse } from './IndoorProject';
import { IndoorProjectFormInput, validationSchema } from './IndoorProjectForm';
import { InputField } from '../../../FormFields';

type IndoorProjectDetailFormProps = {
  indoorProject: IndoorProjectAPIResponse;
};

export default function IndoorProjectDetailForm({
  indoorProject,
}: IndoorProjectDetailFormProps) {
  const { id, ...defaultValues } = indoorProject;

  const [status, setStatus] = useState<Status | null>(null);

  const methods = useForm<IndoorProjectFormInput>({
    defaultValues: {
      ...defaultValues,
      startDate: defaultValues.start_date
        ? (new Date(defaultValues.start_date)
            .toISOString()
            .split('T')[0] as any)
        : undefined,
      endDate: defaultValues.end_date
        ? (new Date(defaultValues.end_date).toISOString().split('T')[0] as any)
        : undefined,
    } as IndoorProjectFormInput,
    resolver: yupResolver(validationSchema) as any,
    mode: 'onChange',
    reValidateMode: 'onChange',
  });

  const {
    formState: { isSubmitting },
    handleSubmit,
    trigger,
  } = methods;

  const onSubmit: SubmitHandler<IndoorProjectFormInput> = async (values) => {
    setStatus(null);

    try {
      const { title, description, startDate, endDate } = values;
      const payload = {
        title,
        description,
        start_date: startDate,
        end_date: endDate,
      };

      await api.put(`/indoor_projects`, payload);
      setStatus({
        type: 'success',
        msg: 'Indoor project updated successfully',
      });
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

  return (
    <FormProvider {...methods}>
      <form
        className="flex items-center gap-4"
        onSubmit={handleSubmit(onSubmit)}
      >
        <InputField label="Title" name="title" />
        <InputField label="Description" name="description" />
        <InputField
          type="date"
          label="Start date"
          name="startDate"
          onChange={() => setTimeout(() => trigger('endDate'), 0)}
        />
        <InputField
          type="date"
          label="End date"
          name="endDate"
          onChange={() => setTimeout(() => trigger('startDate'), 0)}
        />
        <button
          className="max-h-10 px-4 py-2 bg-amber-500 text-white font-medium rounded hover:bg-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-300"
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Updating...' : 'Update'}
        </button>
      </form>
      {status && status.type && status.msg && (
        <Alert alertType={status.type}>{status.msg}</Alert>
      )}
    </FormProvider>
  );
}
