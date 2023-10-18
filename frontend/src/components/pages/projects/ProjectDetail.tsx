import axios from 'axios';
import { Form, Formik } from 'formik';
import { useEffect, useState } from 'react';
import {
  Link,
  Params,
  useLoaderData,
  useParams,
  useNavigate,
  useRevalidator,
} from 'react-router-dom';
import { MapIcon, TrashIcon, PencilIcon } from '@heroicons/react/24/outline';

import Alert from '../../Alert';
import { Button } from '../../Buttons';
import { ConfirmationPopup } from '../../ConfirmationPopup';
import { Editing, EditField, SelectField, TextField } from '../../InputFields';
import FlightForm from './flights/FlightForm';
import { GeoJSONFeature, Location } from './ProjectForm';
import Modal from '../../Modal';
import ProjectFormMap from './ProjectFormMap';
import Table, { TableBody, TableHead } from '../../Table';

import { DefaultSymbologySettings } from '../../maps/MapContext';
import { Team } from '../teams/Teams';
import validationSchema from './validationSchema';

interface Project {
  id: string;
  title: string;
  description: string;
  planting_date: string;
  harvest_date: string;
  location_id: string;
  team_id: string;
  is_owner: boolean;
  field: GeoJSONFeature;
}

export interface Band {
  data_type: string;
  nodata: string | null;
  stats: {
    mean: number;
    stddev: number;
    maximum: number;
    minimum: number;
  };
  unit: string;
}

export interface EO {
  name: string;
  description: string;
}

export interface DataProduct {
  id: string;
  data_type: string;
  original_filename: string;
  filepath: string;
  url: string;
  flight_id: string;
  stac_properties: {
    raster: Band[];
    eo: EO[];
  };
  user_style: null | DefaultSymbologySettings;
}

export interface Flight {
  id: string;
  acquisition_date: Date;
  altitude: number;
  side_overlap: number;
  forward_overlap: number;
  sensor: string;
  platform: string;
  project_id: string;
  pilot_id: string;
  data_products: DataProduct[];
}

export interface Pilot {
  label: string;
  value: string;
}

interface ProjectData {
  pilots: Pilot[];
  project: Project;
  flights: Flight[];
  teams: Team[];
}

export async function loader({ params }: { params: Params<string> }) {
  const pilots = await axios.get(`/api/v1/projects/${params.projectId}/members`);
  const project = await axios.get(`/api/v1/projects/${params.projectId}`);
  const flights = await axios.get(`/api/v1/projects/${params.projectId}/flights`);
  const teams = await axios.get(`/api/v1/teams`);
  if (pilots && project && flights && teams) {
    const teamsf = teams.data;
    teamsf.unshift({ title: 'No team', id: '' });
    return {
      pilots: pilots.data,
      project: project.data,
      flights: flights.data,
      teams: teamsf,
    };
  } else {
    return null;
  }
}

