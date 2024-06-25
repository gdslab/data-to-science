import axios, { AxiosResponse, isAxiosError } from 'axios';
import { Formik, Form } from 'formik';
import { Params, useLoaderData, useNavigate, useParams } from 'react-router-dom';

import Alert from '../../../Alert';
import { Button, OutlineButton } from '../../../Buttons';
import Card from '../../../Card';
import { SelectField, TextField } from '../../../InputFields';

import { classNames } from '../../../utils';
import { getInitialValues, PLATFORM_OPTIONS, SENSOR_OPTIONS } from './initialValues';
import validationSchema from './validationSchema';
import FlightDeleteModal from './FlightDeleteModal';
import { Flight } from '../Project';
import { useProjectContext } from '../ProjectContext';

export async function loader({ params }: { params: Params<string> }) {
  const flight = await axios.get(
    `/api/v1/projects/${params.projectId}/flights/${params.flightId}`
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
  const { flight } = useLoaderData() as { flight: Flight };
  const params = useParams();
  const navigate = useNavigate();
  const { projectRole, projectMembers } = useProjectContext();

  return (
    <div className={classNames(editMode ? 'w-1/2 m-8' : '', '')}>
      <Card>
        {!editMode ? <h1>Create Flight</h1> : <h1>Edit Flight</h1>}
        {projectMembers && projectMembers.length > 0 ? (
          <Formik
            initialValues={{
              ...getInitialValues(editMode ? flight : null),
              pilotId: editMode ? flight.pilot_id : projectMembers[0].member_id,
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
                  response = await axios.put(
                    `/api/v1/projects/${params.projectId}/flights/${flight.id}`,
                    data
                  );
                } else {
                  response = await axios.post(
                    `/api/v1/projects/${params.projectId}/flights`,
                    data
                  );
                }
                if (response) {
                  setStatus({ type: 'success', msg: editMode ? 'Updated' : 'Created' });
                  if (setOpen) setOpen(false);
                  navigate(`/projects/${params.projectId}`);
                } else {
                  // do something
                }
              } catch (err) {
                if (isAxiosError(err)) {
                  setStatus({ type: 'error', msg: err.response?.data.detail });
                } else {
                  setStatus({ type: 'error', msg: 'Unable to complete request' });
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
                <TextField label="Altitude (m)" name="altitude" />
                <TextField label="Side overlap (%)" name="sideOverlap" />
                <TextField label="Forward overlap (%)" name="forwardOverlap" />
                <SelectField label="Sensor" name="sensor" options={SENSOR_OPTIONS} />
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
                  {projectRole === 'owner' && editMode ? (
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
