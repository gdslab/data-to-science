import axios from 'axios';
import { Form, Formik } from 'formik';
import { useState } from 'react';
import { Link, useRevalidator } from 'react-router-dom';
import { MapIcon } from '@heroicons/react/24/outline';

import Alert from '../../Alert';
import { EditField, Editing, SelectField, TextField } from '../../InputFields';
import Modal from '../../Modal';
import { Location, Project } from './Project';
import { useProjectContext } from './ProjectContext';
import ProjectDeleteModal from './ProjectDeleteModal';
import ProjectFormMap from './ProjectFormMap';
import Table, { TableBody, TableHead } from '../../Table';

import { projectUpdateValidationSchema } from './validationSchema';
import { Team } from '../teams/Teams';

interface ProjectDetailEditForm {
  location: Location | null;
  project: Project;
  setLocation: React.Dispatch<React.SetStateAction<Location | null>>;
  teams: Team[];
}

export default function ProjectDetailEditForm({
  location,
  project,
  setLocation,
  teams,
}: ProjectDetailEditForm) {
  const [openUpload, setOpenUpload] = useState(false);
  const [openMap, setOpenMap] = useState(false);
  const [isEditing, setIsEditing] = useState<Editing>(null);

  const revalidator = useRevalidator();

  const { projectRole } = useProjectContext();

  const currentTeam = teams ? teams.filter(({ id }) => project.team_id === id) : null;

  return (
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
          const response = await axios.put(`/api/v1/projects/${project.id}`, data);
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
                  <Link to={`/projects/${project.id}/access`}>Manage Access</Link>
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
  );
}
