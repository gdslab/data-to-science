import axios from 'axios';
import { Formik, Form } from 'formik';
import { Link, useLoaderData, useParams } from 'react-router-dom';

import Alert from '../../../Alert';
import { Button, OutlineButton } from '../../../Buttons';
import Card from '../../../Card';
import { SelectField, TextField } from '../../../InputFields';
import { User } from '../../../../AuthContext';

import initialValues, { PLATFORM_OPTIONS, SENSOR_OPTIONS } from './initialValues';

interface Pilot {
  label: string;
  value: string;
}

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

export default function FlightForm() {
  const { projectId } = useParams();
  const pilots = useLoaderData() as Pilot[];

  return (
    <div className="h-full flex flex-wrap items-center justify-center bg-accent1">
      <div className="sm:w-full md:w-1/3 max-w-xl mx-4">
        <Card>
          <Formik
            initialValues={{ ...initialValues, pilotId: pilots[0].value }}
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
              <div className="m-4">
                <h1>Flight</h1>
                <Form>
                  <TextField
                    type="date"
                    label="Acquisition date"
                    name="acquisitionDate"
                  />
                  <TextField label="Altitude (m)" name="altitude" />
                  <TextField label="Side overlap (%)" name="sideOverlap" />
                  <TextField label="Forward overlap (%)" name="forwardOverlap" />
                  <SelectField label="Sensor" name="sensor" options={SENSOR_OPTIONS} />
                  <SelectField
                    label="Platform"
                    name="platform"
                    options={PLATFORM_OPTIONS}
                  />
                  <SelectField label="Pilot" name="pilotId" options={pilots} />
                  <div className="mt-4">
                    <Button type="submit" disabled={isSubmitting}>
                      Create Flight
                    </Button>
                  </div>
                  <div className="mt-4">
                    <Link to={`/projects/${projectId}`}>
                      <OutlineButton>Return</OutlineButton>
                    </Link>
                  </div>
                  {status && status.type && status.msg ? (
                    <div className="mt-4">
                      <Alert alertType={status.type}>{status.msg}</Alert>
                    </div>
                  ) : null}
                </Form>
              </div>
            )}
          </Formik>
        </Card>
      </div>
    </div>
  );
}
