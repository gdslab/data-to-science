const style = 'bg-primary text-black font-bold py-2 px-4 w-full rounded';

export function CustomSubmitButton({
  disabled,
  children,
}: {
  disabled: boolean;
  children: React.ReactNode;
}) {
  return (
    <button className={style} type="submit" disabled={disabled}>
      {children}
    </button>
  );
}
