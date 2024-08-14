import { useForm, FormProvider, SubmitHandler } from 'react-hook-form';
import * as yup from 'yup';
import { yupResolver } from '@hookform/resolvers/yup';

import { CheckboxInput, NumberInput, RadioInput } from './RHFInputs';

import { ImageProcessingSettings } from './RawData.types';

const defaultValues: ImageProcessingSettings = {
  alignQuality: 'medium',
  buildDepthQuality: 'medium',
  camera: 'single',
  disclaimer: false,
  keyPoint: 40000,
  tiePoint: 4000,
};

const schema = yup.object({
  alignQuality: yup
    .string()
    .oneOf(
      ['low', 'medium', 'high'],
      'Alignment accuracy must be "low", "medium", or "high"'
    )
    .required('Alignment accuracy is required'),
  buildDepthQuality: yup
    .string()
    .oneOf(
      ['low', 'medium', 'high'],
      'Build depth quality must be "low", "medium", or "high"'
    )
    .required('Build depth quality is required'),
  camera: yup
    .string()
    .oneOf(['single', 'multi'], 'Camera sensors must be single or multi')
    .required('Camera sensors is required'),
  disclaimer: yup
    .boolean()
    .oneOf([true], 'You must accept these terms before proceeding')
    .required('Accepting terms is required'),
  keyPoint: yup
    .number()
    .positive('Key point limit must be greater than 0')
    .required('Key point limit is required'),
  tiePoint: yup
    .number()
    .positive('Tie point limit must be greater than 0')
    .required('Tie point limit is required'),
});

type RawDataImageProcessingForm = {
  onSubmitJob: (settings: ImageProcessingSettings) => void;
  toggleModal: () => void;
};

export default function RawDataImageProcessingForm({
  onSubmitJob,
  toggleModal,
}: RawDataImageProcessingForm) {
  const methods = useForm<ImageProcessingSettings>({
    defaultValues,
    resolver: yupResolver(schema),
  });
  const {
    handleSubmit,
    formState: { errors },
  } = methods;
  const onSubmit: SubmitHandler<ImageProcessingSettings> = (data) => {
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
              <span className="text-sm font-medium">Camera Sensors</span>
              <div>
                <RadioInput
                  fieldName="camera"
                  inputId="cameraSingle"
                  label="Single-sensor"
                  value="single"
                />
              </div>
              <div>
                <RadioInput
                  disabled
                  fieldName="camera"
                  inputId="cameraMulti"
                  label="Multi-sensor"
                  value="multi"
                />
              </div>
            </fieldset>
            {/* Align Photos */}
            <fieldset className="border border-solid border-slate-300 p-3">
              <legend className="block text-gray-600 font-bold pt-2 pb-1">
                Align Photos
              </legend>
              {/* Accuracy */}
              <div>
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
              </div>
              {/* Key point and tie point limits */}
              <div className="flex flex-col gap-4 justify-start">
                <NumberInput
                  fieldName="keyPoint"
                  inputId="keyPointLimit"
                  label="Key point limit"
                  step={1000}
                />
                <NumberInput
                  fieldName="tiePoint"
                  inputId="tiePointLimit"
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
              <div>
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
              </div>
            </fieldset>
          </div>
          <div className="mt-4">
            <CheckboxInput
              fieldName="disclaimer"
              inputId="disclaimer"
              label="Check to proceed"
            />
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
