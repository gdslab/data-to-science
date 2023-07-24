import { useState } from "react";
import axios from "axios";
import { Formik, Form } from "formik";
import { useNavigate } from "react-router-dom";

import CustomTextField from "../CustomTextField";

import initialValues from "./initialValues";
import validationSchema from "./validationSchema";

export default function TeamForm() {
  const navigate = useNavigate();
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
            };
            const response = await axios.post("/api/v1/teams/", data, {
              headers: {
                Authorization: `Bearer ${localStorage.getItem("access_token")}`,
              },
            });
            if (response) {
              setResponseData(response.data);
              navigate("/teams");
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
            <legend>Create Team</legend>
            <Form>
              <CustomTextField label="Title" name="title" />
              <CustomTextField label="Description" name="description" />
              <div>
                <button type="submit" disabled={isSubmitting}>
                  Create Team
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
