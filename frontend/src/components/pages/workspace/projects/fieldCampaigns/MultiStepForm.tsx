import clsx from 'clsx';
import { Form, Formik } from 'formik';
import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import * as Yup from 'yup';

import Alert from '../../../../Alert';
import { Button } from '../../../../Buttons';

type MultiStep = {
  children: React.ReactNode;
  validationSchema: Yup.ObjectSchema<any>;
};

export default function MultiStepForm({
  children,
  initialValues,
  onSubmit,
  status,
  setStatus,
}) {
  const { projectId } = useParams();

  const [stepNumber, setStepNumber] = useState(0);
  const steps: React.ReactNode[] = React.Children.toArray(children);
  const [snapshot, setSnapshot] = useState(initialValues);

  const step = steps[stepNumber];
  const totalSteps = steps.length;
  const isLastStep = stepNumber === totalSteps - 1;

  useEffect(() => {
    if (status) {
      setStatus(null);
    }
  }, [stepNumber]);

  const next = (values) => {
    setSnapshot(values);
    setStepNumber(Math.min(stepNumber + 1, totalSteps - 1));
  };

  const previous = (values) => {
    setSnapshot(values);
    setStepNumber(Math.max(stepNumber - 1, 0));
  };

  const handleSubmit = async (values, bag, quit = false) => {
    if (isLastStep) {
      if (quit) {
        return onSubmit({ submitAndQuit: true })(values, bag);
      } else {
        return onSubmit({ submitAndQuit: false })(values, bag);
      }
    } else {
      bag.setTouched({});
      next(values);
    }
  };

  return (
    <Formik
      initialValues={snapshot}
      onSubmit={handleSubmit}
      validationSchema={
        React.isValidElement<MultiStep>(step) && step.props.validationSchema
      }
    >
      {(formik) => (
        <Form className="relative h-full">
          <div className="flex-1 flex flex-wrap gap-4 pb-28 overflow-y-auto">
            {step}
            {status && status.type && status.msg ? (
              <div className="w-full pb-8">
                <Alert alertType={status.type}>{status.msg}</Alert>
              </div>
            ) : null}
          </div>
          <div className="w-full bg-slate-200 fixed bottom-0 px-6">
            <div className="flex flex-col">
              <div className="flex flex-row self-center justify-end gap-4">
                <Link to={`/projects/${projectId}`} state={{ selectedIndex: 1 }}>
                  <Button type="button" size="sm">
                    Cancel
                  </Button>
                </Link>
                {stepNumber > 0 && (
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => previous(formik.values)}
                  >
                    Previous
                  </Button>
                )}
                <div>
                  <Button type="submit" size="sm" disabled={formik.isSubmitting}>
                    {isLastStep ? 'Save' : 'Next'}
                  </Button>
                </div>
                {stepNumber === 2 && (
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => handleSubmit(formik.values, formik, true)}
                  >
                    Save & Exit
                  </Button>
                )}
              </div>
              <div className="flex w-full self-end justify-center">
                <div className="w-4/5 my-4">
                  <div>
                    <h2 className="sr-only">Steps</h2>
                    <div
                      className={clsx(
                        'relative after:absolute after:inset-x-0 after:top-1/2 after:block after:h-1 after:-translate-y-1/2 after:rounded-lg after:bg-slate-300'
                      )}
                    >
                      <ol className="relative z-10 flex justify-between text-sm font-medium text-gray-500">
                        <li className="flex items-center gap-2 p-2 bg-slate-200">
                          <span
                            className={clsx(
                              'size-6 rounded-full text-center text-[10px]/6 font-bold',
                              {
                                'bg-accent2 text-white': stepNumber === 0,
                                'bg-gray-100': stepNumber !== 0,
                              }
                            )}
                          >
                            1
                          </span>
                          <span
                            className={clsx('hidden sm:block', {
                              'text-accent2': stepNumber === 0,
                            })}
                          >
                            {' '}
                            Experiment Information{' '}
                          </span>
                        </li>

                        <li className="flex items-center gap-2 p-2 bg-slate-200">
                          <span
                            className={clsx(
                              'size-6 rounded-full text-center text-[10px]/6 font-bold',
                              {
                                'bg-accent2 text-white': stepNumber === 1,
                                'bg-gray-100': stepNumber !== 1,
                              }
                            )}
                          >
                            2
                          </span>
                          <span
                            className={clsx('hidden sm:block', {
                              'text-accent2': stepNumber === 1,
                            })}
                          >
                            {' '}
                            Treatments{' '}
                          </span>
                        </li>

                        <li className="flex items-center gap-2 p-2 bg-slate-200">
                          <span
                            className={clsx(
                              'size-6 rounded-full text-center text-[10px]/6 font-bold',
                              {
                                'bg-accent2 text-white': stepNumber === 2,
                                'bg-gray-100': stepNumber !== 2,
                              }
                            )}
                          >
                            3
                          </span>
                          <span
                            className={clsx('hidden sm:block', {
                              'text-accent2': stepNumber === 2,
                            })}
                          >
                            {' '}
                            Measurements{' '}
                          </span>
                        </li>
                      </ol>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Form>
      )}
    </Formik>
  );
}

export const MultiStep = ({ children }: MultiStep) => children;
