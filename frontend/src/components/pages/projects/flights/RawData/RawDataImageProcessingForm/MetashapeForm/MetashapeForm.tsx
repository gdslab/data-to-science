import { useForm, FormProvider, SubmitHandler } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';

import {
  CheckboxInput,
  NumberInput,
  RadioInput,
} from '../../../../../../RHFInputs';

import {
  MetashapeSettings,
  RawDataImageProcessingFormProps,
} from '../../RawData.types';

import defaultValues from './defaultValues';
import validationSchema from './validationSchema';

export default function MetashapeForm({
  onSubmitJob,
  toggleModal,
}: RawDataImageProcessingFormProps) {
  const methods = useForm<MetashapeSettings>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });
  const {
    handleSubmit,
    formState: { errors },
  } = methods;
  const onSubmit: SubmitHandler<MetashapeSettings> = (data) => {
    onSubmitJob(data);
    toggleModal();
  };

  return (
    <div className="bg-white/80 rounded-md p-4">
      <legend className="block text-lg text-gray-600 font-bold pt-2 pb-1">
        Image Processing Settings
      </legend>
      <FormProvider {...methods}>
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="flex gap-8">
            {/* Camera Options */}
            <fieldset className="border border-solid border-slate-300 p-3">
              <legend className="block text-gray-600 font-bold pt-2 pb-1">
                Camera Options
              </legend>
              <div>
                <RadioInput
                  fieldName="camera"
                  inputId="cameraSingle"
                  label="Single-camera"
                  value="single"
                />
              </div>
              <div>
                <RadioInput
                  fieldName="camera"
                  inputId="cameraMulti"
                  label="Multi-camera"
                  value="multi"
                />
              </div>
              {errors &&
                errors.camera &&
                typeof errors.camera.message === 'string' && (
                  <p className="text-sm text-red-500">
                    {errors.camera.message}
                  </p>
                )}
            </fieldset>
            {/* Align Photos */}
            <fieldset className="border border-solid border-slate-300 p-3">
              <legend className="block text-gray-600 font-bold pt-2 pb-1">
                Align Photos
              </legend>
              {/* Accuracy */}
              <div className="flex flex-col gap-1.5">
                <span className="text-sm font-medium">Accuracy</span>
                <div>
                  <RadioInput
                    fieldName="alignQuality"
                    inputId="alignQualityLow"
                    label="Low"
                    value="low"
                  />
                </div>
                <div>
                  <RadioInput
                    fieldName="alignQuality"
                    inputId="alignQualityMedium"
                    label="Medium"
                    value="medium"
                  />
                </div>
                <div>
                  <RadioInput
                    fieldName="alignQuality"
                    inputId="alignQualityHigh"
                    label="High"
                    value="high"
                  />
                </div>
                {errors &&
                  errors.alignQuality &&
                  typeof errors.alignQuality.message === 'string' && (
                    <p className="text-sm text-red-500">
                      {errors.alignQuality.message}
                    </p>
                  )}
              </div>
              {/* Key point and tie point limits */}
              <div className="flex flex-col gap-4 justify-start">
                <NumberInput
                  fieldName="keyPoint"
                  label="Key point limit"
                  step={1000}
                />
                <NumberInput
                  fieldName="tiePoint"
                  label="Tie point limit"
                  step={100}
                />
              </div>
            </fieldset>
            {/* Build Point Cloud */}
            <fieldset className="border border-solid border-slate-300 p-3">
              <legend className="block text-gray-600 font-bold pt-2 pb-1">
                Build Point Cloud
              </legend>
              {/* Quality */}
              <div className="flex flex-col gap-1.5">
                <span className="text-sm font-medium">Quality</span>
                <div>
                  <RadioInput
                    fieldName="buildDepthQuality"
                    inputId="buildDepthQualityLow"
                    label="Low"
                    value="low"
                  />
                </div>
                <div>
                  <RadioInput
                    fieldName="buildDepthQuality"
                    inputId="buildDepthQualityMedium"
                    label="Medium"
                    value="medium"
                  />
                </div>
                <div>
                  <RadioInput
                    fieldName="buildDepthQuality"
                    inputId="buildDepthQualityHigh"
                    label="High"
                    value="high"
                  />
                </div>
                {errors &&
                  errors.buildDepthQuality &&
                  typeof errors.buildDepthQuality.message === 'string' && (
                    <p className="text-sm text-red-500">
                      {errors.buildDepthQuality.message}
                    </p>
                  )}
              </div>
            </fieldset>
          </div>
          <div className="mt-4">
            <CheckboxInput fieldName="disclaimer" label="Check to proceed" />
            <div className="mt-4">
              <button
                className="w-32 bg-accent2/90 text-white font-semibold py-1 rounded enabled:hover:bg-accent2 disabled:opacity-75 disabled:cursor-not-allowed"
                type="submit"
              >
                Submit Job
              </button>
            </div>
          </div>
        </form>
      </FormProvider>
    </div>
  );
}
