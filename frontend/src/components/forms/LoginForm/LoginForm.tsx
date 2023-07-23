import { useState } from "react";
import axios from "axios";
import { Formik, Form } from "formik";
import { redirect } from "react-router-dom";

import CustomTextField from "../CustomTextField";

import initialValues from "./initialValues";
import validationSchema from "./validationSchema";

export default function LoginForm() {
  const [responseData, setResponseData] = useState(null);

  return (
    <div style={{ width: 450 }}>
      <Formik
        initialValues={initialValues}
        validationSchema={validationSchema}
        onSubmit={async (values, { setSubmitting, setStatus }) => {
          setStatus("");
          try {
            const data = {
              username: values.email,
              password: values.password,
            };
            const response = await axios.post("/api/v1/auth/access-token", data, {
              headers: { "Content-Type": "application/x-www-form-urlencoded" },
            });
            if (response) {
              setResponseData(response.data);
              localStorage.setItem("access_token", response.data.access_token);
              redirect("/");
            } else {
              // do something
            }
          } catch (err) {
            if (axios.isAxiosError(err)) {
              console.error(err.response?.data.detail);
              setStatus(err.response?.data.detail);
            } else {
              // do something
            }
          }
          setSubmitting(false);
        }}
      >
        {({ isSubmitting, status }) => (
          <fieldset>
            <legend>Login</legend>
            <Form>
              <CustomTextField label="Email" name="email" type="email" />
              <CustomTextField label="Password" name="password" type="password" />
              <div>
                <button type="submit" disabled={isSubmitting}>
                  Login
                </button>
              </div>
              {status ? (
                <div style={{ marginTop: 15 }}>
                  <span style={{ color: "red" }}>{status}</span>
                </div>
              ) : null}
              {responseData ? (
                <pre>{JSON.stringify(responseData, undefined, 2)}</pre>
              ) : null}
            </Form>
          </fieldset>
        )}
      </Formik>
    </div>
  );
}
