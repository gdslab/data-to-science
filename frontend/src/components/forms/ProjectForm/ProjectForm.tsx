import { useState } from 'react';
import axios from 'axios';
import { Formik, Form } from 'formik';
import { useLoaderData, useNavigate } from 'react-router-dom';

import Alert from '../../Alert';
import { CustomButton, CustomSubmitButton } from '../CustomButtons';
import CustomSelectField from '../CustomSelectField';
import CustomTextField from '../CustomTextField';

import initialValues, { InitialValues } from './initialValues';
import validationSchema from './validationSchema';

interface Team {
  id: string;
  title: string;
  description: string;
}

export async function loader() {
  const response = await axios.get('/api/v1/teams/');
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
  storedValues,
}: {
  editMode: boolean;
  projectId?: string;
  storedValues?: InitialValues;
}) {
  const navigate = useNavigate();
  const teams = useLoaderData() as Team[];
  return (
    <div className="m-4" style={{ width: 450 }}>
      <Formik
        initialValues={storedValues ? storedValues : initialValues}
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
              : await axios.post('/api/v1/projects/', data);
            if (response) {
              navigate('/projects');
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
        {({ isSubmitting, setFieldTouched, setFieldValue, status, values }) => (
          <div>
            <h1>{editMode ? 'Edit project' : 'Create project'}</h1>
            <Form>
              <CustomTextField label="Title" name="title" />
              <CustomTextField label="Description" name="description" />
              <CustomTextField label="Location" name="locationId" />
              {!values.locationId ? (
                <div className="mt-4">
                  <CustomButton
                    onClick={async () => {
                      try {
                        const data = {
                          name: `Field ${new Date().toString()}`,
                          geom: 'SRID=4326;POLYGON((0 0,1 0,1 1,0 1,0 0))',
                        };
                        const response = await axios.post('/api/v1/locations/', data);
                        if (response) {
                          setFieldValue('locationId', response.data.id);
                          setFieldTouched('locationId', true);
                        }
                      } catch (err) {
                        if (axios.isAxiosError(err)) {
                          console.error(err);
                        } else {
                          // do something
                        }
                      }
                    }}
                  >
                    Add Location
                  </CustomButton>
                </div>
              ) : null}
              <CustomTextField type="date" label="Planting date" name="plantingDate" />
              <CustomTextField type="date" label="Harvest date" name="harvestDate" />
              {teams.length > 0 ? (
                <CustomSelectField
                  label="Team"
                  name="teamId"
                  options={teams.map((team) => ({
                    label: team.title,
                    value: team.id,
                  }))}
                />
              ) : null}
              <div className="mt-4">
                <CustomSubmitButton disabled={isSubmitting}>
                  {editMode ? 'Update project' : 'Create project'}
                </CustomSubmitButton>
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
    </div>
  );
}
