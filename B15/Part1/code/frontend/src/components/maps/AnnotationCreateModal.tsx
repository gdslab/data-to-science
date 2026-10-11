import { isAxiosError } from 'axios';
import { useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import * as Yup from 'yup';
import { DialogTitle } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { yupResolver } from '@hookform/resolvers/yup';
import { Feature } from 'geojson';

import Alert, { Status } from '../Alert';
import { Button, OutlineButton } from '../Buttons';
import { InputField, TextAreaField } from '../FormFields';
import Modal from '../Modal';

import api from '../../api';
import { Visibility } from './contexts/AnnotationContext';
import { useMapContext } from './MapContext';

type AnnotationFormData = {
  description: string;
  tags: string;
  visibility: Visibility;
};

const validationSchema = Yup.object({
  description: Yup.string()
    .min(1, 'Description is required')
    .required('Description is required'),
  tags: Yup.string().optional().default(''),
  visibility: Yup.string()
    .oneOf(['OWNER', 'PROJECT'] as const)
    .required(),
});

const defaultValues: AnnotationFormData = {
  description: '',
  tags: '',
  visibility: 'OWNER',
};

interface AnnotationCreateModalProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  feature: Feature | null;
  projectId: string;
  flightId: string;
  dataProductId: string;
  onSuccess: () => void;
  onCancel: () => void;
}

export default function AnnotationCreateModal({
  open,
  setOpen,
  feature,
  projectId,
  flightId,
  dataProductId,
  onSuccess,
  onCancel,
}: AnnotationCreateModalProps) {
  const [status, setStatus] = useState<Status | null>(null);
  const { activeProject } = useMapContext();
  const isViewer = activeProject?.role === 'viewer';

  const methods = useForm<AnnotationFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });

  const {
    formState: { isSubmitting },
    handleSubmit,
    register,
    reset,
  } = methods;

  const onSubmit: SubmitHandler<AnnotationFormData> = async (values) => {
    if (!feature) return;
    setStatus(null);

    const tags = values.tags
      ? values.tags
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean)
      : [];

    try {
      await api.post(
        `/projects/${projectId}/flights/${flightId}/data_products/${dataProductId}/annotations`,
        {
          description: values.description,
          geom: feature,
          tags,
          visibility: values.visibility,
        }
      );
      reset();
      setStatus(null);
      setOpen(false);
      onSuccess();
    } catch (err) {
      if (isAxiosError(err)) {
        setStatus({
          type: 'error',
          msg: err.response?.data.detail || 'Unable to create annotation',
        });
      } else {
        setStatus({ type: 'error', msg: 'Unable to create annotation' });
      }
    }
  };

  const handleCancel = () => {
    reset();
    setStatus(null);
    setOpen(false);
    onCancel();
  };

  return (
    <Modal open={open} setOpen={() => handleCancel()} dismissible={false}>
      <div className="my-8 mx-4">
        <div className="mx-4 my-2">
          <div className="flex items-start justify-between gap-4 mb-4">
            <DialogTitle as="h2" className="text-lg font-bold">
              New Annotation
            </DialogTitle>
            <button
              type="button"
              aria-label="Close"
              className="shrink-0 rounded-lg border border-slate-300 p-1.5 text-slate-500 hover:text-slate-700"
              onClick={handleCancel}
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          </div>
          <FormProvider {...methods}>
            <form
              className="flex flex-col gap-4"
              onSubmit={handleSubmit(onSubmit)}
            >
              <TextAreaField
                label="Description"
                name="description"
                placeholder="Describe this annotation..."
                rows={4}
              />
              <InputField
                label="Tags"
                name="tags"
                required={false}
                placeholder="e.g. erosion, field-edge, note"
              />
              {isViewer ? (
                <p className="text-sm text-slate-500">
                  Visibility: <span className="font-medium">Personal</span>
                </p>
              ) : (
                <fieldset>
                  <legend className="text-sm font-medium text-gray-700">
                    Visibility
                  </legend>
                  <div className="mt-1 flex flex-col gap-2">
                    <label className="flex items-start gap-2 text-sm cursor-pointer">
                      <input
                        type="radio"
                        value="OWNER"
                        {...register('visibility')}
                        className="mt-0.5 h-4 w-4 text-primary border-gray-300 focus:ring-primary"
                      />
                      <span>
                        <span className="font-medium">Personal</span>
                        <span className="block text-xs text-slate-500">
                          Only you can view this annotation
                        </span>
                      </span>
                    </label>
                    <label className="flex items-start gap-2 text-sm cursor-pointer">
                      <input
                        type="radio"
                        value="PROJECT"
                        {...register('visibility')}
                        className="mt-0.5 h-4 w-4 text-primary border-gray-300 focus:ring-primary"
                      />
                      <span>
                        <span className="font-medium">Project</span>
                        <span className="block text-xs text-slate-500">
                          Anyone with access to the project can view this
                          annotation
                        </span>
                      </span>
                    </label>
                  </div>
                </fieldset>
              )}
              <div className="flex items-center justify-between mt-4">
                <div className="w-36">
                  <OutlineButton size="sm" type="button" onClick={handleCancel}>
                    Cancel
                  </OutlineButton>
                </div>
                <div className="w-36">
                  <Button type="submit" size="sm" disabled={isSubmitting}>
                    {isSubmitting ? 'Saving...' : 'Save'}
                  </Button>
                </div>
              </div>
              {status && status.type && status.msg && (
                <Alert alertType={status.type}>{status.msg}</Alert>
              )}
            </form>
          </FormProvider>
        </div>
      </div>
    </Modal>
  );
}