import { Field, FieldArray, FormikErrors, useFormikContext } from 'formik';
import Papa from 'papaparse';
import { Fragment } from 'react';

import Alert from '../../../Alert';
import ConfirmationModal from '../../../ConfirmationModal';
import { TextField } from '../../../InputFields';
import { FieldCampaignInitialValues } from './FieldCampaign';
import { UpdateCSVErrors } from './FieldCampaign';
import UppyTemplateUpload from './UppyTemplateUpload';

export default function FieldCampaignFormStep2({
  csvErrors,
  updateCsvErrors,
}: {
  csvErrors: Papa.ParseError[][] | Omit<Papa.ParseError, 'code'>[][];
  updateCsvErrors: UpdateCSVErrors;
}) {
  const {
    errors,
    values,
  }: {
    errors: FormikErrors<FieldCampaignInitialValues>;
    values: FieldCampaignInitialValues;
  } = useFormikContext();

  return (
    <div className="flex flex-col gap-2">
      <h1>Treatment</h1>
      <p>
        The template can be created to suit your individual needs. For example, for ease
        of data collection in the field, it may make sense to create separate templates
        according to the first level (factor) of your field's spatial layout (e.g.,
        Well-watered, Water-deficit).
      </p>

      <div>
        <FieldArray
          name="treatments"
          render={(arrayHelpers) => (
            <div className="flex flex-col gap-4">
              <div className="flex flex-row gap-4 max-h-[424px] overflow-x-auto p-4">
                {values['treatments'] && values['treatments'].length > 0
                  ? values['treatments'].map((treatment, index) => (
                      <div
                        className="relative flex flex-col gap-2 h-96 w-80 rounded-lg border-2 border-slate-600 p-4 overflow-y-auto"
                        key={index}
                      >
                        <TextField
                          name={`treatments.${index}.name`}
                          label="Treatment name"
                        />
                        {!treatment.columns || treatment.columns.length === 0 ? (
                          <UppyTemplateUpload
                            id={index.toString()}
                            updateCsvErrors={updateCsvErrors}
                          />
                        ) : null}
                        {csvErrors[index].length === 0 ? (
                          <Fragment>
                            {treatment.filenames && treatment.filenames.length > 0 ? (
                              <div>
                                <span className="font-semibold text-sm text-slate-700">
                                  Upload file(s):
                                </span>
                                <ul>
                                  {treatment.filenames.map((fn) => (
                                    <li key={fn}>{fn}</li>
                                  ))}
                                </ul>
                              </div>
                            ) : null}
                            {treatment.columns && treatment.columns.length > 0 ? (
                              <fieldset>
                                <legend>Select columns to keep:</legend>

                                <div className="space-y-2"></div>
                                {treatment.columns.map((col, colIndex) => (
                                  <label
                                    key={`${col.name}-${colIndex}`}
                                    htmlFor={col.name}
                                    className="flex cursor-pointer items-start gap-4"
                                  >
                                    <div className="flex items-center">
                                      <Field
                                        type="checkbox"
                                        className="size-4 rounded border-gray-300"
                                        name={`treatments.${index}.columns.${colIndex}.selected`}
                                      />
                                    </div>
                                    <div>
                                      <strong className="font-medium text-gray-900">
                                        {col.name}
                                      </strong>
                                    </div>
                                  </label>
                                ))}
                              </fieldset>
                            ) : null}
                          </Fragment>
                        ) : null}
                        <div className="mt-4 flex items-end justify-center w-full h-full">
                          <ConfirmationModal
                            btnName="Remove Treatment"
                            title="Are you sure you want to remove this treatment?"
                            content="You will not be able to recover this treatment after removing it and saving the template."
                            confirmText="Remove treatment"
                            rejectText="Keep treatment"
                            onConfirm={() => {
                              arrayHelpers.remove(index);
                              updateCsvErrors([], index.toString(), 'remove');
                            }}
                          />
                        </div>

                        {csvErrors.length > index && csvErrors[index].length > 0
                          ? csvErrors[index].map((error, errorIndex) => (
                              <span key={errorIndex} className="text-red-500">
                                {error.type}: {error.message}
                              </span>
                            ))
                          : null}
                      </div>
                    ))
                  : null}
                <div
                  className="flex flex-row items-center justify-center gap-2 h-96 w-80 cursor-pointer rounded-lg border-2 border-dashed border-slate-400 p-4 overflow-y-auto"
                  onClick={() => {
                    updateCsvErrors([], csvErrors.length.toString(), 'add');
                    arrayHelpers.push({ name: '', columns: [] });
                  }}
                >
                  <span className="text-lg text-slate-700 font-semibold">
                    Add Treatment
                  </span>
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
                </div>
              </div>
            </div>
          )}
        ></FieldArray>
      </div>
      {errors.treatments && typeof errors.treatments === 'string' ? (
        <div>
          <Alert alertType="warning">{errors.treatments}</Alert>
        </div>
      ) : null}
    </div>
  );
}
