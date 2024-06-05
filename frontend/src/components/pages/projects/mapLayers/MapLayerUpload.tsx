import axios, { isAxiosError, AxiosResponse } from 'axios';
import { ErrorMessage, Form, Formik } from 'formik';
import { FeatureCollection } from 'geojson';
import { useState } from 'react';
import { useParams } from 'react-router-dom';

import Alert, { Status } from '../../../Alert';
import MapLayerFileInput from './MapLayerFileInput';
import { Button } from '../../../Buttons';
import { useProjectContext } from '../ProjectContext';

import { validationSchema } from './validationSchema';

export default function MapLayerUpload() {
  const [mlFileInputKey, setMLFileInputKey] = useState(Date.now());
  const [status, setStatus] = useState<Status | null>(null);
  const { projectId } = useParams();

  const { mapLayersDispatch } = useProjectContext();

  return (
    <div className="flex flex-col gap-8">
      <h3>Add new map layer</h3>
      <p>
        Shapefile and GeoJSON datasets{' '}
        <strong>must be in the WGS84 coordinate system.</strong>
      </p>
      <Formik
        initialValues={{ layerName: '', geojson: null }}
        validationSchema={validationSchema}
        onSubmit={async (values, actions) => {
          try {
            const response: AxiosResponse<FeatureCollection> = await axios.post(
              `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}/vector_layers`,
              { layer_name: values.layerName, geojson: values.geojson }
            );
            if (response.status === 201) {
              setStatus({ type: 'success', msg: 'Project layer added' });
              // reset upload form
              actions.resetForm();
              // update key for file input elem (clears out previous file)
              setMLFileInputKey(Date.now());
              // update map layer context with new map layer
              mapLayersDispatch({ type: 'update', payload: [response.data] });
            } else {
              setStatus({ type: 'error', msg: 'Unable to add project layer' });
              // reset upload form
              actions.resetForm();
              // update key for file input elem (clears out previous file)
              setMLFileInputKey(Date.now());
            }
          } catch (err) {
            if (isAxiosError(err)) {
              setStatus({ type: 'error', msg: err.response?.data.detail });
            } else {
              setStatus({ type: 'error', msg: 'Unable to add project layer' });
            }
            // reset upload form
            actions.resetForm();
            // update key for file input elem (clears out previous file)
            setMLFileInputKey(Date.now());
          }
        }}
      >
        {() => (
          <Form className="flex flex-col gap-4">
            {/* Form input fields */}
            <MapLayerFileInput inputKey={mlFileInputKey} setStatus={setStatus} />
            {/* Display formik error messages related to GeoJSON object */}
            <ErrorMessage name="geojson" component="span" className="text-red-500" />
            {/* Submit button */}
            <Button type="submit">Upload</Button>
            {/* Display any error messages from backend API */}
            {status && status.type && status.msg ? (
              <Alert alertType={status.type}>{status.msg}</Alert>
            ) : null}
          </Form>
        )}
      </Formik>
    </div>
  );
}
