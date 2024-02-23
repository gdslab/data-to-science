import axios from 'axios';
import { Form, Formik } from 'formik';
import { useEffect, useState } from 'react';
import {
  Link,
  Params,
  useLoaderData,
  useParams,
  useRevalidator,
} from 'react-router-dom';
import { MapIcon, PencilIcon } from '@heroicons/react/24/outline';

import Alert from '../../Alert';
import { Button } from '../../Buttons';
import { Editing, EditField, SelectField, TextField } from '../../InputFields';
import FlightCarousel from './flights/FlightCarousel';
import FlightForm from './flights/FlightForm';
import { GeoJSONFeature, Location } from './ProjectForm';
import Modal from '../../Modal';
import ProjectFormMap from './ProjectFormMap';
import Table, { TableBody, TableHead } from '../../Table';
import TableCardRadioInput from '../../TableCardRadioInput';
import { User } from '../../../AuthContext';
import { SymbologySettings } from '../../maps/MapContext';
import { Team } from '../teams/Teams';
import { projectUpdateValidationSchema } from './validationSchema';
import { sorter } from '../../utils';
import { useProjectContext } from './ProjectContext';
import FlightDeleteModal from './flights/FlightDeleteModal';
import ProjectDeleteModal from './ProjectDeleteModal';

interface FieldProperties {
  [key: string]: string;
}

export type FieldGeoJSONFeature = Omit<GeoJSON.Feature, 'properties'> & {
  properties: FieldProperties;
};

export interface Project {
  id: string;
  title: string;
  description: string;
  planting_date: string;
  harvest_date: string;
  location_id: string;
  team_id: string;
  flight_count: number;
  owner_id: string;
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
  public: boolean;
  stac_properties: {
    raster: Band[];
    eo: EO[];
  };
  user_style: SymbologySettings;
}

export interface Flight {
  id: string;
  acquisition_date: string;
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
  role: string;
  flights: Flight[];
  teams: Team[];
}

