import { Field, ErrorMessage } from 'formik';

const styles = {
  label: 'block text-sm text-gray-400 font-bold pt-2 pb-1',
  field:
    'focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none bg-white border border-gray-400 rounded py-1 px-4 block w-full',
  disabled:
    'bg-gray-200 border border-gray-400 rounded py-1 px-4 block w-full appearance-none',
  errorMsg: 'text-red-500 text-sm',
};

interface Option {
  label: string;
  value: string;
}

export default function CustomSelectField({
  disabled = false,
  label,
  name,
  options,
}: {
  disabled?: boolean;
  label: string;
  name: string;
  options: Option[];
}) {
  return (
    <div>
      <div className="relative">
        <label className={styles.label} htmlFor={name}>
          {label}:
        </label>
        <Field
          className={disabled ? styles.disabled : styles.field}
          component="select"
          id={name}
          name={name}
          disabled={disabled}
        >
          {options.map((option) => (
            <option key={option.value || 'novalue'} value={option.value}>
              {option.label}
            </option>
          ))}
        </Field>
      </div>
      <ErrorMessage className={styles.errorMsg} name={name} component="span" />
    </div>
  );
}
