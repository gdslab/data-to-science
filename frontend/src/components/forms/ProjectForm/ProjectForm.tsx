import { useState } from "react";
import axios from "axios";
import { Formik, Form } from "formik";
import { useLoaderData, useNavigate } from "react-router-dom";

import CustomSelectField from "../CustomSelectField";
import CustomTextField from "../CustomTextField";

import initialValues from "./initialValues";
import validationSchema from "./validationSchema";

interface Team {
  id: string;
  title: string;
  description: string;
}

export default function ProjectForm() {
  const navigate = useNavigate();
  const teams = useLoaderData() as Team[];
  const [responseData, setResponseData] = useState(null);

  return (
    <div style={{ width: 450 }}>
      <Formik
        initialValues={initialValues}
        validationSchema={validationSchema}
        onSubmit={async (values, { setSubmitting }) => {
          try {
            const data = {
              title: values.title,
              description: values.description,
              location_id: values.locationID,
              planting_date: values.plantingDate,
              harvest_date: values.harvestDate,
              team_id: values.teamID,
            };
            const response = await axios.post("/api/v1/projects/", data, {
              headers: {
                Authorization: `Bearer ${localStorage.getItem("access_token")}`,
              },
            });
            if (response) {
              setResponseData(response.data);
              navigate("/projects");
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
        {({ isSubmitting, setFieldTouched, setFieldValue }) => (
          <fieldset>
            <legend>Create Project</legend>
            <Form>
              <CustomTextField label="Title" name="title" />
              <CustomTextField label="Description" name="description" />
              <CustomTextField label="Location" name="locationID" />
              <button
                type="button"
                style={{ marginLeft: 15 }}
                onClick={async () => {
                  try {
                    const data = {
                      name: `Field ${new Date().toString()}`,
                      geom: "SRID=4326;POLYGON((0 0,1 0,1 1,0 1,0 0))",
                    };
                    const response = await axios.post("/api/v1/locations/", data, {
                      headers: {
                        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                      },
                    });
                    if (response) {
                      setFieldValue("locationID", response.data.id);
                      setFieldTouched("locationID", true);
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
              </button>
              <CustomTextField type="date" label="Planting date" name="plantingDate" />
              <CustomTextField type="date" label="Harvest date" name="harvestDate" />
              {teams.length > 0 ? (
                <CustomSelectField
                  label="Team"
                  name="teamID"
                  options={teams.map((team) => ({
                    label: team.title,
                    value: team.id,
                  }))}
                />
              ) : null}
              <div>
                <button type="submit" disabled={isSubmitting}>
                  Create Project
                </button>
                {responseData ? (
                  <pre>{JSON.stringify(responseData, undefined, 2)}</pre>
                ) : null}
              </div>
            </Form>
          </fieldset>
        )}
      </Formik>
    </div>
  );
}
