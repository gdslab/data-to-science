import { useEffect } from 'react';
import {
  FormProvider,
  SubmitHandler,
  useForm,
  useWatch,
} from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';

import { SelectField } from '../../../../FormFields';
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

  // Filter out already selected traits to avoid duplication
  const targetTraitXOptions = targetTraitOptions.filter(
    (option) => option.value !== selectedTraitY
  );

  const targetTraitYOptions = targetTraitOptions.filter(
    (option) => option.value !== selectedTraitX
  );

  // Clear Y trait if it becomes the same as X trait or if it's no longer valid
  useEffect(() => {
    if (selectedTraitX && selectedTraitY && selectedTraitX === selectedTraitY) {
      methods.setValue('targetTraitY', '');
    }

    // Also clear Y trait if its current value is no longer in the available options
    if (
      selectedTraitY &&
      !targetTraitYOptions.some((option) => option.value === selectedTraitY)
    ) {
      methods.setValue('targetTraitY', '');
    }
  }, [selectedTraitX, selectedTraitY, targetTraitYOptions, methods]);

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
            <SelectField
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
