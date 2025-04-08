import { Form, Formik } from 'formik';
import { useState } from 'react';
import { useRevalidator } from 'react-router-dom';

import api from '../../../api';
import { EditField, Editing, TextField } from '../../InputFields';

import validationSchema from './validationSchema';
import { TeamData } from './TeamDetail';

type TeamEditFormProps = {
  teamData: TeamData;
};

export default function TeamEditForm({ teamData }: TeamEditFormProps) {
  const revalidator = useRevalidator();

  const [isEditing, setIsEditing] = useState<Editing>(null);

  return (
    <Formik
      initialValues={{
        title: teamData.team.title,
        description: teamData.team.description,
      }}
      validationSchema={validationSchema}
      onSubmit={async (values) => {
        try {
          const response = await api.put(`/teams/${teamData.team.id}`, values);
          if (response) {
            revalidator.revalidate();
          }
          setIsEditing(null);
        } catch (err) {
          setIsEditing(null);
        }
      }}
    >
      {() => (
        <Form>
          <div className="grid rows-auto gap-2">
            <EditField
              fieldName="title"
              isEditing={isEditing}
              setIsEditing={setIsEditing}
            >
              {!isEditing || isEditing.field !== 'title' ? (
                <h2 className="mb-0">{teamData.team.title}</h2>
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
                <span className="text-gray-600">
                  {teamData.team.description}
                </span>
              ) : (
                <TextField name="description" />
              )}
            </EditField>
          </div>
        </Form>
      )}
    </Formik>
  );
}
