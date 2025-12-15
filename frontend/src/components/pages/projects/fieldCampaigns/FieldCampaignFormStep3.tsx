import {
  ErrorMessage,
  FieldArray,
  FormikErrors,
  useFormikContext,
} from 'formik';
import { Fragment, ReactElement, useEffect, useState } from 'react';
import { PencilIcon } from '@heroicons/react/24/outline';

import { NumberField, TextField } from '../../../InputFields';
import { FieldCampaignInitialValues } from './FieldCampaign';
import { Button } from '../../../Buttons';
import ConfirmationModal from '../../../ConfirmationModal';

function SampleNameFields({
  name,
  numOfSamples,
}: {
  name: string;
  numOfSamples: number;
}) {
  const arr: ReactElement[] = [];
  for (let i = 0; i < numOfSamples; i++) {
    arr.push(
      <div key={`${name}.${i}`} className="shrink-0 w-14 p-1">
        <TextField name={`${name}.${i}`} showError={false} />
      </div>
    );
  }
  return arr;
}

function TimepointForm({ mIndex, tIndex, values }) {
  const { handleChange, setFieldValue } = useFormikContext();

  return (
    <div key={`measurements.${mIndex}.timepoints.${tIndex}`}>
      <div className="flex flex-row gap-4">
        <TextField
          name={`measurements.${mIndex}.timepoints.${tIndex}.timepointIdentifier`}
          label="Timepoint identifier"
        />
        <div className="w-28">
          <NumberField
            name={`measurements.${mIndex}.timepoints.${tIndex}.numberOfSamples`}
            label="No. of samples"
            min={1}
            max={10}
            step={1}
            onChange={(e) => {
              const numOfSamples = parseInt(e.target.value);
              if (numOfSamples > 0) {
                if (
                  values.measurements[mIndex].timepoints[tIndex].sampleNames
                    .length === 0
                ) {
                  const presetSampleNames: string[] = [];
                  const firstSampleName = 'A'.charCodeAt(0);

                  for (let i = 0; i < numOfSamples; i++) {
                    presetSampleNames.push(
                      String.fromCharCode(firstSampleName + i)
                    );
                  }
                  setFieldValue(
                    `measurements.${mIndex}.timepoints.${tIndex}.sampleNames`,
                    presetSampleNames
                  );
                } else {
                  const prev =
                    values.measurements[mIndex].timepoints[tIndex].sampleNames;
                  if (prev.length < numOfSamples) {
                    const neededSampleNames = new Array(
                      numOfSamples - prev.length
                    ).fill('');
                    setFieldValue(
                      `measurements.${mIndex}.timepoints.${tIndex}.sampleNames`,
                      [...prev, ...neededSampleNames]
                    );
                  } else {
                    const neededSampleNames = prev.slice(0, numOfSamples);
                    setFieldValue(
                      `measurements.${mIndex}.timepoints.${tIndex}.sampleNames`,
                      neededSampleNames
                    );
                  }
                }
              }

              handleChange(e);
            }}
          />
        </div>
      </div>
      <div className="block text-sm text-gray-400 font-bold pt-2 pb-1">
        Sample Names*
      </div>
      <div className="flex flex-row gap-2 pb-4 overflow-x-auto">
        <SampleNameFields
          name={`measurements.${mIndex}.timepoints.${tIndex}.sampleNames`}
          numOfSamples={
            values.measurements[mIndex].timepoints[tIndex].numberOfSamples
          }
        />
      </div>
      <ErrorMessage
        className="text-red-500 text-sm"
        name={`measurements.${mIndex}.timepoints.${tIndex}.sampleNames`}
        component="span"
      />
    </div>
  );
}

