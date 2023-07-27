import axios from "axios";
import { Formik, Form } from "formik";

import CustomTextField from "../CustomTextField";

import initialValues from "./initialValues";
import validationSchema from "./validationSchema";

export default function RegistrationForm() {
  return (
    <div style={{ width: 450 }}>
      <Formik
        initialValues={initialValues}
        validationSchema={validationSchema}
        onSubmit={async (values, { setSubmitting, setStatus }) => {
          try {
            const data = {
              first_name: values.firstName,
              last_name: values.lastName,
              email: values.email,
              password: values.password,
            };
            const response = await axios.post("/api/v1/users/", data);
            if (response) {
              // do something
            } else {
              // do something
            }
          } catch (err) {
            if (axios.isAxiosError(err)) {
              console.error(err);
              setStatus(err.response?.data.detail);
            } else {
              // do something
            }
          }
          setSubmitting(false);
        }}
      >
        {({ values, isSubmitting, status }) => (
          <fieldset>
            <legend>Registration</legend>
            <Form>
              <CustomTextField label="First name" name="firstName" />
              <CustomTextField label="Last name" name="lastName" />
              <CustomTextField label="Email" name="email" type="email" />
              <CustomTextField label="Password" name="password" type="password" />
              {values.password.length > 0 ? (
                <CustomTextField
                  label="Retype password"
                  name="passwordRetype"
                  type="password"
                />
              ) : null}
              <p>
                New accounts will require email confirmation and manual approval before
                use.
              </p>
              <div>
                <button type="submit" disabled={isSubmitting}>
                  Register
                </button>
              </div>
              {status ? (
                <div style={{ marginTop: 15 }}>
                  <span style={{ color: "red" }}>{status}</span>
                </div>
              ) : null}
            </Form>
          </fieldset>
        )}
      </Formik>
    </div>
  );
}
