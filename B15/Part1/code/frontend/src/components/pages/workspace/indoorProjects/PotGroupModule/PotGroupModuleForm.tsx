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
  PotGroupModuleFormData,
  PotGroupModuleFormProps,
} from '../IndoorProject';

import {
  cameraOrientationOptions,
  plottedByOptions,
  groupsAccordingToOptions,
} from '../formOptions';

import defaultValues from './defaultValues';
import { fetchPotGroupModuleVisualizationData } from './service';
import validationSchema from './validationSchema';

export default function PotGroupModuleForm({
  indoorProjectId,
  indoorProjectDataId,
  potBarcodes,
  setVisualizationData,
}: PotGroupModuleFormProps) {
  // Initialize the form
  const methods = useForm<PotGroupModuleFormData>({
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
  const onSubmit: SubmitHandler<PotGroupModuleFormData> = async (values) => {
    setVisualizationData(null);

    if (!indoorProjectDataId) return;

    const selectedAccordingTo = values.accordingTo;
    const numericBarcode = Number(selectedAccordingTo);
    const isSinglePot =
      selectedPlottedBy === 'pots' &&
      selectedAccordingTo !== 'all' &&
      Number.isFinite(numericBarcode);

    const data = await fetchPotGroupModuleVisualizationData({
      indoorProjectId,
      indoorProjectDataId,
      cameraOrientation: values.cameraOrientation,
      plottedBy: values.plottedBy,
      accordingTo: isSinglePot ? 'single_pot' : values.accordingTo,
      potBarcode: isSinglePot ? numericBarcode : undefined,
    });
    setVisualizationData(data);
  };

  return (
    <div className="my-2">
      <span className="block font-bold">HSV Visualization Options</span>
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
