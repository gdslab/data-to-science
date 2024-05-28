import { Link, useParams } from 'react-router-dom';

import { Button } from '../../../Buttons';
import { ActiveStep } from './FieldCampaign';
import { classNames } from '../../../utils';
import { useFormikContext } from 'formik';
import clsx from 'clsx';

export default function FieldCampaignNav({
  activeStep,
  handleSubmit,
  isSubmitting,
  setActiveStep,
}: ActiveStep) {
  const { projectId } = useParams();
  const LAST_STEP_IDX = 2;

  const formik = useFormikContext();

  function forwardStep() {
    if (activeStep + 1 < LAST_STEP_IDX + 1) {
      setActiveStep(activeStep + 1);
    }
  }

  function backStep() {
    if (activeStep - 1 > -1) {
      setActiveStep(activeStep - 1);
    }
  }

  return (
    <div className="relative h-full flex flex-col">
      <div className="absolute bottom-20 flex flex-row self-center justify-end gap-4">
        <Link to={`/projects/${projectId}`} state={{ selectedIndex: 1 }}>
          <Button type="button" size="sm">
            Cancel
          </Button>
        </Link>
        <Button type="button" size="sm" disabled={activeStep === 0} onClick={backStep}>
          Previous
        </Button>
        {activeStep < 2 ? (
          <Button
            type="button"
            size="sm"
            disabled={activeStep === LAST_STEP_IDX}
            onClick={forwardStep}
          >
            Next
          </Button>
        ) : null}
        {activeStep === 2 ? (
          <Button type="submit" size="sm">
            {isSubmitting ? 'Saving...' : 'Save'}
          </Button>
        ) : null}
        {activeStep === 2 ? (
          <Button
            type="button"
            size="sm"
            onClick={() => handleSubmit({ submitAndQuit: true })(formik.values, formik)}
          >
            {isSubmitting ? 'Saving...' : 'Save & Exit'}
          </Button>
        ) : null}
      </div>
      <div className="absolute bottom-0 flex w-full self-end justify-center">
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
                    className={classNames(
                      activeStep === 0 ? 'bg-accent2 text-white' : 'bg-gray-100',
                      'size-6 rounded-full text-center text-[10px]/6 font-bold'
                    )}
                  >
                    1
                  </span>
                  <span
                    className={clsx('hidden sm:block', {
                      'text-accent2': activeStep === 0,
                    })}
                  >
                    {' '}
                    Experiment Information{' '}
                  </span>
                </li>

                <li className="flex items-center gap-2 p-2 bg-slate-200">
                  <span
                    className={classNames(
                      activeStep === 1 ? 'bg-accent2 text-white' : 'bg-gray-100',
                      'size-6 rounded-full text-center text-[10px]/6 font-bold'
                    )}
                  >
                    2
                  </span>
                  <span
                    className={clsx('hidden sm:block', {
                      'text-accent2': activeStep === 1,
                    })}
                  >
                    {' '}
                    Treatments{' '}
                  </span>
                </li>

                <li className="flex items-center gap-2 p-2 bg-slate-200">
                  <span
                    className={classNames(
                      activeStep === 2 ? 'bg-accent2 text-white' : 'bg-gray-100',
                      'size-6 rounded-full text-center text-[10px]/6 font-bold'
                    )}
                  >
                    3
                  </span>
                  <span
                    className={clsx('hidden sm:block', {
                      'text-accent2': activeStep === 2,
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
  );
}
