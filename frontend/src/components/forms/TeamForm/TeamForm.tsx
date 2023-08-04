import axios from 'axios';
import { Formik, Form } from 'formik';
import { useNavigate } from 'react-router-dom';

import Alert from '../../Alert';
import { CustomSubmitButton } from '../CustomButtons';
import CustomTextField from '../CustomTextField';

import initialValues from './initialValues';
import validationSchema from './validationSchema';

export default function TeamForm() {
  const navigate = useNavigate();

  return (
    <div style={{ width: 450 }}>
      <Formik
        initialValues={initialValues}
        validationSchema={validationSchema}
        onSubmit={async (values, { resetForm, setSubmitting, setStatus }) => {
          setStatus(null);
          try {
            const data = {
              title: values.title,
              description: values.description,
            };
            const response = await axios.post('/api/v1/teams/', data);
            if (response) {
              navigate('/teams');
              resetForm();
            } else {
              setStatus({ type: 'error', msg: 'Unable to create team' });
            }
          } catch (err) {
            if (axios.isAxiosError(err)) {
              setStatus({ type: 'error', msg: err.response?.data.detail });
            } else {
              setStatus({ type: 'error', msg: 'Unexpected error has occurred' });
            }
          }
          setSubmitting(false);
        }}
      >
        {({ isSubmitting }) => (
          <div>
            <span className="text-xl font-semibold">Create team</span>
            <Form>
              <CustomTextField label="Title" name="title" />
              <CustomTextField label="Description" name="description" />
              <div className="mt-4">
                <CustomSubmitButton disabled={isSubmitting}>
                  Create team
                </CustomSubmitButton>
              </div>
            </Form>
          </div>
        )}
      </Formik>
    </div>
  );
}
