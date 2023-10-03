import {
  ArrowRightIcon,
  CursorArrowRaysIcon,
  FolderPlusIcon,
  LinkIcon,
} from '@heroicons/react/24/outline';

interface Button extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  icon?: string;
  size?: string;
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
    case 'arrowRays':
      return (
        <span className="pointer-events-none absolute inset-y-0 end-0 grid w-1/4 place-content-center text-white">
          <CursorArrowRaysIcon className="h-6 w-6" aria-hidden="true" />
        </span>
      );
    case 'folderplus':
      return (
        <span className="pointer-events-none absolute inset-y-0 start-0 grid w-1/4 place-content-center text-white">
          <FolderPlusIcon className="h-6 w-6" aria-hidden="true" />
        </span>
      );
    case 'share':
      return (
        <span className="pointer-events-none absolute inset-y-0 end-0 grid w-1/4 place-content-center text-white">
          <LinkIcon className="h-4 w-4" aria-hidden="true" />
        </span>
      );
    default:
      return null;
  }
}

export function Button({ children, icon, size = 'normal', ...props }: Button) {
  return (
    <div className="relative">
      <button
        className={classNames(
          size === 'sm' ? 'text-sm font-bold' : 'text-xl font-extrabold',
          classNames(
            props.disabled
              ? 'text-slate-300 bg-slate-600'
              : 'text-white bg-accent3 hover:bg-accent3-dark ease-in-out duration-300',
            'border-2 border-accent3 hover:border-accent3-dark rounded-md py-2 px-8 w-full'
          )
        )}
        {...props}
      >
        {children}
      </button>
      {icon ? getIcon(icon) : null}
    </div>
  );
}

export function OutlineButton({ children, size = 'normal', ...props }: Button) {
  return (
    <button
      className={classNames(
        size === 'sm' ? 'text-sm font-bold' : 'text-xl font-extrabold',
        'border-2 border-accent3 text-accent3 rounded-md py-2 px-8 w-full hover:bg-accent3 hover:text-white ease-in-out duration-300'
      )}
      {...props}
    >
      {children}
    </button>
  );
}
