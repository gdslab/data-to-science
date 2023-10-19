import { useEffect, useState } from 'react';
import axios from 'axios';
import { Formik, Form } from 'formik';
import { useNavigate } from 'react-router-dom';

import Alert from '../../Alert';
import { Button } from '../../Buttons';
import ProjectFormMap from './ProjectFormMap';
import { SelectField, TextField } from '../../InputFields';
import { Team } from '../teams/Teams';

import initialValues from './initialValues';
import validationSchema from './validationSchema';

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

export type Coordinates = number[][];

export interface GeoJSONFeature {
  type: string;
  geometry: {
    type: string;
    coordinates: Coordinates[] | Coordinates[][];
  };
  properties: {
    [key: string]: string;
  };
}

export interface FeatureCollection {
  type: 'FeatureCollection';
  features: GeoJSON.Feature[];
}

export interface Location {
  geojson: GeoJSONFeature;
  center: {
    lat: number;
    lng: number;
  };
  type: string;
}

export type SetLocation = React.Dispatch<React.SetStateAction<Location | null>>;

export default function ProjectForm({
  setModalOpen,
}: {
  setModalOpen: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const navigate = useNavigate();
  const [teams, setTeams] = useState<Team[]>([]);
  const [location, setLocation] = useState<Location | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    async function loadTeams() {
      try {
        const teams = await loader();
        if (teams) setTeams(teams);
      } catch (err) {
        setTeams([]);
      }
    }
    loadTeams();
  }, []);

  return (
    <div className="my-8 mx-4">
      <h1>New Project</h1>
      <Formik
        initialValues={initialValues}
        validationSchema={validationSchema}
        onSubmit={async (values, { setSubmitting }) => {
          try {
            const data = {
              title: values.title,
              description: values.description,
              location_id: values.locationId,
              team_id: values.teamId ? values.teamId : null,
              ...(values.plantingDate && { planting_date: values.plantingDate }),
              ...(values.harvestDate && { harvest_date: values.harvestDate }),
            };
            const response = await axios.post('/api/v1/projects', data);
            if (response) {
              navigate('/projects');
              setModalOpen(false);
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
        {({ isSubmitting, status, values }) => (
          <Form>
            <div className="grid md:grid-cols-2 grid-cols-1 gap-8">
              <ProjectFormMap
                location={location}
                locationId={values.locationId}
                open={open}
                setLocation={setLocation}
                setOpen={setOpen}
              />
              <div className="">
                <TextField label="Title" name="title" />
                <TextField
                  type="textarea"
                  label="Description"
                  name="description"
                  placeholder="Enter a description of the project..."
                />
                <div className="grid grid-cols-2 gap-4">
                  <TextField
                    type="date"
                    label="Planting date"
                    name="plantingDate"
                    required={false}
                  />
                  <TextField
                    type="date"
                    label="Harvest date"
                    name="harvestDate"
                    required={false}
                  />
                </div>
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
              </div>
            </div>
            {status && status.type && status.msg ? (
              <div className="mt-4">
                <Alert alertType={status.type}>{status.msg}</Alert>
              </div>
            ) : null}
            <div className="flex justify-center mt-4 w-full">
              <div className="w-96">
                <Button type="submit" disabled={isSubmitting}>
                  Create
                </Button>
              </div>
            </div>
          </Form>
        )}
      </Formik>
    </div>
  );
}
