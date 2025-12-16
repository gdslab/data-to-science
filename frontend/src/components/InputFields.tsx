import {
  ErrorMessage,
  Field,
  FieldArray,
  FormikValues,
  useFormikContext,
} from 'formik';
import { CheckIcon, PencilIcon, XMarkIcon } from '@heroicons/react/24/outline';

import { Button } from './Buttons';
import { getIcon } from './utils';

const styles = {
  textField:
    'focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-hidden border border-gray-400 rounded-sm py-1 px-4 block w-full appearance-none',
  rangeField: 'w-full m-0 accent-accent2',
  selectField:
    'focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-hidden border border-gray-400 rounded-sm py-1 px-4 pr-10 block w-full',
  disabled:
    'bg-gray-200 border border-gray-400 rounded-sm py-1 px-4 block w-full appearance-none',
};

interface InputFieldLabels {
  altLabel?: boolean;
  label?: string;
}

interface InputField extends InputFieldLabels {
  children?: React.ReactNode;
  disabled?: boolean;
  name: string;
  placeholder?: string;
  required?: boolean;
  showError?: boolean;
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
}

interface NumberField extends InputField {
  max?: number;
  min?: number;
  step?: number;
}

interface RangeField extends InputField {
  max?: number;
  min?: number;
  step?: number;
  list?: string;
}

interface TextField extends InputField {
  icon?: string;
  type?: string;
}

const defaultLabelClass = 'block text-sm text-gray-400 font-bold pt-2 pb-1';
const altLabelClass = 'block font-bold pt-2 pb-1';

const InputField = ({
  children,
  altLabel,
  label,
  name,
  required,
  showError,
}: InputField) => (
  <div className="relative">
    {label ? (
      <label
        className={altLabel ? altLabelClass : defaultLabelClass}
        htmlFor={name}
      >
        {label}
        {required && !altLabel ? '*' : ''}
      </label>
    ) : null}
    {children}
    {showError ? (
      <ErrorMessage
        className="text-red-500 text-sm"
        name={name}
        component="span"
      />
    ) : null}
  </div>
);

export function NumberField({
  altLabel = false,
  disabled = false,
  label,
  max = undefined,
  min = undefined,
  name,
  required = true,
  showError = true,
  step = 1,
  onChange = undefined,
}: NumberField) {
  const { handleChange } = useFormikContext();

  return (
    <InputField
      altLabel={altLabel}
      label={label}
      name={name}
      required={required}
      showError={showError}
    >
      <Field
        className={disabled ? styles.disabled : styles.textField}
        id={name}
        name={name}
        type="number"
        disabled={disabled}
        min={min}
        max={max}
        step={step}
        onChange={onChange ? onChange : handleChange}
      />
    </InputField>
  );
}

