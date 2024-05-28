import axios from 'axios';
import { Formik, Form } from 'formik';
import { useEffect, useState } from 'react';
import { useLoaderData, useNavigate } from 'react-router-dom';
import * as Yup from 'yup';

import FieldCampaignNav from './FieldCampaignNav';
import FieldCampaignFormStep1 from './FieldCampaignFormStep1';
import FieldCampaignFormStep2 from './FieldCampaignFormStep2';
import FieldCampaignFormStep3 from './FieldCampaignFormStep3';

import { FieldCampaignInitialValues } from './FieldCampaign';
import { Params, useParams } from 'react-router-dom';
import { FieldCampaign } from '../Project';
import Alert, { Status } from '../../../Alert';

const initialValues: FieldCampaignInitialValues = {
  newColumns: [
    { name: 'Experiment', fill: '' },
    { name: 'Year', fill: '', placeholder: 'e.g., 2022' },
    { name: 'Season', fill: '', placeholder: 'e.g., Summer' },
  ],
  measurements: [],
  treatments: [],
};

const validationSchema = Yup.object({
  newColumns: Yup.array().of(
    Yup.object({
      name: Yup.string()
        .min(1, 'Must have at least 1 character')
        .max(64, 'Cannot exceed 64 characters')
        .required('Required'),
      fill: Yup.string()
        .min(1, 'Must have at least 1 character')
        .max(64, 'Cannot exceed 64 characters')
        .required('Required'),
    })
  ),
  treatments: Yup.array()
    .of(
      Yup.object({
        data: Yup.array().of(Yup.object()),
        filenames: Yup.array().of(Yup.string()),
        headers: Yup.array().of(
          Yup.object({ name: Yup.string(), selected: Yup.boolean() })
        ),
        name: Yup.string()
          .min(1, 'Must have at least 1 character')
          .max(64, 'Cannot exceed 64 characters')
          .required('Required'),
      })
    )
    .min(1, 'Must enter at least one treatment')
    .required(),
  measurements: Yup.array().of(
    Yup.object({
      name: Yup.string()
        .min(1, 'Must have at least 1 character')
        .max(64, 'Cannot exceed 64 characters')
        .required('Required'),
      units: Yup.string()
        .min(1, 'Must have at least 1 character')
        .max(64, 'Cannot exceed 64 characters'),
      timepoints: Yup.array().of(
        Yup.object({
          numberOfSamples: Yup.number()
            .min(1, 'Must have at least 1 sample')
            .required('Required'),
          sampleNames: Yup.array()
            .of(
              Yup.string()
                .min(1, 'Must have at least 1 character')
                .max(64, 'Cannot exceed 64 characters')
                .required('Required')
            )
            .test('unique', 'Sample names must be unique', (value) =>
              value ? value.length === new Set(value)?.size : true
            )
            .test(
              'matches-num-of-samps',
              'Number of sample names must match "No. of samples" value',
              (value, context) => {
                const { numberOfSamples } = context.parent;
                return (value && value.length === numberOfSamples) || !numberOfSamples;
              }
            ),
          timepointIdentifier: Yup.string()
            .min(1, 'Must have at least 1 character')
            .max(64, 'Cannot exceed 64 characters')
            .required('Required'),
        })
      ),
    })
  ),
});

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

export default function FieldCampaignForm() {
  const navigate = useNavigate();

  const [activeStep, setActiveStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);

  const { campaignId, projectId } = useParams();

  const { fieldCampaign } = useLoaderData() as { fieldCampaign: FieldCampaign };

  useEffect(() => {
    if (fieldCampaign && fieldCampaign.form_data) {
      setActiveStep(2);
    }
  }, []);

  useEffect(() => {
    setStatus(null);
  }, [activeStep]);

  const handleSubmit = (extra) => async (values, _actions) => {
    setIsSubmitting(true);
    try {
      const response = await axios.put(
        `/api/v1/projects/${projectId}/campaigns/${campaignId}`,
        { form_data: values }
      );
      if (response) {
        setIsSubmitting(false);
        if (extra.submitAndQuit) {
          navigate(`/projects/${projectId}`, { state: { selectedIndex: 1 } });
        } else {
          setStatus({ type: 'success', msg: 'Campaign successfully saved' });
        }
      } else {
        setIsSubmitting(false);
        setStatus({ type: 'error', msg: 'Unable to save campaign' });
      }
    } catch (err) {
      setIsSubmitting(false);
      setStatus({ type: 'error', msg: 'Unable to save campaign' });
    }
  };

  return (
    <div className="mx-4 h-full">
      <div className="flex flex-col h-full gap-4">
        <Formik
          initialValues={
            fieldCampaign && fieldCampaign.form_data
              ? fieldCampaign.form_data
              : initialValues
          }
          validationSchema={validationSchema}
          onSubmit={handleSubmit({ submitAndQuit: false })}
        >
          {() => (
            <Form className="flex flex-col h-full gap-4">
              {activeStep === 0 ? <FieldCampaignFormStep1 /> : null}
              {activeStep === 1 ? <FieldCampaignFormStep2 /> : null}
              {activeStep === 2 ? <FieldCampaignFormStep3 /> : null}
              {status && status.type && status.msg ? (
                <Alert alertType={status.type}>{status.msg}</Alert>
              ) : null}
              <FieldCampaignNav
                activeStep={activeStep}
                handleSubmit={handleSubmit}
                isSubmitting={isSubmitting}
                setActiveStep={setActiveStep}
              />
            </Form>
          )}
        </Formik>
      </div>
    </div>
  );
}
