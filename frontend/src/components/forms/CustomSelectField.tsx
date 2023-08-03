import { Field, ErrorMessage } from 'formik';

interface Option {
  label: string;
  value: string;
}

export default function CustomSelectField({
  label,
  name,
  options,
}: {
  label: string;
  name: string;
  options: Option[];
}) {
  return (
    <>
      <label htmlFor={name}>{label}:</label>
      <Field component="select" id={name} name={name}>
        {options.map((option) => (
          <option key={option.value || 'novalue'} value={option.value}>
            {option.label}
          </option>
        ))}
      </Field>
      <ErrorMessage className="error" name={name} component="span" />
    </>
  );
}
