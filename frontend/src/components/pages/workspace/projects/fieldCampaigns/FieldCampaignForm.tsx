import axios from 'axios';
import Papa from 'papaparse';
import { useEffect, useState } from 'react';
import { Params, useLoaderData, useNavigate, useParams } from 'react-router-dom';

import { Status } from '../../../../Alert';
import { FieldCampaign } from '../Project';
import { FieldCampaignInitialValues } from './FieldCampaign';
import FieldCampaignFormStep1 from './FieldCampaignFormStep1';
import FieldCampaignFormStep2 from './FieldCampaignFormStep2';
import FieldCampaignFormStep3 from './FieldCampaignFormStep3';
import MultiStepForm, { MultiStep } from './MultiStepForm';
import {
  step1ValidationSchema,
  step2ValidationSchema,
  step3ValidationSchema,
} from './validationSchemas';

export async function loader({ params }: { params: Params<string> }) {
  const fieldCampaign = await axios.get(
    `/api/v1/projects/${params.projectId}/campaigns/${params.campaignId}`
  );

  if (fieldCampaign) {
    return { fieldCampaign: fieldCampaign.data };
  } else {
    return null;
  }
}

const initialValues: FieldCampaignInitialValues = {
  newColumns: [
    { name: 'Experiment', fill: '' },
    { name: 'Year', fill: '', placeholder: 'e.g., 2022' },
    { name: 'Season', fill: '', placeholder: 'e.g., Summer' },
  ],
  measurements: [],
  treatments: [],
};

export default function FieldCampaignForm() {
  const [csvErrors, setCsvErrors] = useState<
    Papa.ParseError[][] | Omit<Papa.ParseError, 'code'>[][]
  >([]);
  const [status, setStatus] = useState<Status | null>(null);

  const { fieldCampaign } = useLoaderData() as { fieldCampaign: FieldCampaign };
  const navigate = useNavigate();
  const { campaignId, projectId } = useParams();

  useEffect(() => {
    // reset csv errors if opening existing form to edit
    if (
      fieldCampaign &&
      fieldCampaign.form_data &&
      fieldCampaign.form_data.treatments.length > 0
    ) {
      setCsvErrors(new Array(fieldCampaign.form_data.treatments.length).fill([]));
    }
  }, []);

  /**
   * Update array tracking csv parsing errors.
   * @param errors New errors to add to array.
   * @param index Position where to add new errors.
   */
  function updateCsvErrors(
    errors: Papa.ParseError[] | Omit<Papa.ParseError, 'code'>[],
    index: string,
    op: 'add' | 'remove' | 'clear'
  ) {
    if (op === 'remove') {
      let currentCsvErrors = csvErrors.slice();
      currentCsvErrors.splice(parseInt(index), 1);
      setCsvErrors(currentCsvErrors);
    } else if (op === 'add') {
      let currentCsvErrors = csvErrors.slice();
      currentCsvErrors[parseInt(index)] = errors;
      setCsvErrors(currentCsvErrors);
    } else if (op === 'clear') {
      let currentCsvErrors = csvErrors.slice();
      currentCsvErrors[parseInt(index)] = [];
      setCsvErrors(currentCsvErrors);
    } else {
      throw new Error('Unrecognized operation for updating csv errors');
    }
  }

  const handleSubmit = (extra) => async (values, _actions) => {
    try {
      const response = await axios.put(
        `/api/v1/projects/${projectId}/campaigns/${campaignId}`,
        { form_data: values }
      );
      if (response) {
        if (extra.submitAndQuit) {
          navigate(`/projects/${projectId}`, { state: { selectedIndex: 1 } });
        } else {
          setStatus({ type: 'success', msg: 'Campaign successfully saved' });
        }
      } else {
        setStatus({ type: 'error', msg: 'Unable to save campaign' });
      }
    } catch (err) {
      setStatus({ type: 'error', msg: 'Unable to save campaign' });
    }
  };

  return (
    <div className="mx-4 h-full">
      <div className="flex flex-col h-full gap-4">
        <MultiStepForm
          initialValues={
            fieldCampaign && fieldCampaign.form_data
              ? fieldCampaign.form_data
              : initialValues
          }
          onSubmit={handleSubmit}
          status={status}
          setStatus={setStatus}
        >
          <MultiStep validationSchema={step1ValidationSchema}>
            <FieldCampaignFormStep1 />
          </MultiStep>
          <MultiStep validationSchema={step2ValidationSchema}>
            <FieldCampaignFormStep2
              csvErrors={csvErrors}
              updateCsvErrors={updateCsvErrors}
            />
          </MultiStep>
          <MultiStep validationSchema={step3ValidationSchema}>
            <FieldCampaignFormStep3 />
          </MultiStep>
        </MultiStepForm>
      </div>
    </div>
  );
}
