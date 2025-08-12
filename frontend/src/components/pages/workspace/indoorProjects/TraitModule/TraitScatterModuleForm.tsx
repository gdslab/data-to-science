import { useEffect } from 'react';
import {
  FormProvider,
  SubmitHandler,
  useForm,
  useWatch,
} from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';

import { SelectField, RadioField } from '../../../../FormFields';
import {
  TraitScatterModuleFormData,
  TraitScatterModuleFormProps,
} from '../IndoorProject';

import { cameraOrientationOptions, groupByOptions } from '../formOptions';

import scatterDefaultValues from './scatterDefaultValues';
import { fetchTraitScatterModuleVisualizationData } from './scatterService';
import scatterValidationSchema from './scatterValidationSchema';

export default function TraitScatterModuleForm({
  indoorProjectId,
  indoorProjectDataId,
  numericColumns,
  setVisualizationData,
}: TraitScatterModuleFormProps) {
  // Initialize the form
  const methods = useForm<TraitScatterModuleFormData>({
    defaultValues: scatterDefaultValues,
    resolver: yupResolver(scatterValidationSchema),
    mode: 'onSubmit', // Only validate on submit to prevent loops
  });

  // Get the form methods
  const {
    control,
    formState: { isSubmitting },
    handleSubmit,
  } = methods;

  // Get the selected camera orientation
  const selectedCameraOrientation = useWatch({
    control,
    name: 'cameraOrientation',
  });

  // Get selected traits to avoid duplication
  const selectedTraitX = useWatch({
    control,
    name: 'targetTraitX',
  });

  const selectedTraitY = useWatch({
    control,
    name: 'targetTraitY',
  });

  // Only show the numeric target trait options for the selected camera orientation
  const targetTraitOptions =
    selectedCameraOrientation === 'top'
      ? numericColumns.top.map((col) => ({ label: col, value: col }))
      : numericColumns.side.map((col) => ({ label: col, value: col }));

  // Use the same options for both X and Y traits (no filtering)
  const targetTraitXOptions = targetTraitOptions;
  const targetTraitYOptions = targetTraitOptions;

  // Handle the form submission
  const onSubmit: SubmitHandler<TraitScatterModuleFormData> = async (
    values
  ) => {
    setVisualizationData(null);

    if (!indoorProjectDataId) return;

    try {
      const data = await fetchTraitScatterModuleVisualizationData({
        indoorProjectId,
        indoorProjectDataId,
        cameraOrientation: values.cameraOrientation,
        groupBy: values.groupBy,
        targetTraitX: values.targetTraitX,
        targetTraitY: values.targetTraitY,
      });
      setVisualizationData(data);
    } catch (error) {
      throw error;
    }
  };

  return (
    <div className="my-2">
      <span className="block font-bold">Trait Scatter Plot Options</span>
      <FormProvider {...methods}>
        <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
          <div className="flex items-start gap-8">
            {/* Camera Orientation */}
            <RadioField
              label="Camera Orientation"
              name="cameraOrientation"
              options={cameraOrientationOptions}
            />
            {/* Group By */}
            <SelectField
              label="Group By"
              name="groupBy"
              options={groupByOptions}
            />
            {/* X Axis Trait */}
            <SelectField
              label="X Axis Trait"
              name="targetTraitX"
              options={targetTraitXOptions}
            />
            {/* Y Axis Trait */}
            <SelectField
              label="Y Axis Trait"
              name="targetTraitY"
              options={targetTraitYOptions}
            />
          </div>
          {/* Submit button */}
          <div className="w-48">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full px-4 py-2 bg-purple-500 text-white font-medium rounded hover:bg-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-300 disabled:bg-purple-500/60 disabled:cursor-not-allowed"
            >
              {!isSubmitting
                ? 'Generate Scatter Plot'
                : 'Generating scatter plot...'}
            </button>
          </div>
        </form>
      </FormProvider>
    </div>
  );
}