export default function FieldCampaignFormStep3() {
  const [measurementSteps, setMeasurementSteps] = useState<number[]>([]);
  const [timepoints, setTimepoints] = useState<number[]>([]);

  const {
    errors,
    values,
  }: {
    errors: FormikErrors<FieldCampaignInitialValues>;
    values: FieldCampaignInitialValues;
  } = useFormikContext();
  const { setFieldValue } = useFormikContext();

  useEffect(() => {
    if (values.measurements.length > 0 && measurementSteps.length === 0) {
      setMeasurementSteps(new Array(values.measurements.length).fill(2));
      const initialTimepoints: number[] = [];
      values.measurements.forEach(() => {
        initialTimepoints.push(0);
      });
      setTimepoints(initialTimepoints);
    }
  }, [values.measurements, measurementSteps.length]);

  function forwardMeasurementStep(index: number) {
    const currentSteps = [...measurementSteps];
    currentSteps[index] += 1;

    if (
      values.measurements[index].timepoints.length === 0 &&
      currentSteps[index] === 1
    ) {
      setFieldValue(`measurements.${index}.timepoints.0`, {
        numberOfSamples: 0,
        sampleNames: [],
        timepointIdentifier: '',
      });
    }
    setMeasurementSteps(currentSteps);
  }

  function backwardMeasurementStep(index: number) {
    const currentSteps = [...measurementSteps];
    currentSteps[index] -= 1;
    setMeasurementSteps(currentSteps);
  }

  return (
    <div className="flex flex-col gap-2 overflow-x-auto">
      <h1>Measurements</h1>
      <p>
        When sampling occurs, usually one person writes down one measurement
        (trial in the case of point measurements) using a mobile personal device
        (cellphone, table, or computer) or paper. For that reason, one template
        is created for one measurement. However, it is sometimes easier to enter
        two traits simultaneously, for instance, canopy height and width. We
        used the same template in the lab to collect related traits, such as
        yield components such as biomass (g/m2), thousand-grain weight (g), etc.
      </p>
      <FieldArray
        name="measurements"
        render={(arrayHelpers) => (
          <div className="flex flex-row gap-4 p-4">
            {values.measurements && values.measurements.length > 0
              ? values.measurements.map((_measurement, mIndex) => (
                  <div
                    key={mIndex}
                    className="relative shrink-0 h-72 w-96 flex flex-col gap-4 p-4 rounded-lg border-2 border-dashed border-slate-400"
                  >
                    {/* step 1 - enter measurement name and units */}
                    {measurementSteps[mIndex] === 0 ? (
                      <Fragment>
                        <TextField
                          name={`measurements.${mIndex}.name`}
                          label="Measurement name"
                        />
                        <TextField
                          name={`measurements.${mIndex}.units`}
                          label="Measurement units"
                          required={false}
                        />
                      </Fragment>
                    ) : null}
                    {/* step 2 - add timepoints */}
                    {measurementSteps[mIndex] === 1 ? (
                      <TimepointForm
                        mIndex={mIndex}
                        tIndex={timepoints[mIndex]}
                        values={values}
                      />
                    ) : null}
                    {/* step 3 - review entered information w/ edit option */}
                    {measurementSteps[mIndex] === 2 ? (
                      <div className="flex flex-col gap-4">
                        <div className="flex flex-row items-center gap-2">
                          <span className="text-2xl font-bold">
                            {values.measurements[mIndex].name}
                            {values.measurements[mIndex].units
                              ? ` (${values.measurements[mIndex].units})`
                              : ''}
                          </span>
                          <button
                            className="cursor-pointer"
                            type="button"
                            onClick={() => {
                              // change active measurement step to timepoint form step
                              const currentMeasurementSteps =
                                measurementSteps.slice();
                              currentMeasurementSteps[mIndex] = 0;
                              setMeasurementSteps(currentMeasurementSteps);
                            }}
                          >
                            <span className="sr-only">Edit</span>
                            <PencilIcon className="w-4 h-4" />
                          </button>
                        </div>
                        {values.measurements[mIndex].timepoints.length > 0 ? (
                          <div>
                            <span className="block text-sm font-semibold pt-2 pb-1">
                              Timepoints
                            </span>
                            <div className="flex flex-col gap-2 max-h-28 overflow-y-auto">
                              {values.measurements[mIndex].timepoints.map(
                                (timepoint, tIndex) => (
                                  <div
                                    key={tIndex}
                                    className="flex flex-row items-center gap-2"
                                  >
                                    <span className="text-lg w-28">
                                      {timepoint.timepointIdentifier}
                                    </span>
                                    <button
                                      className="cursor-button"
                                      type="button"
                                      onClick={() => {
                                        // set active timepoint for measurement to this timepoint
                                        const currentTimepoints = [
                                          ...timepoints,
                                        ];
                                        currentTimepoints[mIndex] = tIndex;
                                        setTimepoints(currentTimepoints);
                                        // change active measurement step to timepoint form step
                                        const currentMeasurementSteps = [
                                          ...measurementSteps,
                                        ];
                                        currentMeasurementSteps[mIndex] = 1;
                                        setMeasurementSteps(
                                          currentMeasurementSteps
                                        );
                                      }}
                                    >
                                      <span className="sr-only">Edit</span>
                                      <PencilIcon className="w-4 h-4" />
                                    </button>
                                    <ConfirmationModal
                                      btnName="Remove Timepoint"
                                      btnType="trashIcon"
                                      title="Are you sure you want to remove this timepoint?"
                                      content="You will not be able to recover this timepoint after removing it and saving the template."
                                      confirmText="Remove timepoint"
                                      rejectText="Keep timepoint"
                                      onConfirm={() => {
                                        const currentTimepoints = [
                                          ...values.measurements[mIndex]
                                            .timepoints,
                                        ];
                                        currentTimepoints.splice(tIndex, 1);
                                        setFieldValue(
                                          `measurements.${mIndex}.timepoints`,
                                          currentTimepoints
                                        );
                                      }}
                                    />
                                  </div>
                                )
                              )}
                            </div>
                          </div>
                        ) : null}
                        <div className="w-36 absolute bottom-4 right-4">
                          <Button
                            type="button"
                            size="sm"
                            onClick={() => {
                              // create new timepoint element for current measurement
                              setFieldValue(
                                `measurements.${mIndex}.timepoints.${values.measurements[mIndex].timepoints.length}`,
                                {
                                  numberOfSamples:
                                    values.measurements[mIndex].timepoints[0]
                                      .numberOfSamples,
                                  sampleNames:
                                    values.measurements[mIndex].timepoints[0]
                                      .sampleNames,
                                  timepointIdentifier: '',
                                }
                              );
                              // set active timepoint for measurement to new timepoint
                              const currentTimepoints = [...timepoints];
                              currentTimepoints[mIndex] += 1;
                              setTimepoints(currentTimepoints);
                              // change active measurement step to timepoint form step
                              const currentMeasurementSteps = [
                                ...measurementSteps,
                              ];
                              currentMeasurementSteps[mIndex] = 1;
                              setMeasurementSteps(currentMeasurementSteps);
                            }}
                          >
                            Add Timepoint
                          </Button>
                        </div>
                      </div>
                    ) : null}
                    {measurementSteps[mIndex] < 2 ? (
                      <Fragment>
                        <div className="w-36 absolute bottom-4 right-4">
                          <Button
                            type="button"
                            size="sm"
                            disabled={
                              errors &&
                              errors.measurements &&
                              errors.measurements[mIndex]
                                ? true
                                : false
                            }
                            onClick={() => forwardMeasurementStep(mIndex)}
                          >
                            {measurementSteps[mIndex] < 1 ? 'Next' : 'Done'}
                          </Button>
                        </div>
                        {measurementSteps[mIndex] > 0 ? (
                          <div className="w-36 absolute bottom-4 left-4">
                            <Button
                              type="button"
                              size="sm"
                              onClick={() => backwardMeasurementStep(mIndex)}
                            >
                              Back
                            </Button>
                          </div>
                        ) : null}
                      </Fragment>
                    ) : null}
                    {measurementSteps[mIndex] === 2 && (
                      <div className="mt-4 flex items-end justify-start w-full h-full">
                        <ConfirmationModal
                          btnName="Remove Measurement"
                          title="Are you sure you want to remove this measurement?"
                          content="You will not be able to recover this measurement after removing it and saving the template."
                          confirmText="Remove measurement"
                          rejectText="Keep measurement"
                          onConfirm={() => {
                            const currentMeasurementSteps = [
                              ...measurementSteps,
                            ];
                            currentMeasurementSteps.splice(mIndex, 1);
                            setMeasurementSteps(currentMeasurementSteps);
                            arrayHelpers.remove(mIndex);
                          }}
                        />
                      </div>
                    )}
                  </div>
                ))
              : null}
            <button
              type="button"
              className="h-72 w-96 shrink-0 flex flex-row items-center justify-center gap-2 cursor-pointer rounded-lg border-2 border-dashed border-slate-400 p-4 overflow-y-auto hover:border-slate-600 text-lg text-slate-700 font-semibold disabled:text-slate-300"
              onClick={() => {
                // add new measurement with default values
                arrayHelpers.push({
                  name: '',
                  units: '',
                  timepoints: [],
                });
                // set step 0 as initial step for measurement form
                setMeasurementSteps([...measurementSteps, 0]);
                // set active timepoint for new measurement to 0
                setTimepoints([...timepoints, 0]);
              }}
            >
              <span className="">Add Measurement</span>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
                className="w-6 h-6"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 4.5v15m7.5-7.5h-15"
                />
              </svg>
            </button>
          </div>
        )}
      />
    </div>
  );
}
