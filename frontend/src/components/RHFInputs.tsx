import { useFormContext } from 'react-hook-form';

interface Input extends React.InputHTMLAttributes<HTMLInputElement> {
  fieldName: string;
  label: string;
}

interface NumberInput extends Input {
  step: number;
}

interface RadioInput extends Input {
  inputId: string;
  value: string;
}

interface TextInput extends Input {
  placeholder?: string;
}

function CheckboxInput({ fieldName, label, ...props }: Input) {
  const {
    register,
    formState: { errors },
  } = useFormContext();

  const error = errors && errors[fieldName];

  return (
    <label htmlFor={fieldName}>
      <input
        id={fieldName}
        type="checkbox"
        {...register(fieldName)}
        {...props}
      />
      <span className="text-sm ml-2">{label}</span>
      {error && <p className="text-sm text-red-500">{`${error.message}`}</p>}
    </label>
  );
}

function NumberInput({ fieldName, label, step, ...props }: NumberInput) {
  const {
    register,
    formState: { errors },
  } = useFormContext();

  const error = errors && errors[fieldName];

  return (
    <label htmlFor={fieldName}>
      <span className="text-sm font-medium inline-block mr-2 min-w-24">
        {label}:
      </span>
      <input
        id={fieldName}
        type="number"
        step={step}
        {...register(fieldName)}
        {...props}
      />
      {error && <p className="text-sm text-red-500">{`${error.message}`}</p>}
    </label>
  );
}

function RadioInput({
  fieldName,
  inputId,
  label,
  value,
  ...props
}: RadioInput) {
  const { register } = useFormContext();

  // see https://github.com/react-hook-form/react-hook-form/issues/4604
  const customRegister = (name) => {
    const { ref, ...field } = register(name);

    const customRef = (...args: Parameters<typeof ref>) => {
      setTimeout(() => ref(...args));
    };

    return { ...field, ref: customRef };
  };

  return (
    <label htmlFor={inputId}>
      <input
        id={inputId}
        type="radio"
        value={value}
        {...customRegister(fieldName)}
        {...props}
      />
      <span className="text-sm ml-2">{label}</span>
    </label>
  );
}

function TextInput({ fieldName, label, placeholder, ...props }: TextInput) {
  const {
    register,
    formState: { errors },
  } = useFormContext();

  const error = errors && errors[fieldName];

  return (
    <label htmlFor={fieldName}>
      <span className="text-sm font-medium inline-block mr-2 min-w-24">
        {label}:
      </span>
      <input
        id={fieldName}
        type="text"
        placeholder={placeholder}
        {...register(fieldName)}
        {...props}
      />
      {error && <p className="text-sm text-red-500">{`${error.message}`}</p>}
    </label>
  );
}
export { CheckboxInput, NumberInput, RadioInput, TextInput };
