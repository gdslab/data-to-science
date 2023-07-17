import { useState } from "react";
import axios from "axios";
import { Formik, Form } from "formik";

import CustomTextField from "../CustomTextField";

import initialValues from "./initialValues";
import validationSchema from "./validationSchema";

export default function ProjectForm() {
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
              location: values.location,
              planting_date: values.plantingDate,
              harvest_date: values.harvestDate,
            };
            const response = await axios.post("/api/v1/projects/", data, {
              headers: {
                Authorization: `Bearer ${localStorage.getItem("access_token")}`,
              },
            });
            if (response) {
              setResponseData(response.data);
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
        {({ isSubmitting }) => (
          <fieldset>
            <legend>Create Project</legend>
            <Form>
              <CustomTextField label="Title" name="title" />
              <CustomTextField label="Description" name="description" />
              <CustomTextField type="date" label="Planting date" name="plantingDate" />
              <CustomTextField type="date" label="Harvest date" name="harvestDate" />
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
