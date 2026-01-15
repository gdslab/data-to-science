import { isAxiosError } from 'axios';
import { useEffect, useState } from 'react';
import {
  FormProvider,
  SubmitHandler,
  useForm,
  useWatch,
} from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';

import { SelectField, RadioField } from '../../../../FormFields';
import Alert, { Status } from '../../../../Alert';
import { TraitModuleFormData, TraitModuleFormProps } from '../IndoorProject';

import {
  cameraOrientationOptions,
  plottedByOptions,
  groupsAccordingToOptions,
} from '../formOptions';

import defaultValues from './defaultValues';
import { fetchTraitModuleVisualizationData } from './service';
import validationSchema from './validationSchema';

export default function TraitModuleForm({
  indoorProjectId,
  indoorProjectDataId,
  numericColumns,
  potBarcodes,
  setVisualizationData,
}: TraitModuleFormProps) {
  // Status for error/success messages
  const [status, setStatus] = useState<Status | null>(null);

  // Initialize the form
  const methods = useForm<TraitModuleFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });

  // Get the form methods
  const {
    control,
    setValue,
    formState: { isSubmitting },
    handleSubmit,
  } = methods;

  // Get the selected camera orientation
  const selectedCameraOrientation = useWatch({
    control,
    name: 'cameraOrientation',
  });

  // Get the selected plotted by option
  const selectedPlottedBy = useWatch({
    control,
    name: 'plottedBy',
  });

  // Reset accordingTo when plottedBy changes
  useEffect(() => {
    if (selectedPlottedBy === 'groups') {
      setValue('accordingTo', 'treatment');
    } else if (selectedPlottedBy === 'pots') {
      setValue('accordingTo', 'all');
    }
  }, [selectedPlottedBy, setValue]);

  // Only show the numeric target trait options for the selected camera orientation
  const targetTraitOptions =
    selectedCameraOrientation === 'top'
      ? numericColumns.top.map((col) => ({ label: col, value: col }))
      : numericColumns.side.map((col) => ({ label: col, value: col }));

  // Dynamic according to options based on plotted by selection
  const accordingToOptions =
    selectedPlottedBy === 'groups'
      ? groupsAccordingToOptions
      : [{ label: 'All', value: 'all' }].concat(
          (Array.isArray(potBarcodes) ? potBarcodes : []).map((bc) => ({
            label: String(bc),
            value: String(bc),
          }))
        );

  // Handle the form submission
  const onSubmit: SubmitHandler<TraitModuleFormData> = async (values) => {
    setStatus(null); // Clear any previous status
    setVisualizationData(null);

    if (!indoorProjectDataId) return;

    try {
      const numericBarcode = Number(values.accordingTo);
      const isSinglePot =
        selectedPlottedBy === 'pots' &&
        values.accordingTo !== 'all' &&
        Number.isFinite(numericBarcode);

      const data = await fetchTraitModuleVisualizationData({
        indoorProjectId,
        indoorProjectDataId,
        cameraOrientation: values.cameraOrientation,
        plottedBy: values.plottedBy,
        accordingTo: isSinglePot ? 'single_pot' : values.accordingTo,
        targetTrait: values.targetTrait,
        potBarcode: isSinglePot ? numericBarcode : undefined,
      });
      setVisualizationData(data);
    } catch (error) {
      // Handle different types of errors
      if (isAxiosError(error)) {
        setStatus({
          type: 'error',
          msg:
            error.response?.data?.detail ||
            'Failed to fetch trait visualization data',
        });
      } else {
        setStatus({
          type: 'error',
          msg: 'An unexpected error occurred while processing your request',
        });
      }
    }
  };

  return (
    <div className="my-2">
      <span className="block font-bold">Trait Visualization Options</span>
      <FormProvider {...methods}>
        <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
          <div className="flex items-start gap-8">
            {/* Camera Orientation */}
            <RadioField
              label="Camera Orientation"
              name="cameraOrientation"
              options={cameraOrientationOptions}
            />
            {/* Plotted By */}
            <RadioField
              label="Plotted By"
              name="plottedBy"
              options={plottedByOptions}
            />
            {/* According To */}
            <SelectField
              label="According To"
              name="accordingTo"
              options={accordingToOptions}
            />
            {/* Target Trait */}
            <SelectField
              label="Target Trait"
              name="targetTrait"
              options={targetTraitOptions}
            />
          </div>
          {/* Submit button */}
          <div className="w-48">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full px-4 py-2 bg-blue-500 text-white font-medium rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-blue-500/60 disabled:cursor-not-allowed"
            >
              {!isSubmitting ? 'Plot Trait Values' : 'Plotting trait values...'}
            </button>
          </div>
        </form>
      </FormProvider>
      {status && (
        <div className="mt-4">
          <Alert alertType={status.type}>{status.msg}</Alert>
        </div>
      )}
    </div>
  );
}