export function RangeField({
  altLabel = false,
  disabled = false,
  label,
  max = undefined,
  min = undefined,
  name,
  required = true,
  showError = true,
  step = 1,
  list,
  onChange = undefined,
}: RangeField) {
  const { handleChange } = useFormikContext();

  return (
    <InputField
      altLabel={altLabel}
      label={label}
      name={name}
      required={required}
      showError={showError}
    >
      <Field
        className={disabled ? styles.disabled : styles.rangeField}
        id={name}
        name={name}
        type="range"
        disabled={disabled}
        min={min}
        max={max}
        step={step}
        list={list}
        onChange={onChange ? onChange : handleChange}
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
  showError = true,
  type,
}: TextField) {
  return (
    <InputField
      altLabel={altLabel}
      label={label}
      name={name}
      required={required}
      showError={showError}
    >
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

export type Editing = { field: string } | null;

interface EditField {
  children: React.ReactNode;
  fieldName: string;
  isEditing: { field: string } | null;
  setIsEditing: React.Dispatch<React.SetStateAction<Editing>>;
}

export function EditField({
  children,
  fieldName,
  isEditing,
  setIsEditing,
}: EditField) {
  return (
    <div className="flex items-center gap-8">
      <div className="block my-1 mx-0">{children}</div>
      {!isEditing ? (
        <span>
          <PencilIcon
            className="inline h-4 w-4 text-slate-400 cursor-pointer"
            onClick={(e) => {
              e.preventDefault();
              setIsEditing({ field: fieldName });
            }}
          />
        </span>
      ) : null}
      {isEditing && isEditing.field === fieldName ? (
        <div className="flex gap-4">
          <button
            type="submit"
            className="inline rounded-full focus:outline-hidden focus:ring-3 focus:ring-accent2"
          >
            <CheckIcon className="h-4 w-4 text-slate-400" />
          </button>
          <button
            type="button"
            className="inline rounded-full focus:outline-hidden focus:ring-3 focus:ring-accent2"
            onClick={() => {
              setIsEditing(null);
            }}
          >
            <XMarkIcon className="h-4 w-4 text-slate-400" />
          </button>
        </div>
      ) : null}
    </div>
  );
}

interface SelectOption {
  label: string;
  value: string | number;
}

type ColorMapSelectOption = [string, string[]][];

interface SelectField
  extends InputFieldLabels,
    React.SelectHTMLAttributes<HTMLInputElement> {
  options: SelectOption[] | ColorMapSelectOption;
}

export function SelectField({
  altLabel = false,
  disabled = false,
  label,
  name = 'select-input',
  required = true,
  options,
  ...props
}: SelectField) {
  return (
    <InputField
      altLabel={altLabel}
      label={label}
      name={name}
      required={required}
    >
      <Field
        as="select"
        className={disabled ? styles.disabled : styles.selectField}
        id={name}
        name={name}
        disabled={disabled}
        {...props}
      >
        {name === 'colorRamp'
          ? (options as ColorMapSelectOption).map((cm: [string, string[]]) => (
              <optgroup key={cm[0]} label={cm[0]}>
                {cm[1].map((cmName) => (
                  <option key={cmName} value={cmName}>
                    {cmName}
                  </option>
                ))}
              </optgroup>
            ))
          : options.map((option) => (
              <option key={option.value || 'novalue'} value={option.value}>
                {option.label}
              </option>
            ))}
      </Field>
    </InputField>
  );
}

interface TextFieldArray {
  btnLabel: string;
  name: string;
  values: FormikValues;
}

export function TextArrayField({ btnLabel, name, values }: TextFieldArray) {
  return (
    <FieldArray
      name={name}
      render={(arrayHelpers) => (
        <div className="flex flex-col items-start gap-2">
          {values[name] && values[name].length > 0 ? (
            values[name].map((_newName: string, index: number) => (
              <div key={`${name}.${index}`}>
                <div className="flex gap-4">
                  <TextField name={`${name}.${index}`} />
                  <div className="flex flex gap-4">
                    <button
                      type="button"
                      onClick={() => arrayHelpers.remove(index)}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth="1.5"
                        stroke="currentColor"
                        className="w-6 h-6"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M15 12H9m12 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
                        />
                      </svg>
                    </button>
                    <button
                      type="button"
                      onClick={() => arrayHelpers.insert(index, '')}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth="1.5"
                        stroke="currentColor"
                        className="w-6 h-6"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M12 9v6m3-3H9m12 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <Button
              type="button"
              size="sm"
              onClick={() => arrayHelpers.push('')}
            >
              {btnLabel}
            </Button>
          )}
        </div>
      )}
    ></FieldArray>
  );
}

interface SelectFieldArray {
  btnLabel: string;
  name: string;
  values: FormikValues;
  options: { label: string; value: string }[];
}

export function SelectFieldArray({
  btnLabel,
  name,
  values,
  options,
}: SelectFieldArray) {
  return (
    <FieldArray
      name={name}
      render={(arrayHelpers) => (
        <div className="flex flex-col items-start gap-2">
          {values[name] && values[name].length > 0 ? (
            values[name].map((_newName: string, index: number) => (
              <div key={`${name}.${index}`}>
                <div className="flex gap-4">
                  <SelectField name={`${name}.${index}`} options={options} />
                  <div className="flex flex gap-4">
                    <button
                      type="button"
                      onClick={() => arrayHelpers.remove(index)}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth="1.5"
                        stroke="currentColor"
                        className="w-6 h-6"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M15 12H9m12 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
                        />
                      </svg>
                    </button>
                    <button
                      type="button"
                      onClick={() => arrayHelpers.insert(index, '')}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth="1.5"
                        stroke="currentColor"
                        className="w-6 h-6"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M12 9v6m3-3H9m12 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <Button
              type="button"
              size="sm"
              onClick={() => arrayHelpers.push('')}
            >
              {btnLabel}
            </Button>
          )}
        </div>
      )}
    ></FieldArray>
  );
}
