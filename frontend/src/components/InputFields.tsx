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
  altLabel?: boolean;
  children?: React.ReactNode;
  disabled?: boolean;
  label: string;
  name: string;
  placeholder?: string;
  required?: boolean;
}

interface NumberField extends InputField {
  max: number;
  min: number;
  step?: number;
}

interface TextField extends InputField {
  icon?: string;
  type?: string;
}

const defaultLabelClass = 'block text-sm text-gray-400 font-bold pt-2 pb-1';
const altLabelClass = 'block font-bold pt-2 pb-1';

const InputField = ({ children, altLabel, label, name, required }: InputField) => (
  <div className="relative">
    <label className={altLabel ? altLabelClass : defaultLabelClass} htmlFor={name}>
      {label}
      {required && !altLabel ? '*' : ''}
    </label>
    {children}
    <ErrorMessage className="text-red-500 text-sm" name={name} component="span" />
  </div>
);

export function NumberField({
  altLabel = false,
  disabled = false,
  label,
  max,
  min,
  name,
  required = true,
  step = 1,
}: NumberField) {
  return (
    <InputField altLabel={altLabel} label={label} name={name} required={required}>
      <Field
        className={disabled ? styles.disabled : styles.textField}
        id={name}
        name={name}
        type="number"
        disabled={disabled}
        min={min}
        max={max}
        step={step}
      />
    </InputField>
  );
}

export function TextField({
  altLabel = false,
  disabled = false,
  icon,
  label,
  name,
  placeholder = '',
  required = true,
  type,
}: TextField) {
  return (
    <InputField altLabel={altLabel} label={label} name={name} required={required}>
      <Field
        as={type === 'textarea' ? 'textarea' : null}
        className={disabled ? styles.disabled : styles.textField}
        id={name}
        type={type ? type : 'text'}
        name={name}
        disabled={disabled}
        rows={type === 'textarea' ? 4 : 1}
        placeholder={placeholder}
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
  altLabel = false,
  disabled = false,
  label,
  name,
  required = true,
  options,
}: SelectField) {
  return (
    <InputField altLabel={altLabel} label={label} name={name} required={required}>
      <Field
        as="select"
        className={disabled ? styles.disabled : styles.selectField}
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
