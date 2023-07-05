import { Field, ErrorMessage } from "formik";

export default function CustomSelectField({
  label,
  name,
  options,
}: {
  label: string;
  name: string;
  options: string[];
}) {
  return (
    <>
      <label htmlFor={name}>{label}:</label>
      <Field component="select" id={name} name={name}>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </Field>
      <ErrorMessage className="error" name={name} component="span" />
    </>
  );
}
