const style =
  'bg-gray-700 text-white font-bold py-2 px-4 w-full rounded hover:bg-gray-600';

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
