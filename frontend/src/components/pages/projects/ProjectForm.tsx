import { useState } from 'react';
import axios from 'axios';
import { Formik, Form } from 'formik';
import { useLoaderData, useNavigate } from 'react-router-dom';

import Alert from '../../Alert';
import { Button } from '../../Buttons';
import Card from '../../Card';
import FileUpload from '../../FileUpload';
import MapModal from '../../maps/MapModal';
import { SelectField, TextField } from '../../InputFields';

import initialValues from './initialValues';
import validationSchema from './validationSchema';

interface Team {
  id: string;
  title: string;
  description: string;
}

export async function loader() {
  const response = await axios.get('/api/v1/teams');
  if (response) {
    const teams = response.data;
    teams.unshift({ title: 'No team', id: '' });
    return teams;
  } else {
    return [];
  }
}

export default function ProjectForm({
  editMode = false,
  projectId = '',
}: {
  editMode?: boolean;
  projectId?: string;
}) {
  const navigate = useNavigate();
  const teams = useLoaderData() as Team[];
  const [open, setOpen] = useState(false);
  return (
    <div className="h-full flex flex-wrap items-center justify-center bg-accent1">
      <div className="sm:w-full md:w-1/3 max-w-xl mx-4">
        <h1 className="ml-4 text-white">
          {editMode ? 'Project Details' : 'Create project'}
        </h1>
        <Card>
          <Formik
            initialValues={initialValues}
            validationSchema={validationSchema}
            onSubmit={async (values, { setSubmitting }) => {
              try {
                const data = {
                  title: values.title,
                  description: values.description,
                  location_id: values.locationId,
                  planting_date: values.plantingDate,
                  ...(values.harvestDate && { harvest_date: values.harvestDate }),
                  ...(values.teamId && { team_id: values.teamId }),
                };
                const response = editMode
                  ? await axios.put(`/api/v1/projects/${projectId}`, data)
                  : await axios.post('/api/v1/projects', data);
                if (response) {
                  editMode ? navigate(`/projects/${projectId}`) : navigate('/projects');
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
            {({ isSubmitting, status }) => (
              <div>
                <Form>
                  <TextField label="Title" name="title" />
                  <TextField label="Description" name="description" />
                  <TextField label="Location ID" name="locationId" disabled={true} />
                  <div className="mt-4">
                    <MapModal open={open} setOpen={setOpen} />
                    <Button onClick={() => setOpen(true)}>Draw on map</Button>
                    <span className="block text-sm text-gray-400 font-bold pt-2 pb-1">
                      or
                    </span>
                    <FileUpload
                      restrictions={{
                        allowedFileTypes: ['.shp', '.shx', '.dbf', '.prj'],
                        maxNumberOfFiles: 1,
                      }}
                      endpoint={`/api/v1/projects/${projectId}/upload`}
                    />
                  </div>
                  <TextField type="date" label="Planting date" name="plantingDate" />
                  <TextField
                    type="date"
                    label="Harvest date"
                    name="harvestDate"
                    required={false}
                  />
                  {teams.length > 0 ? (
                    <SelectField
                      label="Team"
                      name="teamId"
                      options={teams.map((team) => ({
                        label: team.title,
                        value: team.id,
                      }))}
                    />
                  ) : null}
                  <div className="mt-4">
                    <Button type="submit" disabled={isSubmitting}>
                      {editMode ? 'Update project' : 'Create project'}
                    </Button>
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
