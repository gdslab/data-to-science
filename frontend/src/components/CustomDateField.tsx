import { Field, ErrorMessage } from "formik";

export default function CustomTextField({
  label,
  name,
}: {
  label: string;
  name: string;
  type?: string;
}) {
  return (
    <>
      <label htmlFor={name}>{label}:</label>
      <Field type="date" name={name} />
      <ErrorMessage className="error" name={name} component="span" />
    </>
  );
}
