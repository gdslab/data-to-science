import { Field, ErrorMessage } from 'formik';

import { getIcon } from './utils';

const styles = {
  textField:
    'focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none border border-gray-400 rounded py-1 px-4 block w-full appearance-none',
  selectField:
    'focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none border border-gray-400 rounded py-1 px-4 block w-full',
  disabled:
    'bg-gray-200 border border-gray-400 rounded py-1 px-4 block w-full appearance-none',
};

interface InputField {
  children?: React.ReactNode;
  disabled?: boolean;
  label: string;
  name: string;
  required?: boolean;
}

interface TextField extends InputField {
  icon?: string;
  type?: string;
}

const InputField = ({ children, label, name, required }: InputField) => (
  <div className="relative">
    <label className="block text-sm text-gray-400 font-bold pt-2 pb-1" htmlFor={name}>
      {label}
      {required ? '*' : ''}
    </label>
    {children}
    <ErrorMessage className="text-red-500 text-sm" name={name} component="span" />
  </div>
);

export function TextField({
  disabled = false,
  icon,
  label,
  name,
  required = true,
  type,
}: TextField) {
  return (
    <InputField label={label} name={name} required={required}>
      <Field
        className={disabled ? styles.disabled : styles.textField}
        id={name}
        type={type ? type : 'text'}
        name={name}
        disabled={disabled}
      />
      {icon ? getIcon(icon) : null}
    </InputField>
  );
}

interface SelectOption {
  label: string;
  value: string;
}

interface SelectField extends InputField {
  options: SelectOption[];
}

export function SelectField({
  disabled = false,
  label,
  name,
  required = true,
  options,
}: SelectField) {
  return (
    <InputField label={label} name={name} required={required}>
      <Field
        className={disabled ? styles.disabled : styles.selectField}
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
    </InputField>
  );
}
