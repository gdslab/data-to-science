import { AxiosResponse, isAxiosError } from 'axios';
import { Formik, Form, useFormikContext } from 'formik';
import { useState } from 'react';
import {
  Params,
  useLoaderData,
  useNavigate,
  useParams,
  useRevalidator,
} from 'react-router';

import Alert from '../../../../Alert';
import { Button, OutlineButton } from '../../../../Buttons';
import Card from '../../../../Card';
import { SelectField, TextField } from '../../../../InputFields';
import FlightDeleteModal from './FlightDeleteModal';
import { Flight } from '../Project';

import {
  getInitialValues,
  PLATFORM_OPTIONS,
  SENSOR_OPTIONS,
} from './initialValues';
import validationSchema from './validationSchema';

import { useProjectContext } from '../ProjectContext';

function FtToMConverter() {
  const { setFieldValue } = useFormikContext();
  const [ftValue, setFtValue] = useState('');

  return (
    <div>
      <div className="flex items-start gap-2">
        <div className="flex-1">
          <TextField label="Altitude (meters)" name="altitude" />
        </div>
        <div>
          <label className="block text-sm text-gray-400 font-bold pt-2 pb-1">
            Convert from ft
          </label>
          <div className="flex items-center gap-1">
            <input
              type="number"
              value={ftValue}
              onChange={(e) => setFtValue(e.target.value)}
              placeholder="ft"
              className="focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-hidden border border-gray-400 rounded-sm py-1 px-2 w-24 appearance-none"
            />
            <button
              type="button"
              onClick={() => {
                const ft = parseFloat(ftValue);
                if (!isNaN(ft)) {
                  setFieldValue(
                    'altitude',
                    Math.round(ft * 0.3048 * 100) / 100,
                  );
                  setFtValue('');
                }
              }}
              className="bg-primary text-white text-sm font-medium rounded-sm py-1 px-2 hover:bg-primary/80 whitespace-nowrap"
            >
              ft &rarr; m
            </button>
          </div>
        </div>
      </div>
      <p className="text-xs text-gray-400 mt-1">
        If your altitude is in feet, use the &ldquo;Convert from ft&rdquo; field
        on the right to enter the value and click the button to automatically
        fill in the altitude in meters.
      </p>
    </div>
  );
}

import api from '../../../../../api';
import { classNames } from '../../../../utils';

export async function loader({ params }: { params: Params<string> }) {
  const flight = await api.get(
    `/projects/${params.projectId}/flights/${params.flightId}`,
  );

  if (flight) {
    return { flight: flight.data };
  } else {
    return null;
  }
}

export default function FlightForm({
  editMode = false,
  setOpen,
}: {
  editMode?: boolean;
  setOpen?: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const loaderData = useLoaderData() as { flight: Flight } | undefined;
  const flight = editMode ? loaderData?.flight : undefined;
  const params = useParams();
  const navigate = useNavigate();
  const revalidator = useRevalidator();
  const { projectRole, projectMembers } = useProjectContext();

  return (
    <div className={classNames(editMode ? 'w-1/2 m-8' : '', '')}>
      <Card>
        {!editMode ? <h1>Create Flight</h1> : <h1>Edit Flight</h1>}
        {projectMembers && projectMembers.length > 0 ? (
          <Formik
            initialValues={{
              ...getInitialValues(editMode && flight ? flight : null),
              pilotId:
                editMode && flight
                  ? flight.pilot_id
                  : projectMembers[0].member_id,
            }}
            validationSchema={validationSchema}
            onSubmit={async (values, { setSubmitting, setStatus }) => {
              try {
                const data = {
                  name: values.name,
                  acquisition_date: values.acquisitionDate,
                  altitude: values.altitude,
                  side_overlap: values.sideOverlap,
                  forward_overlap: values.forwardOverlap,
                  sensor: values.sensor,
                  pilot_id: values.pilotId,
                  platform:
                    values.platform === 'Other'
                      ? values.platformOther
                      : values.platform,
                };
                let response: AxiosResponse | null = null;
                if (editMode && flight) {
                  response = await api.put(
                    `/projects/${params.projectId}/flights/${flight.id}`,
                    data,
                  );
                } else {
                  response = await api.post(
                    `/projects/${params.projectId}/flights`,
                    data,
                  );
                }
                if (response) {
                  setStatus({
                    type: 'success',
                    msg: editMode ? 'Updated' : 'Created',
                  });
                  if (setOpen) {
                    // Modal usage - revalidate to refresh flights data, then close modal
                    revalidator.revalidate();
                    setOpen(false);
                  } else {
                    // Route usage - navigate back to project detail (will trigger loader)
                    navigate(`/projects/${params.projectId}`);
                  }
                } else {
                  // do something
                }
              } catch (err) {
                if (isAxiosError(err)) {
                  setStatus({ type: 'error', msg: err.response?.data.detail });
                } else {
                  setStatus({
                    type: 'error',
                    msg: 'Unable to complete request',
                  });
                }
              }
              setSubmitting(false);
            }}
          >
            {({ isSubmitting, status, values }) => (
              <Form>
                <TextField
                  label="Name"
                  name="name"
                  placeholder="Enter flight name (e.g., 'My Flight')"
                  required={false}
                />
                <TextField
                  type="date"
                  label="Acquisition date"
                  name="acquisitionDate"
                />
                <FtToMConverter />
                <TextField label="Side overlap (%)" name="sideOverlap" />
                <TextField label="Forward overlap (%)" name="forwardOverlap" />
                <SelectField
                  label="Sensor"
                  name="sensor"
                  options={SENSOR_OPTIONS}
                />
                <SelectField
                  label="Platform"
                  name="platform"
                  options={PLATFORM_OPTIONS}
                />
                {values && values.platform === 'Other' ? (
                  <TextField label="Platform other" name="platformOther" />
                ) : null}
                <SelectField
                  label="Pilot"
                  name="pilotId"
                  options={projectMembers.map(({ member_id, full_name }) => ({
                    label: full_name,
                    value: member_id,
                  }))}
                />
                <div className="flex flex-col gap-4 mt-4">
                  <Button type="submit" disabled={isSubmitting}>
                    {editMode ? 'Update' : 'Create'}
                  </Button>
                  <OutlineButton
                    onClick={(e) => {
                      e.preventDefault();
                      if (setOpen) {
                        setOpen(false);
                      } else {
                        navigate(`/projects/${params.projectId}`);
                      }
                    }}
                  >
                    Cancel
                  </OutlineButton>
                  {projectRole === 'owner' && editMode && flight ? (
                    <FlightDeleteModal flight={flight} iconOnly={false} />
                  ) : null}
                </div>
                {status && status.type && status.msg ? (
                  <div className="mt-4">
                    <Alert alertType={status.type}>{status.msg}</Alert>
                  </div>
                ) : null}
              </Form>
            )}
          </Formik>
        ) : (
          <span>Searching for pilots...</span>
        )}
      </Card>
    </div>
  );
}
