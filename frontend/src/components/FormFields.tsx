import ConnectForm from './ConnectForm';

const styles = {
  error: 'mt-1 text-red-500 text-sm',
  label: 'block text-sm text-gray-400 font-bold pt-2 pb-1',
  inputText:
    'focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none border border-gray-400 rounded py-1 px-4 block w-full appearance-none',
  inputTextArea: 'w-full h-48 resize-none rounded',
};

type InputField = {
  label: string;
  name: string;
  required?: boolean;
  type?: string;
};

export function InputField({
  label,
  name,
  required = true,
  type = 'text',
}: InputField) {
  return (
    <ConnectForm>
      {({ formState: { errors }, register }) => (
        <div>
          <label className={styles.label}>
            {label}
            {required && '*'}
          </label>
          <input
            className={styles.inputText}
            type={type}
            {...register(name)}
            aria-invalid={errors[name] ? 'true' : 'false'}
          />
          {errors[name] && (
            <p role="alert" className={styles.error}>
              {errors[name].message}
            </p>
          )}
        </div>
      )}
    </ConnectForm>
  );
}

export function TextAreaField({ label, name, required = true }: InputField) {
  return (
    <ConnectForm>
      {({ formState: { errors }, register }) => (
        <div>
          <label className={styles.label}>
            {label}
            {required && '*'}
          </label>
          <textarea
            className={styles.inputTextArea}
            {...register(name)}
            aria-invalid={errors[name] ? 'true' : 'false'}
          />
          {errors[name] && (
            <p role="alert" className={styles.error}>
              {errors[name].message}
            </p>
          )}
        </div>
      )}
    </ConnectForm>
  );
}
