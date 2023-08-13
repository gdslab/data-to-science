import { ArrowRightIcon } from '@heroicons/react/24/outline';

const style = 'bg-primary text-black font-bold py-2 px-4 w-full rounded';

interface Button extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  disabled?: boolean;
  icon?: string;
  size?: string;
  type?: 'button' | 'submit' | 'reset';
}

function classNames(...classes: [string, string]) {
  return classes.filter(Boolean).join(' ');
}

function getIcon(iconName: string) {
  switch (iconName) {
    case 'arrow':
      return (
        <span className="pointer-events-none absolute inset-y-0 end-0 grid w-1/4 place-content-center text-white">
          <ArrowRightIcon className="h-6 w-6" aria-hidden="true" />
        </span>
      );
    default:
      return null;
  }
}

export function Button({
  children,
  disabled = false,
  icon,
  size = 'normal',
  type = 'button',
  ...props
}: Button) {
  return (
    <div className="relative">
      <button
        className={classNames(
          size === 'sm' ? 'text-sm font-bold' : 'text-xl font-extrabold',
          'bg-accent3 text-white rounded-md p-2 w-full hover:bg-accent3-dark ease-in-out duration-300'
        )}
        type={type}
        disabled={disabled}
        {...props}
      >
        {children}
      </button>
      {icon ? getIcon(icon) : null}
    </div>
  );
}

export function OutlineButton({
  children,
  disabled = false,
  size = 'normal',
  type = 'button',
}: Button) {
  return (
    <button
      className={classNames(
        size === 'sm' ? 'text-sm font-bold' : 'text-xl font-extrabold',
        'border-2 border-accent3 text-accent3 rounded-md p-2 w-full hover:bg-accent3 hover'
      )}
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
