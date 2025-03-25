import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';

import { SelectField } from '../../../../FormFields';
import {
  PotGroupModuleFormData,
  PotGroupModuleFormProps,
} from '../IndoorProject';

import { cameraOrientationOptions, groupByOptions } from '../formOptions';

import defaultValues from './defaultValues';
import { fetchPotGroupModuleVisualizationData } from './service';
import validationSchema from './validationSchema';

export default function PotGroupModuleForm({
  indoorProjectId,
  indoorProjectDataId,
  setVisualizationData,
}: PotGroupModuleFormProps) {
  // Initialize the form
  const methods = useForm<PotGroupModuleFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });

  // Get the form methods
  const {
    formState: { isSubmitting },
    handleSubmit,
  } = methods;

  // Handle the form submission
  const onSubmit: SubmitHandler<PotGroupModuleFormData> = async (values) => {
    setVisualizationData(null);

    if (!indoorProjectDataId) return;

    try {
      const data = await fetchPotGroupModuleVisualizationData({
        indoorProjectId,
        indoorProjectDataId,
        cameraOrientation: values.cameraOrientation,
        groupBy: values.groupBy,
      });
      setVisualizationData(data);
    } catch (error) {
      throw error;
    }
  };

  return (
    <div className="my-2">
      <span className="block font-bold">HSV Visualization Options</span>
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
          </div>
          {/* Submit button */}
          <div className="w-48">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full px-4 py-2 bg-blue-500 text-white font-medium rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-blue-500/60 disabled:cursor-not-allowed"
            >
              {!isSubmitting ? 'Plot HSV values' : 'Plotting HSV values...'}
            </button>
          </div>
        </form>
      </FormProvider>
    </div>
  );
}
