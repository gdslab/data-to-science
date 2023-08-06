import { Field, ErrorMessage } from 'formik';

const styles = {
  label: 'block text-sm font-bold pt-2 pb-1',
  field:
    'focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none border border-gray-400 rounded py-2 px-4 block w-full',
  errorMsg: 'text-red-500 text-sm',
};

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
      <label className={styles.label} htmlFor={name}>
        {label}:
      </label>
      <Field className={styles.field} component="select" id={name} name={name}>
        {options.map((option) => (
          <option key={option.value || 'novalue'} value={option.value}>
            {option.label}
          </option>
        ))}
      </Field>
      <ErrorMessage className={styles.errorMsg} name={name} component="span" />
    </>
  );
}
