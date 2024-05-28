import axios, { AxiosResponse, isAxiosError } from 'axios';
import { Formik, Form } from 'formik';
import { useNavigate } from 'react-router-dom';
import * as Yup from 'yup';

import Alert from '../../../Alert';
import { Button } from '../../../Buttons';
import { TextField, SelectField } from '../../../InputFields';
import { useProjectContext } from '../ProjectContext';

import { FieldCampaignResponse } from './FieldCampaign';

const initialValues: { title: string; leadId: string } = {
  title: '',
  leadId: '',
};

const validationSchema = Yup.object({
  title: Yup.string().required('Must enter campaign name'),
  leadId: Yup.string().required('Must choose a lead'),
});

export default function FieldCampaignCreate() {
  const { project, projectMembers } = useProjectContext();
  const navigate = useNavigate();

  if (!project) {
    <div className="p-4">Missing project</div>;
  } else {
    return (
      <div className="p-4 w-96">
        <h1>Create Campaign</h1>
        <Formik
          initialValues={initialValues}
          validationSchema={validationSchema}
          onSubmit={async (values, { setStatus, setSubmitting }) => {
            try {
              const data = {
                title: values.title,
                lead_id: values.leadId,
              };
              const response: AxiosResponse<FieldCampaignResponse> = await axios.post(
                `${import.meta.env.VITE_API_V1_STR}/projects/${project.id}/campaigns`,
                data
              );
              if (response) {
                setSubmitting(false);
                navigate(
                  `/projects/${project.id}/campaigns/${response.data.id}/create`
                );
              } else {
                setStatus({ type: 'error', msg: 'Unable to create campaign' });
                setSubmitting(false);
              }
            } catch (err) {
              if (isAxiosError(err) && err.response?.data.detail) {
                setStatus({ type: 'error', msg: err.response.data.detail });
              } else {
                setStatus({ type: 'error', msg: 'Unable to create campaign' });
              }
              setSubmitting(false);
            }
          }}
        >
          {({ isSubmitting, status }) => (
            <Form>
              <div className="flex flex-col gap-4">
                <TextField label="Campaign Title" name="title" />
                {projectMembers ? (
                  <SelectField
                    label="Lead"
                    name="leadId"
                    options={[{ label: 'Select lead', value: '' }].concat(
                      projectMembers.map(({ member_id, full_name }) => ({
                        label: full_name,
                        value: member_id,
                      }))
                    )}
                  />
                ) : (
                  <span>Unable to find project members</span>
                )}
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting ? 'Creating' : 'Create'}
                </Button>
                {status && status.type && status.msg ? (
                  <div className="mt-4">
                    <Alert alertType={status.type}>{status.msg}</Alert>
                  </div>
                ) : null}
              </div>
            </Form>
          )}
        </Formik>
      </div>
    );
  }
}
