const style = 'bg-primary text-black font-bold py-2 px-4 w-full rounded';

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
