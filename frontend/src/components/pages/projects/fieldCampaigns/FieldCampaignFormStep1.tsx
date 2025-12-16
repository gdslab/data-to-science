import { FieldArray, useFormikContext } from 'formik';

import { TextField } from '../../../InputFields';
import { FieldCampaignInitialValues } from './FieldCampaign';

export default function FieldCampaignFormStep1() {
  const { values }: { values: FieldCampaignInitialValues } = useFormikContext();

  return (
    <div className="flex flex-col gap-2">
      <h1>Experiment information</h1>
      <p>
        Here is where you can enter information to identify your experiment. You
        can add more information if necessary.
      </p>

      <FieldArray
        name="newColumns"
        render={(arrayHelpers) => (
          <div>
            <div className="grid md:grid-cols-2 grid-cols-1 max-h-96 overflow-y-auto gap-2">
              {values['newColumns'] && values['newColumns'].length > 0
                ? values['newColumns'].map(
                    (
                      newColumn: {
                        name: string;
                        fill: string;
                        placeholder?: string;
                      },
                      index: number
                    ) => (
                      <div key={index}>
                        <div className="flex items-center gap-4 px-4 bg-white/60 rounded-md shadow-xs">
                          <div className="flex items-center gap-4 w-11/12">
                            <div className="min-h-24 w-1/2">
                              <TextField
                                name={`newColumns.${index}.name`}
                                label="Column name"
                                disabled={newColumn.name === 'Experiment'}
                              />
                            </div>
                            <div className="min-h-24 w-1/2">
                              <TextField
                                name={`newColumns.${index}.fill`}
                                label="Fill value"
                                placeholder={newColumn.placeholder}
                              />
                            </div>
                          </div>
                          <div className="flex items-center justify-center min-h-24 w-1/12">
                            {newColumn.name !== 'Experiment' ? (
                              <button
                                type="button"
                                onClick={() => arrayHelpers.remove(index)}
                              >
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
                                    d="M15 12H9m12 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
                                  />
                                </svg>
                              </button>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    )
                  )
                : null}
              <div
                className="flex flex-row items-center justify-center gap-2 h-24 h-24 min-w-80 cursor-pointer rounded-lg border-2 border-dashed border-slate-400 p-4 overflow-y-auto"
                onClick={() => arrayHelpers.push({ name: '', fill: '' })}
              >
                <span className="text-lg text-slate-700 font-semibold">
                  Add Experiment Information
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
  );
}
