import {
  FormProvider,
  SubmitHandler,
  useForm,
  useWatch,
} from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';

import { SelectField } from '../../../../FormFields';
import { TraitModuleFormData, TraitModuleFormProps } from '../IndoorProject';

import { cameraOrientationOptions, groupByOptions } from '../formOptions';

import defaultValues from './defaultValues';
import { fetchTraitModuleVisualizationData } from './service';
import validationSchema from './validationSchema';

export default function TraitModuleForm({
  indoorProjectId,
  indoorProjectDataId,
  numericColumns,
  setVisualizationData,
}: TraitModuleFormProps) {
  // Initialize the form
  const methods = useForm<TraitModuleFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
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

  // Only show the numeric target trait options for the selected camera orientation
  const targetTraitOptions =
    selectedCameraOrientation === 'top'
      ? numericColumns.top.map((col) => ({ label: col, value: col }))
      : numericColumns.side.map((col) => ({ label: col, value: col }));

  // Handle the form submission
  const onSubmit: SubmitHandler<TraitModuleFormData> = async (values) => {
    setVisualizationData(null);

    if (!indoorProjectDataId) return;

    try {
      const data = await fetchTraitModuleVisualizationData({
        indoorProjectId,
        indoorProjectDataId,
        cameraOrientation: values.cameraOrientation,
        groupBy: values.groupBy,
        targetTrait: values.targetTrait,
      });
      setVisualizationData(data);
    } catch (error) {
      throw error;
    }
  };

  return (
    <div className="my-2">
      <span className="block font-bold">Trait Visualization Options</span>
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
    </div>
  );
}
