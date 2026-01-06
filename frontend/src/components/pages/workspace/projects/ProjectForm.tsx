import { isAxiosError } from 'axios';
import { Formik, Form } from 'formik';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';

import Alert from '../../../Alert';
import { Button } from '../../../Buttons';
import ProjectFormMap from './ProjectFormMap';
import { SelectField, TextField } from '../../../InputFields';
import { Team } from '../../teams/Teams';

import initialValues from './initialValues';
import { projectCreateValidationSchema } from './validationSchema';
import { useProjectContext } from './ProjectContext';

import api from '../../../../api';

export async function loader() {
  const response = await api.get('/teams', { params: { owner_only: true } });
  if (response) {
    const teams = response.data;
    teams.unshift({ title: 'No team', id: '' });
    return teams;
  } else {
    return [];
  }
}

export default function ProjectForm({
  setModalOpen,
}: {
  setModalOpen: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const navigate = useNavigate();
  const [teams, setTeams] = useState<Team[]>([]);

  const { locationDispatch, project } = useProjectContext();

  useEffect(() => {
    async function loadTeams() {
      try {
        const teams = await loader();
        if (teams) setTeams(teams);
      } catch {
        setTeams([]);
      }
    }
    loadTeams();
  }, []);

  useEffect(() => {
    if (!project) locationDispatch({ type: 'clear', payload: null });
  }, [locationDispatch, project]);

  return (
    <div className="my-8 mx-4">
      <h1>New Project</h1>
      <Formik
        initialValues={initialValues}
        validationSchema={projectCreateValidationSchema}
        onSubmit={async (values, { setStatus, setSubmitting }) => {
          try {
            const data = {
              title: values.title,
              description: values.description,
              location: values.location,
              team_id: values.teamId ? values.teamId : null,
              ...(values.plantingDate && {
                planting_date: values.plantingDate,
              }),
              ...(values.harvestDate && { harvest_date: values.harvestDate }),
            };
            const response = await api.post('/projects', data);
            if (response && response.status === 201) {
              navigate('/projects');
              setModalOpen(false);
            } else {
              setStatus({
                type: 'error',
                msg: 'Unexpected error occurred. Unable to create project.',
              });
            }
          } catch (err) {
            if (isAxiosError(err) && err.response && err.response.data.detail) {
              setStatus({
                type: 'error',
                msg: err.response.data.detail,
              });
            } else {
              setStatus({
                type: 'error',
                msg: 'Unexpected error occurred. Unable to create project.',
              });
            }
          }
          setSubmitting(false);
        }}
      >
        {({ isSubmitting, status }) => (
          <Form>
            <div className="grid md:grid-cols-2 grid-cols-1 gap-8">
              <div>
                <div className="inline text-sm text-gray-400 font-bold pt-2 pb-1">
                  Field location*
                </div>
                <ProjectFormMap />
              </div>
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
                    label="Start of project"
                    name="plantingDate"
                    required={false}
                  />
                  <TextField
                    type="date"
                    label="End of project"
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
