import axios from 'axios';
import { Formik, Form } from 'formik';
import { useNavigate } from 'react-router-dom';

import Alert from '../../../Alert';
import { Button, OutlineButton } from '../../../Buttons';
import { SelectField, TextField } from '../../../InputFields';
import { User } from '../../../../AuthContext';

import initialValues, { PLATFORM_OPTIONS, SENSOR_OPTIONS } from './initialValues';
import validationSchema from './validationSchema';

export async function loader() {
  const userProfileLS = localStorage.getItem('userProfile');
  if (userProfileLS) {
    const userProfile: User = JSON.parse(userProfileLS);
    return [
      {
        value: userProfile.id,
        label: `${userProfile.first_name} ${userProfile.last_name}`,
      },
    ];
  } else {
    return [];
  }
}

export default function FlightForm({
  // pilots,
  projectId,
  setOpen,
}: {
  // pilots: Pilot[];
  projectId: string;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const navigate = useNavigate();
  const pilots = [
    { value: 'f921e938-c85a-4bbf-ab3a-ca832f36a4ca', label: 'Ben Hancock' },
  ];
  return (
    <div className="my-8 mx-4">
      <h1>New Flight</h1>
      <Formik
        initialValues={{ ...initialValues, pilotId: pilots[0].value }}
        validationSchema={validationSchema}
        onSubmit={async (values, { setSubmitting, setStatus }) => {
          try {
            const data = {
              acquisition_date: values.acquisitionDate,
              altitude: values.altitude,
              side_overlap: values.sideOverlap,
              forward_overlap: values.forwardOverlap,
              sensor: values.sensor,
              pilot_id: values.pilotId,
              platform: values.platform,
            };
            const response = await axios.post(
              `/api/v1/projects/${projectId}/flights`,
              data
            );
            if (response) {
              setStatus({ type: 'success', msg: 'Created' });
              setOpen(false);
              navigate(`/projects/${projectId}`);
            } else {
              // do something
            }
          } catch (err) {
            if (axios.isAxiosError(err)) {
              // console.error(err);
            } else {
              // do something
            }
            setStatus({ type: 'error', msg: 'Error' });
          }
          setSubmitting(false);
        }}
      >
        {({ isSubmitting, status }) => (
          <Form>
            <TextField type="date" label="Acquisition date" name="acquisitionDate" />
            <TextField label="Altitude (m)" name="altitude" />
            <TextField label="Side overlap (%)" name="sideOverlap" />
            <TextField label="Forward overlap (%)" name="forwardOverlap" />
            <SelectField label="Sensor" name="sensor" options={SENSOR_OPTIONS} />
            <SelectField label="Platform" name="platform" options={PLATFORM_OPTIONS} />
            <SelectField label="Pilot" name="pilotId" options={pilots} />

            <div className="grid grid-rows-2 gap-4 mt-4">
              <Button type="submit" disabled={isSubmitting}>
                Create
              </Button>
              <OutlineButton onClick={() => setOpen(false)}>Cancel</OutlineButton>
            </div>
            {status && status.type && status.msg ? (
              <div className="mt-4">
                <Alert alertType={status.type}>{status.msg}</Alert>
              </div>
            ) : null}
          </Form>
        )}
      </Formik>
    </div>
  );
}
