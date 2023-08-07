import { useState } from 'react';
import axios from 'axios';
import { Formik, Form } from 'formik';

import { CustomSubmitButton } from '../CustomButtons';
import CustomSelectField from '../CustomSelectField';
import CustomTextField from '../CustomTextField';

import initialValues, { PLATFORM_OPTIONS, SENSOR_OPTIONS } from './initialValues';

export default function FlightForm() {
  const [responseData, setResponseData] = useState(null);

  return (
    <div style={{ width: 450 }}>
      <Formik
        initialValues={initialValues}
        onSubmit={async (values, { setSubmitting }) => {
          try {
            const data = {
              acquisition_date: values.acquisitionDate,
              altitude: values.altitude,
              side_overlap: values.sideOverlap,
              forward_overlap: values.forwardOverlap,
              sensor: values.sensor,
              platform: values.platform,
            };
            const response = await axios.post('/api/v1/flights/', data, {
              headers: {
                Authorization: `Bearer ${localStorage.getItem('access_token')}`,
              },
            });
            if (response) {
              setResponseData(response.data);
            } else {
              // do something
            }
          } catch (err) {
            if (axios.isAxiosError(err)) {
              console.error(err);
            } else {
              // do something
            }
          }
          setSubmitting(false);
        }}
      >
        {({ isSubmitting }) => (
          <div className="m-4">
            <h1>Create Flight</h1>
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
              <div className="mt-4">
                <CustomSubmitButton disabled={isSubmitting}>
                  Create Flight
                </CustomSubmitButton>
                {responseData ? (
                  <pre>{JSON.stringify(responseData, undefined, 2)}</pre>
                ) : null}
              </div>
            </Form>
          </div>
        )}
      </Formik>
    </div>
  );
}