export default function ProjectDetail() {
  const navigate = useNavigate();
  const { project, flights, teams } = useLoaderData() as ProjectData;
  const { projectId } = useParams();
  const revalidator = useRevalidator();

  const [location, setLocation] = useState<Location | null>(null);
  const [openUpload, setOpenUpload] = useState(false);
  const [openConfirmationPopup, setOpenConfirmationPopup] = useState(false);
  const [open, setOpen] = useState(false);
  const [openMap, setOpenMap] = useState(false);
  const [isEditing, setIsEditing] = useState<Editing>(null);

  const currentTeam = teams ? teams.filter(({ id }) => project.team_id === id) : null;

  useEffect(() => {
    if (project.field) {
      setLocation({
        geojson: project.field,
        center: {
          lat: parseFloat(project.field.properties.center_y),
          lng: parseFloat(project.field.properties.center_x),
        },
        type: 'uploaded',
      });
    }
  }, [project]);

  useEffect(() => {
    if (location) revalidator.revalidate();
  }, []);

  return (
    <div className="mx-4 mt-4">
      {project.is_owner ? (
        <div>
          <Formik
            initialValues={{
              title: project.title,
              description: project.description,
              plantingDate: project.planting_date,
              harvestDate: project.harvest_date ? project.harvest_date : '',
              locationId: project.location_id,
              teamId: project.team_id ? project.team_id : '',
            }}
            validationSchema={validationSchema}
            onSubmit={async (values) => {
              try {
                const data = {
                  title: values.title,
                  description: values.description,
                  location_id: values.locationId,
                  planting_date: values.plantingDate,
                  ...(values.harvestDate && { harvest_date: values.harvestDate }),
                  ...(values.teamId && { team_id: values.teamId }),
                };
                const response = await axios.put(
                  `/api/v1/projects/${project.id}`,
                  data
                );
                if (response) {
                  revalidator.revalidate();
                }
                setIsEditing(null);
              } catch (err) {
                setIsEditing(null);
              }
            }}
          >
            {({ setStatus, status }) => (
              <Form>
                <div className="grid rows-auto gap-2">
                  <EditField
                    fieldName="title"
                    isEditing={isEditing}
                    setIsEditing={setIsEditing}
                  >
                    {!isEditing || isEditing.field !== 'title' ? (
                      <h2 className="mb-0">{project.title}</h2>
                    ) : (
                      <TextField name="title" />
                    )}
                  </EditField>
                  <EditField
                    fieldName="description"
                    isEditing={isEditing}
                    setIsEditing={setIsEditing}
                  >
                    {!isEditing || isEditing.field !== 'description' ? (
                      <span className="text-gray-600">{project.description}</span>
                    ) : (
                      <TextField name="description" />
                    )}
                  </EditField>
                </div>
                <Table>
                  <TableHead
                    columns={['Planting Date', 'Harvest Date', 'Team', 'Location']}
                  />
                  <TableBody
                    rows={[
                      [
                        <EditField
                          fieldName="plantingDate"
                          isEditing={isEditing}
                          setIsEditing={setIsEditing}
                        >
                          {!isEditing || isEditing.field !== 'plantingDate' ? (
                            <span className="text-gray-600">
                              {project.planting_date}
                            </span>
                          ) : (
                            <TextField type="date" name="plantingDate" />
                          )}
                        </EditField>,
                        <EditField
                          fieldName="harvestDate"
                          isEditing={isEditing}
                          setIsEditing={setIsEditing}
                        >
                          {!isEditing || isEditing.field !== 'harvestDate' ? (
                            <span className="text-gray-600">
                              {project.harvest_date}
                            </span>
                          ) : (
                            <TextField type="date" name="harvestDate" />
                          )}
                        </EditField>,
                        <EditField
                          fieldName="teamId"
                          isEditing={isEditing}
                          setIsEditing={setIsEditing}
                        >
                          {!isEditing || isEditing.field !== 'teamId' ? (
                            <span className="text-gray-600">
                              {currentTeam && currentTeam.length > 0
                                ? currentTeam[0].title
                                : ''}
                            </span>
                          ) : (
                            <SelectField
                              name="teamId"
                              options={teams.map((team) => ({
                                label: team.title,
                                value: team.id,
                              }))}
                            />
                          )}
                        </EditField>,
                        <div>
                          <MapIcon
                            className="h-6 w-6 cursor-pointer"
                            onClick={() => {
                              setStatus(null);
                              setOpenMap(true);
                            }}
                          />
                          <span className="sr-only">View or Edit Location</span>
                          <Modal open={openMap} setOpen={setOpenMap}>
                            <div className="m-4">
                              <ProjectFormMap
                                isUpdate={true}
                                location={location}
                                locationId={project.location_id}
                                open={openUpload}
                                projectId={project.id}
                                setLocation={setLocation}
                                setOpen={setOpenUpload}
                              />
                            </div>
                            {status && status.type && status.msg ? (
                              <div className="m-4">
                                <Alert alertType={status.type}>{status.msg}</Alert>
                              </div>
                            ) : null}
                          </Modal>
                        </div>,
                      ],
                    ]}
                  />
                </Table>
                <div className="flex flex-row justify-end w-full mt-4">
                  <Button
                    type="button"
                    size="sm"
                    icon="trash"
                    onClick={() => setOpenConfirmationPopup(true)}
                  >
                    Deactivate project
                  </Button>
                  <Modal
                    open={openConfirmationPopup}
                    setOpen={setOpenConfirmationPopup}
                  >
                    <ConfirmationPopup
                      title="Are you sure you want to deactivate this project?"
                      content="Deactivating this project will cause all team and project members to immediately lose access to any flights, and data associated with the project."
                      confirmText="Yes, deactivate"
                      rejectText="No, keep project"
                      setOpen={setOpenConfirmationPopup}
                      action={async () => {
                        try {
                          const response = await axios.delete(
                            `/api/v1/projects/${project.id}`
                          );
                          if (response) {
                            setOpenConfirmationPopup(false);
                            navigate('/projects', { state: { reload: true } });
                          } else {
                            setOpenConfirmationPopup(false);
                            setStatus({
                              type: 'error',
                              msg: 'Unable to deactivate project',
                            });
                          }
                        } catch (err) {
                          setOpenConfirmationPopup(false);
                          setStatus({
                            type: 'error',
                            msg: 'Unable to deactivate project',
                          });
                        }
                      }}
                    />
                  </Modal>
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
      ) : null}
      <div className="mt-4">
        <h2>Flights</h2>
        {flights.length > 0 ? (
          <Table>
            <TableHead
              columns={['Platform', 'Sensor', 'Acquisition Date', 'Data', 'Actions']}
            />
            <TableBody
              rows={flights.map((flight) => [
                flight.platform.replace(/_/g, ' '),
                flight.sensor,
                new Date(flight.acquisition_date).toLocaleDateString('en-US'),
                <Link
                  className="text-sky-600"
                  to={`/projects/${projectId}/flights/${flight.id}/data`}
                >
                  View Data
                </Link>,
              ])}
              actions={flights.map((flight, i) => [
                {
                  key: `action-edit-${i}`,
                  icon: <PencilIcon className="h-4 w-4" />,
                  label: 'Edit',
                  url: `/projects/${projectId}/flights/${flight.id}/edit`,
                },
                {
                  key: `action-delete-${i}`,
                  icon: <TrashIcon className="h-4 w-4" />,
                  label: 'Delete',
                  url: '#',
                },
              ])}
            />
          </Table>
        ) : null}
      </div>
      {projectId ? (
        <div className="mt-4 flex justify-center">
          <Button onClick={() => setOpen(true)}>Add New Flight</Button>
          <Modal open={open} setOpen={setOpen}>
            <FlightForm projectId={projectId} setOpen={setOpen} />
          </Modal>
        </div>
      ) : null}
    </div>
  );
}
