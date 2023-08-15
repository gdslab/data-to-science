import axios from 'axios';
import { Formik, Form } from 'formik';
import { useLoaderData, useParams } from 'react-router-dom';
import { useState } from 'react';

import Alert from '../../Alert';
import { Button } from '../CustomButtons';
import Card from '../../Card';
import CustomSelectField from '../CustomSelectField';
import CustomTextField from '../CustomTextField';
import UploadModal from '../../UploadModal';

import initialValues, { PLATFORM_OPTIONS, SENSOR_OPTIONS } from './initialValues';

interface Pilot {
  label: string;
  value: string;
}

export async function loader() {
  // const response = await axios.get('/api/v1/teams/');
  // if (response) {
  //   const teams = response.data;
  //   teams.unshift({ title: 'No team', id: '' });
  //   return teams;
  // } else {
  //   return [];
  // }
  let currentProfile = JSON.parse(localStorage.getItem('userProfile'));

  return [
    {
      value: currentProfile.id,
      label: `${currentProfile.first_name} ${currentProfile.last_name}`,
    },
  ];
}

export default function FlightForm() {
  const { projectId, datasetId } = useParams();
  const [open, setOpen] = useState(false);
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
                  `/api/v1/projects/${projectId}/datasets/${datasetId}/flights`,
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
                  <CustomTextField
                    type="date"
                    label="Acquisition date"
                    name="acquisitionDate"
                  />
                  <CustomTextField label="Altitude (m)" name="altitude" />
                  <CustomTextField label="Side overlap (%)" name="sideOverlap" />
                  <CustomTextField label="Forward overlap (%)" name="forwardOverlap" />
                  <CustomSelectField
                    label="Sensor"
                    name="sensor"
                    options={SENSOR_OPTIONS}
                  />
                  <CustomSelectField
                    label="Platform"
                    name="platform"
                    options={PLATFORM_OPTIONS}
                  />
                  <CustomSelectField label="Pilot" name="pilotId" options={pilots} />
                  <div className="mt-4">
                    <Button type="submit" disabled={isSubmitting}>
                      Create Flight
                    </Button>
                  </div>
                  {status && status.type && status.msg ? (
                    <div className="mt-4">
                      <Alert alertType={status.type}>{status.msg}</Alert>
                    </div>
                  ) : null}
                </Form>
                <div className="mt-4">
                  <UploadModal
                    open={open}
                    setOpen={setOpen}
                    apiRoute={`/api/v1/projects/${projectId}/datasets/${datasetId}/upload`}
                  />
                  <Button onClick={() => setOpen(true)}>Upload raw data (.tif)</Button>
                </div>
              </div>
            )}
          </Formik>
        </Card>
      </div>
    </div>
  );
}
