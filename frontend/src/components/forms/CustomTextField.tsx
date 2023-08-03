import { Field, ErrorMessage } from 'formik';

const styles = {
  label: 'block text-sm font-bold pt-2 pb-1',
  field:
    'focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none border border-gray-400 rounded py-2 px-4 block w-full appearance-none',
  errorMsg: 'text-red-500 text-sm',
};

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
    <div>
      <label className={styles.label} htmlFor={name}>
        {label}
      </label>
      <Field
        className={styles.field}
        id={name}
        type={type ? type : 'text'}
        name={name}
      />
      <ErrorMessage className={styles.errorMsg} name={name} component="span" />
    </div>
  );
}
