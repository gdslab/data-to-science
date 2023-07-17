import { Field, ErrorMessage } from "formik";

export default function CustomTextField({
  label,
  name,
  type,
}: {
  label: string;
  name: string;
  type?: string;
}) {
  return (
    <>
      <label htmlFor={name}>{label}:</label>
      <Field id={name} type={type ? type : "text"} name={name} />
      <ErrorMessage className="error" name={name} component="span" />
    </>
  );
}
