import { useForm, FormProvider, SubmitHandler } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';

import {
  CheckboxInput,
  NumberInput,
  RadioInput,
} from '../../../../../../RHFInputs';

import {
  ODMSettings,
  RawDataImageProcessingFormProps,
} from '../../RawData.types';

import defaultValues from './defaultValues';
import validationSchema from './validationSchema';

export default function ODMForm({
  onSubmitJob,
  toggleModal,
}: RawDataImageProcessingFormProps) {
  const methods = useForm<ODMSettings>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });
  const {
    handleSubmit,
    formState: { errors },
  } = methods;
  const onSubmit: SubmitHandler<ODMSettings> = (data) => {
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
            {/* Ortho Resolution */}
            <fieldset className="border border-solid border-slate-300 p-3">
              <legend className="block text-gray-600 font-bold pt-2 pb-1">
                Orthophoto
              </legend>
              <div>
                <NumberInput
                  fieldName="orthoResolution"
                  label="Resolution (cm)"
                  min={1.0}
                  max={100.0}
                  step={0.1}
                />
              </div>
            </fieldset>
            {/* Point Cloud Quality */}
            <fieldset className="border border-solid border-slate-300 p-3">
              <legend className="block text-gray-600 font-bold pt-2 pb-1">
                Build Point Cloud
              </legend>
              <div className="flex flex-col gap-1.5">
                <span className="text-sm font-medium">Quality</span>
                <RadioInput
                  fieldName="pcQuality"
                  inputId="pcQualityLowest"
                  label="Lowest"
                  value="lowest"
                />
                <RadioInput
                  fieldName="pcQuality"
                  inputId="pcQualityLow"
                  label="Low"
                  value="low"
                />
                <RadioInput
                  fieldName="pcQuality"
                  inputId="pcQualityMedium"
                  label="Medium"
                  value="medium"
                />
                <RadioInput
                  fieldName="pcQuality"
                  inputId="pcQualityHigh"
                  label="High"
                  value="high"
                />
                <RadioInput
                  fieldName="pcQuality"
                  inputId="pcQualityUltra"
                  label="Ultra"
                  value="ultra"
                />
                {errors &&
                  errors.pcQuality &&
                  typeof errors.pcQuality.message === 'string' && (
                    <p className="text-sm text-red-500">
                      {errors.pcQuality.message}
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
