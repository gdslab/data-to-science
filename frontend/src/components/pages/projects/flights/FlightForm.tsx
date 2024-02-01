import axios, { AxiosResponse, isAxiosError } from 'axios';
import { Formik, Form } from 'formik';
import { useContext, useEffect, useState } from 'react';
import { Params, useLoaderData, useNavigate, useParams } from 'react-router-dom';

import Alert from '../../../Alert';
import { Button, OutlineButton } from '../../../Buttons';
import Card from '../../../Card';
import { SelectField, TextField } from '../../../InputFields';
import AuthContext, { User } from '../../../../AuthContext';

import { classNames } from '../../../utils';
import { getInitialValues, PLATFORM_OPTIONS, SENSOR_OPTIONS } from './initialValues';
import validationSchema from './validationSchema';
import { Flight, Pilot } from '../ProjectDetail';
import FlightDeleteModal from './FlightDeleteModal';
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

function fetchPilotFromUserProfile(user: User | null) {
  if (user) {
    return [{ label: `${user.first_name} ${user.last_name}`, value: user.id }];
  } else {
    return [];
  }
}

async function fetchPilots(teamId: string | undefined, user: User | null) {
  if (teamId) {
    try {
      const response = await axios.get(`/api/v1/teams/${teamId}/members`);
      if (response) {
        const pilots = response.data.map(({ full_name, member_id }) => ({
          label: full_name,
          value: member_id,
        }));
        if (pilots.length === 0) {
          return fetchPilotFromUserProfile(user);
        } else {
          return pilots;
        }
      } else {
        return [];
      }
    } catch (err) {
      return [];
    }
  } else {
    return fetchPilotFromUserProfile(user);
  }
}

export default function FlightForm({
  editMode = false,
  teamId,
  setOpen,
}: {
  editMode?: boolean;
  teamId?: string | undefined;
  setOpen?: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const { flight } = useLoaderData() as { flight: Flight };
  const params = useParams();
  const navigate = useNavigate();
  const [pilots, setPilots] = useState<Pilot[]>([]);
  const { user } = useContext(AuthContext);
  const { projectRole } = useProjectContext();

  useEffect(() => {
    fetchPilots(teamId, user)
      .then((data) => setPilots(data))
      .catch((err) => console.error(err));
  }, []);

  return (
    <div className={classNames(editMode ? 'w-1/2 m-8' : '', '')}>
      <Card>
        {!editMode ? <h1>Create Flight</h1> : <h1>Edit Flight</h1>}
        {pilots.length > 0 ? (
          <Formik
            initialValues={{
              ...getInitialValues(editMode ? flight : null),
              pilotId: pilots[0].value,
            }}
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
                  setStatus({ type: 'success', msg: 'Created' });
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
            {({ isSubmitting, status }) => (
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
