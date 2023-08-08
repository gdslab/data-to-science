const style = 'bg-primary text-black font-bold py-2 px-4 w-full rounded';
const outlineBtnStyle = '';

interface Button {
  children: React.ReactNode;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
}

export function Button({ children, disabled = false, type = 'button' }: Button) {
  return (
    <button
      className="bg-accent3 text-white text-xl font-extrabold rounded-md p-4 w-full hover:bg-accent3-dark ease-in-out duration-300"
      type={type}
      disabled={disabled}
    >
      {children}
    </button>
  );
}

export function OutlineButton({ children, disabled = false, type = 'button' }: Button) {
  return (
    <button
      className="border-2 border-accent3 text-accent3 text-xl font-extrabold rounded-md p-4 w-full hover:bg-accent3 hover:text-white ease-in-out duration-300"
      type={type}
      disabled={disabled}
    >
      {children}
    </button>
  );
}

export function CustomButton({
  disabled = false,
  onClick,
  children,
}: {
  disabled?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
}) {
  return (
    <button className={style} type="button" disabled={disabled} onClick={onClick}>
      {children}
    </button>
  );
}

export function CustomSubmitButton({
  disabled = false,
  children,
}: {
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button className={style} type="submit" disabled={disabled}>
      {children}
    </button>
  );
}
