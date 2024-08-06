import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRightIcon,
  ArrowUpOnSquareIcon,
  CursorArrowRaysIcon,
  FolderPlusIcon,
  LinkIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';

interface Button extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  icon?: string;
  size?: string;
}

interface LinkButton extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  children: React.ReactNode;
  icon?: string;
  size?: string;
  url: string;
}

interface LinkOutlineButton extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  target?: string;
  size?: string;
  url: string;
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
    case 'share2':
      return (
        <span className="pointer-events-none absolute inset-y-0 grid w-1/4 place-content-center text-white">
          <ArrowUpOnSquareIcon className="h-4 w-4" aria-hidden="true" />
        </span>
      );
    case 'trash':
      return (
        <span className="pointer-events-none absolute inset-y-0 end-0 grid w-1/4 place-content-center text-white">
          <TrashIcon className="h-4 w-4" aria-hidden="true" />
        </span>
      );
    default:
      return null;
  }
}

const getButtonSizeClassNames = (size: string) =>
  size === 'xs'
    ? 'text-xs font-semibold py-0.5 px-2'
    : size === 'sm'
    ? 'text-sm font-bold py-1.5 px-4'
    : 'text-xl font-extrabold py-2 px-4';

export function LinkOutlineButton({
  children,
  target = '_self',
  url,
  size = 'normal',
  ...props
}: LinkOutlineButton) {
  return (
    <Link to={url} target={target}>
      <button
        className={classNames(
          getButtonSizeClassNames(size),
          'w-full border-2 border-accent3 text-accent3 rounded-md py-2 px-4 w-full hover:bg-accent3 hover:text-white ease-in-out duration-300'
        )}
        type="button"
        {...props}
      >
        {children}
      </button>
    </Link>
  );
}

export function LinkButton({ children, icon, url, size = 'normal' }: LinkButton) {
  return (
    <div className="relative">
      {icon ? getIcon(icon) : null}
      <Link to={url}>
        <button
          className={classNames(
            getButtonSizeClassNames(size),
            classNames(
              icon === 'trash'
                ? 'bg-red-600 hover:bg-red-700 border-red-700 hover:border-red-800'
                : 'bg-accent3 hover:bg-accent3-dark border-accent3 hover:border-accent3-dark',
              'cursor-pointer border-2 rounded-md w-full text-center text-white ease-in-out duration-300'
            )
          )}
          type="button"
        >
          {children}
        </button>
      </Link>
    </div>
  );
}

export function Button({ children, icon, size = 'normal', ...props }: Button) {
  return (
    <div className="relative">
      {icon ? getIcon(icon) : null}
      <button
        className={classNames(
          getButtonSizeClassNames(size),
          classNames(
            props.disabled
              ? 'text-gray-400 bg-gray-200 cursor-not-allowed'
              : 'text-white ease-in-out duration-300',
            !props.disabled
              ? classNames(
                  icon === 'trash'
                    ? 'bg-red-600 hover:bg-red-700 border-red-700 hover:border-red-800'
                    : 'bg-accent3 hover:bg-accent3-dark border-accent3 hover:border-accent3-dark',
                  'border-2 rounded-md w-full'
                )
              : 'border-2 rounded-md w-full'
          )
        )}
        {...props}
      >
        {children}
      </button>
    </div>
  );
}

export function OutlineButton({ children, size = 'normal', ...props }: Button) {
  return (
    <button
      className={classNames(
        getButtonSizeClassNames(size),
        'border-2 border-accent3 text-accent3 rounded-md py-2 px-4 w-full hover:bg-accent3 hover:text-white ease-in-out duration-300'
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function LandingButton({ children, size = 'normal', ...props }: Button) {
  return (
    <button
      className={classNames(
        size === 'sm' ? 'text-sm font-bold' : 'text-xl font-extrabold',
        'border-2 border-white text-white rounded-md py-2 px-4 w-full hover:bg-accent3 hover:text-white ease-in-out duration-300'
      )}
      {...props}
    >
      {children}
    </button>
  );
}

type CopyURLButton = {
  copyText: string;
  copiedText: string;
  title?: string;
  url: string;
};
export function CopyURLButton({ copyText, copiedText, title, url }: CopyURLButton) {
  const [buttonText, setButtonText] = useState(copyText);

  return (
    <Button
      size="sm"
      onClick={() => {
        navigator.clipboard.writeText(url);
        setButtonText(copiedText);
        setTimeout(() => setButtonText(copyText), 2000);
      }}
      title={title ? title : 'Click to copy URL'}
    >
      {buttonText}
    </Button>
  );
}
