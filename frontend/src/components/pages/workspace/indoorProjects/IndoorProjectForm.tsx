import axios, { AxiosResponse, isAxiosError } from 'axios';
import { useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import * as Yup from 'yup';
import { yupResolver } from '@hookform/resolvers/yup';

import Alert, { Status } from '../../../Alert';
import { Button } from '../../../Buttons';
import { InputField } from '../../../FormFields';
import Modal from '../../../Modal';

import { IndoorProjectAPIResponse } from './IndoorProject';

type IndoorProjectFormInput = {
  title: string;
  description: string;
  startDate?: Date;
  endDate?: Date;
};

const defaultValues = {
  title: '',
  description: '',
  startDate: undefined,
  endDate: undefined,
};

const validationSchema = Yup.object({
  title: Yup.string()
    .max(255, 'Must be less than 255 characters')
    .required('Title is required'),
  description: Yup.string()
    .max(300, 'Must be less than 300 characters')
    .required('Description is required'),
  startDate: Yup.date()
    .transform((value, originalValue) => (originalValue === '' ? undefined : value))
    .optional(),
  endDate: Yup.date()
    .min(Yup.ref('startDate'), 'End date must be after start date')
    .transform((value, originalValue) => (originalValue === '' ? undefined : value))
    .optional(),
});

export default function IndoorProjectForm() {
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);

  const navigate = useNavigate();

  const methods = useForm<IndoorProjectFormInput>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });

  const {
    formState: { isSubmitting },
    reset,
    handleSubmit,
  } = methods;

  const onSubmit: SubmitHandler<IndoorProjectFormInput> = async (values) => {
    try {
      const { title, description, startDate, endDate } = values;
      const payload = { title, description, start_date: startDate, end_date: endDate };

      const response: AxiosResponse<IndoorProjectAPIResponse> = await axios.post(
        `${import.meta.env.VITE_API_V1_STR}/indoor_projects`,
        payload
      );

      if (response && response.status == 201) {
        navigate(`/indoor_projects/${response.data.id}`);
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

  const handleClick = () => {
    reset();
    setStatus(null);
    setOpen(!open);
  };

  return (
    <div>
      <Button type="button" onClick={handleClick}>
        Create Indoor Project
      </Button>
      <Modal open={open} setOpen={setOpen}>
        <div className="mx-4 my-2">
          <h1>New Indoor Project</h1>
          <FormProvider {...methods}>
            <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
              <InputField label="Title" name="title" />
              <InputField label="Description" name="description" />
              <InputField type="date" label="Start date" name="startDate" />
              <InputField type="date" label="End date" name="endDate" />
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
      </Modal>
    </div>
  );
}
