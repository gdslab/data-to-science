import { useFormContext } from 'react-hook-form';

interface Input extends React.InputHTMLAttributes<HTMLInputElement> {
  fieldName: string;
  inputId: string;
  label: string;
}

interface NumberInput extends Input {
  step: number;
}

interface RadioInput extends Input {
  value: string;
}

function CheckboxInput({ fieldName, inputId, label, ...props }: Input) {
  const {
    register,
    formState: { errors },
  } = useFormContext();
  return (
    <label htmlFor={inputId}>
      <input id={inputId} type="checkbox" {...register(fieldName)} {...props} />
      <span className="text-sm ml-2">{label}</span>
      {errors && errors[fieldName] && typeof errors[fieldName].message === 'string' && (
        <p className="text-sm text-red-500">{errors[fieldName].message}</p>
      )}
    </label>
  );
}

function NumberInput({ fieldName, inputId, label, step, ...props }: NumberInput) {
  const {
    register,
    formState: { errors },
  } = useFormContext();
  return (
    <label htmlFor={inputId}>
      <span className="text-sm font-medium inline-block mr-2 w-24">{label}:</span>
      <input
        id={inputId}
        type="number"
        step={step}
        {...register(fieldName)}
        {...props}
      />
      {errors && errors[fieldName] && typeof errors[fieldName].message === 'string' && (
        <p className="text-sm text-red-500">{errors[fieldName].message}</p>
      )}
    </label>
  );
}

function RadioInput({ fieldName, inputId, label, value, ...props }: RadioInput) {
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

export { CheckboxInput, NumberInput, RadioInput };
