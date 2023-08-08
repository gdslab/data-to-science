import { Field, ErrorMessage } from 'formik';
import { EnvelopeIcon, EyeIcon } from '@heroicons/react/24/outline';

const styles = {
  label: 'block text-sm text-gray-400 font-bold pt-2 pb-1',
  field:
    'focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none border border-gray-400 rounded py-1 px-4 block w-full appearance-none',
  errorMsg: 'text-red-500 text-sm',
};

function getIcon(iconName: string) {
  switch (iconName) {
    case 'email':
      return (
        <span className="mt-8 pointer-events-none absolute inset-y-0 end-0 grid w-10 place-content-center text-gray-500">
          <EnvelopeIcon className="h-4 w-4" aria-hidden="true" />
        </span>
      );
    case 'password':
      return (
        <span className="mt-8 pointer-events-none absolute inset-y-0 end-0 grid w-10 place-content-center text-gray-500">
          <EyeIcon className="h-4 w-4" aria-hidden="true" />
        </span>
      );
    default:
      return null;
  }
}

export default function CustomTextField({
  icon,
  label,
  name,
  required = true,
  type,
}: {
  icon?: string;
  label: string;
  name: string;
  required?: boolean;
  type?: string;
}) {
  return (
    <div>
      <div className="relative">
        <label className={styles.label} htmlFor={name}>
          {label}
          {required ? '*' : ''}
        </label>
        <Field
          className={styles.field}
          id={name}
          type={type ? type : 'text'}
          name={name}
        />
        {icon ? getIcon(icon) : null}
      </div>
      <ErrorMessage className={styles.errorMsg} name={name} component="span" />
    </div>
  );
}
