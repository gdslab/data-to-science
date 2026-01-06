import { useForm, FormProvider, SubmitHandler } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import { useState } from 'react';

import Checkbox from '../../../../../../../Checkbox';
import {
  CheckboxInput,
  NumberInput,
  RadioInput,
} from '../../../../../../../RHFInputs';

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
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);

  const methods = useForm<MetashapeSettings>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });
  const {
    handleSubmit,
    formState: { errors },
    watch,
  } = methods;

  const watchDisclaimer = watch('disclaimer');
  const watchExportDEM = watch('exportDEM');
  const watchExportOrtho = watch('exportOrtho');
  const onSubmit: SubmitHandler<MetashapeSettings> = (data) => {
    onSubmitJob(data);
    toggleModal();
  };

  return (
    <div className="bg-white/80 rounded-md p-4 min-w-fit">
      <legend className="block text-lg text-gray-600 font-bold pt-2 pb-1">
        Image Processing Settings
      </legend>
      <FormProvider {...methods}>
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="flex gap-8">
            {/* Camera and Align Photos Column */}
            <div className="space-y-4">
              {/* Camera Options */}
              <fieldset className="border border-solid border-slate-300 p-3 min-w-max">
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
            </div>
            {/* Point Cloud Column */}
            <div className="space-y-4">
              {/* Build Point Cloud */}
              <fieldset className="border border-solid border-slate-300 p-3 min-w-60">
                <legend className="block text-gray-600 font-bold pt-2 pb-1">
                  Build Point Cloud
                </legend>
                {/* Quality */}
                <div className="flex flex-col gap-1.5">
                  <span className="text-sm font-medium">Quality</span>
                  <div className="flex gap-4">
                    <RadioInput
                      fieldName="buildDepthQuality"
                      inputId="buildDepthQualityLow"
                      label="Low"
                      value="low"
                    />
                    <RadioInput
                      fieldName="buildDepthQuality"
                      inputId="buildDepthQualityMedium"
                      label="Medium"
                      value="medium"
                    />
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

              {/* Advanced Settings - Conditionally Rendered */}
              {showAdvancedSettings && (
                <>
                  {/* Build Orthomosaic */}
                  <fieldset className="border border-solid border-slate-300 p-3">
                    <legend className="block text-gray-600 font-bold pt-2 pb-1">
                      Build Orthomosaic
                    </legend>
                    {/* Blending Mode */}
                    <div className="flex flex-col gap-1.5">
                      <span className="text-sm font-medium">Blending Mode</span>
                      <div className="flex gap-4 flex-wrap">
                        <RadioInput
                          fieldName="blendingMode"
                          inputId="blendingModeAverage"
                          label="Average"
                          value="average"
                        />
                        <RadioInput
                          fieldName="blendingMode"
                          inputId="blendingModeDisabled"
                          label="Disabled"
                          value="disabled"
                        />
                        <RadioInput
                          fieldName="blendingMode"
                          inputId="blendingModeMin"
                          label="Min"
                          value="min"
                        />
                        <RadioInput
                          fieldName="blendingMode"
                          inputId="blendingModeMax"
                          label="Max"
                          value="max"
                        />
                        <RadioInput
                          fieldName="blendingMode"
                          inputId="blendingModeMosaic"
                          label="Mosaic"
                          value="mosaic"
                        />
                      </div>
                      {errors &&
                        errors.blendingMode &&
                        typeof errors.blendingMode.message === 'string' && (
                          <p className="text-sm text-red-500">
                            {errors.blendingMode.message}
                          </p>
                        )}
                    </div>

                    {/* Additional Processing Options */}
                    <div className="mt-4 space-y-3">
                      <span className="text-sm font-medium text-gray-700 block mb-3">
                        Other Options
                      </span>
                      <div>
                        <CheckboxInput
                          fieldName="fillHoles"
                          label="Fill Holes"
                        />
                      </div>
                      <div>
                        <CheckboxInput
                          fieldName="ghostingFilter"
                          label="Ghosting Filter"
                        />
                      </div>
                      <div>
                        <CheckboxInput
                          fieldName="cullFaces"
                          label="Cull Faces"
                        />
                      </div>
                      <div>
                        <CheckboxInput
                          fieldName="refineSeamlines"
                          label="Refine Seamlines"
                        />
                      </div>
                      <div>
                        <NumberInput
                          fieldName="resolution"
                          label="Resolution (meters) (0 for automatic)"
                          step={0.001}
                        />
                      </div>
                    </div>
                  </fieldset>
                </>
              )}
            </div>

            {/* Export Options Column - Conditionally Rendered */}
            {showAdvancedSettings && (
              <div className="space-y-4">
                <fieldset className="border border-solid border-slate-300 p-3 min-w-60">
                  <legend className="block text-gray-600 font-bold pt-2 pb-1">
                    Export Options
                  </legend>
                  <div className="space-y-3">
                    <div>
                      <CheckboxInput
                        fieldName="exportPointCloud"
                        label="Point cloud"
                      />
                    </div>
                    <div>
                      <CheckboxInput
                        fieldName="exportDEM"
                        label="Digital Elevation Model (DEM)"
                      />
                      {watchExportDEM && (
                        <div className="mt-2 ml-6">
                          <NumberInput
                            fieldName="exportDEMResolution"
                            label="DEM Resolution (meters) (0 for automatic)"
                            step={0.001}
                          />
                        </div>
                      )}
                    </div>
                    <div>
                      <CheckboxInput
                        fieldName="exportOrtho"
                        label="Orthomosaic"
                      />
                      {watchExportOrtho && (
                        <div className="mt-2 ml-6">
                          <NumberInput
                            fieldName="exportOrthoResolution"
                            label="Orthomosaic Resolution (meters) (0 for automatic)"
                            step={0.001}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                </fieldset>
              </div>
            )}
          </div>

          {/* Advanced Settings Toggle and Actions Row */}
          <div className="mt-4 flex justify-between items-center">
            {/* Advanced Settings Toggle */}
            <div className="flex items-center gap-2">
              <Checkbox
                id="advancedSettings-checkbox"
                checked={showAdvancedSettings}
                onChange={(e) => setShowAdvancedSettings(e.target.checked)}
              />
              <label
                htmlFor="advancedSettings-checkbox"
                className="text-sm font-medium text-gray-700"
              >
                Advanced Settings
              </label>
            </div>

            {/* Disclaimer and Submit Button */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Checkbox
                  id="disclaimer-checkbox"
                  {...methods.register('disclaimer')}
                  checked={watchDisclaimer}
                  onChange={methods.register('disclaimer').onChange}
                />
                <label
                  htmlFor="disclaimer-checkbox"
                  className="text-sm font-medium text-gray-700"
                >
                  Check to proceed
                </label>
              </div>
              <button
                className="w-32 bg-accent2/90 text-white font-semibold py-1 rounded-sm enabled:hover:bg-accent2 disabled:opacity-75 disabled:cursor-not-allowed"
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
