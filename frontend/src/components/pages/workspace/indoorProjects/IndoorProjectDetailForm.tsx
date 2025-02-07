import axios, { AxiosResponse, isAxiosError } from 'axios';
import { useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';

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
    defaultValues,
    resolver: yupResolver(validationSchema),
  });

  const {
    formState: { isSubmitting },
    // reset,
    handleSubmit,
  } = methods;

  const onSubmit: SubmitHandler<IndoorProjectFormInput> = async (values) => {
    try {
      const { title, description, startDate, endDate } = values;
      const payload = {
        title,
        description,
        start_date: startDate,
        end_date: endDate,
      };

      const response: AxiosResponse<IndoorProjectAPIResponse> = await axios.put(
        `${import.meta.env.VITE_API_V1_STR}/indoor_projects`,
        payload
      );
      const data = response.data;
      console.log(data);
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
        <InputField type="date" label="Start date" name="startDate" />
        <InputField type="date" label="End date" name="endDate" />
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