export async function loader({ params }: { params: Params<string> }) {
  const profile = localStorage.getItem('userProfile');
  const user: User | null = profile ? JSON.parse(profile) : null;
  if (!user) return null;

  try {
    const project = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}`
    );
    const project_member = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}/members/${
        user.id
      }`
    );
    const flights = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}/flights`
    );
    const teams = await axios.get(`${import.meta.env.VITE_API_V1_STR}/teams`);

    if (project && project_member && flights && teams) {
      const teamsf = teams.data;
      teamsf.unshift({ title: 'No team', id: '' });
      return {
        project: project.data,
        role: project_member.data.role,
        flights: flights.data,
        teams: teamsf,
      };
    } else {
      return {
        project: null,
        role: null,
        flights: [],
        teams: [],
      };
    }
  } catch (err) {
    return {
      project: null,
      role: null,
      flights: [],
      teams: [],
    };
  }
}

export default function ProjectDetail() {
  const { project, role, flights, teams } = useLoaderData() as ProjectData;
  const { projectId } = useParams();
  const revalidator = useRevalidator();
  const { projectRole, flightsDispatch, projectDispatch, projectRoleDispatch } =
    useProjectContext();

  const [location, setLocation] = useState<Location | null>(null);
  const [tableView, toggleTableView] = useState<'table' | 'carousel'>('carousel');
  const [openUpload, setOpenUpload] = useState(false);
  const [open, setOpen] = useState(false);
  const [openMap, setOpenMap] = useState(false);

  const [isEditing, setIsEditing] = useState<Editing>(null);
  const [flightSortOrder, setFlightSortOrder] = useState('asc');

  const currentTeam = teams ? teams.filter(({ id }) => project.team_id === id) : null;

  useEffect(() => {
    if (project && project.field) {
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
    if (role) projectRoleDispatch({ type: 'set', payload: role });
  }, [role]);

  useEffect(() => {
    // @ts-ignore
    if (project) projectDispatch({ type: 'set', payload: project });
  }, [project]);

  useEffect(() => {
    if (flights) flightsDispatch({ type: 'set', payload: flights });
  }, [flights]);

  useEffect(() => {
    if (location) revalidator.revalidate();
  }, []);

  const flightColumns = ['Platform', 'Sensor', 'Acquisition Date', 'Data', 'Actions'];

  if (project) {
    return (
      <div className="flex flex-col h-full gap-4 p-4">
        {projectRole === 'owner' || projectRole === 'manager' ? (
          <Formik
            initialValues={{
              title: project.title,
              description: project.description,
              plantingDate: project.planting_date ? project.planting_date : '',
              harvestDate: project.harvest_date ? project.harvest_date : '',
              locationId: project.location_id,
              teamId: project.team_id ? project.team_id : '',
            }}
            validationSchema={projectUpdateValidationSchema}
            onSubmit={async (values) => {
              try {
                const data = {
                  title: values.title,
                  description: values.description,
                  location_id: values.locationId,
                  team_id: values.teamId ? values.teamId : null,
                  ...(values.plantingDate && { planting_date: values.plantingDate }),
                  ...(values.harvestDate && { harvest_date: values.harvestDate }),
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
                <div className="flex justify-between">
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
                  {projectRole === 'owner' ? (
                    <div className="text-sky-600 cursor-pointer">
                      <h2>
                        <Link to={`/projects/${projectId}/access`}>Manage Access</Link>
                      </h2>
                    </div>
                  ) : null}
                </div>
                <Table>
                  <TableHead
                    columns={['Planting Date', 'Harvest Date', 'Team', 'Location']}
                  />
                  <TableBody
                    rows={[
                      [
                        <div className="flex justify-center">
                          <EditField
                            fieldName="plantingDate"
                            isEditing={isEditing}
                            setIsEditing={setIsEditing}
                          >
                            {!isEditing || isEditing.field !== 'plantingDate' ? (
                              <span>
                                {project.planting_date ? project.planting_date : 'N/A'}
                              </span>
                            ) : (
                              <TextField type="date" name="plantingDate" />
                            )}
                          </EditField>
                        </div>,
                        <div className="flex justify-center">
                          <EditField
                            fieldName="harvestDate"
                            isEditing={isEditing}
                            setIsEditing={setIsEditing}
                          >
                            {!isEditing || isEditing.field !== 'harvestDate' ? (
                              <span>
                                {project.harvest_date ? project.harvest_date : 'N/A'}
                              </span>
                            ) : (
                              <TextField type="date" name="harvestDate" />
                            )}
                          </EditField>
                        </div>,
                        <div className="flex justify-center">
                          <EditField
                            fieldName="teamId"
                            isEditing={isEditing}
                            setIsEditing={setIsEditing}
                          >
                            {!isEditing || isEditing.field !== 'teamId' ? (
                              <span>
                                {currentTeam && currentTeam.length > 0
                                  ? currentTeam[0].title
                                  : 'N/A'}
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
                          </EditField>
                        </div>,
                        <div className="flex justify-center">
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
                  <ProjectDeleteModal project={project} />
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
          <div>
            <h2 className="mb-0">{project.title}</h2>
            <span className="text-gray-600">{project.description}</span>
          </div>
        )}
        <div className="grow min-h-0">
          <div className="h-full flex flex-col gap-4">
            <div className="h-24">
              <h2>Flights</h2>
              <div className="flex justify-between">
                <div className="flex flex-row items-center gap-2">
                  <label
                    htmlFor="flightSortOrder"
                    className="text-sm font-medium text-gray-900 w-20"
                  >
                    Sort by
                  </label>
                  <select
                    name="flightSortOrder"
                    id="flightSortOrder"
                    className="w-full px-1.5 font-semibold rounded-md border-2 border-zinc-300 text-gray-700 sm:text-sm"
                    onChange={(e) => setFlightSortOrder(e.target.value)}
                  >
                    <option value="asc">Date (ascending)</option>
                    <option value="desc">Date (descending)</option>
                  </select>
                </div>
                <TableCardRadioInput
                  tableView={tableView}
                  toggleTableView={toggleTableView}
                />
              </div>
            </div>
            {flights.length > 0 ? (
              tableView === 'table' ? (
                <Table>
                  <TableHead
                    columns={
                      role === 'viewer'
                        ? flightColumns.slice(0, flightColumns.length - 1)
                        : flightColumns
                    }
                  />
                  <TableBody
                    rows={flights
                      .sort((a, b) =>
                        sorter(
                          new Date(a.acquisition_date),
                          new Date(b.acquisition_date),
                          flightSortOrder
                        )
                      )
                      .map((flight) => [
                        flight.platform.replace(/_/g, ' '),
                        flight.sensor,
                        flight.acquisition_date,
                        <Link
                          className="!text-sky-600 visited:text-sky-600"
                          to={`/projects/${projectId}/flights/${flight.id}/data`}
                        >
                          Manage
                        </Link>,
                      ])}
                    actions={
                      role === 'viewer'
                        ? undefined
                        : flights.map((flight, i) => {
                            const editAction = {
                              key: `action-edit-${i}`,
                              icon: <PencilIcon className="h-4 w-4" />,
                              label: 'Edit',
                              url: `/projects/${projectId}/flights/${flight.id}/edit`,
                            };
                            const deleteAction = {
                              key: `action-delete-${i}`,
                              type: 'component',
                              component: (
                                <FlightDeleteModal flight={flight} tableView={true} />
                              ),
                              label: 'Delete',
                            };
                            if (role === 'owner') return [editAction, deleteAction];
                            return [editAction];
                          })
                    }
                  />
                </Table>
              ) : (
                <div className="h-full min-h-96">
                  <FlightCarousel flights={flights} sortOrder={flightSortOrder} />
                </div>
              )
            ) : null}
            {role !== 'viewer' ? (
              <div className="my-4 flex justify-center">
                <Modal open={open} setOpen={setOpen}>
                  <FlightForm setOpen={setOpen} />
                </Modal>
                <Button size="sm" onClick={() => setOpen(true)}>
                  Add New Flight
                </Button>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    );
  } else {
    return (
      <div className="flex flex-col h-full gap-4 p-4">
        Unable to load selected project
      </div>
    );
  }
}
