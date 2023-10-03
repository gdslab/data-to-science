import { EnvelopeIcon, EyeIcon } from '@heroicons/react/24/outline';

export function classNames(...classes: [string, string]) {
  return classes.filter(Boolean).join(' ');
}

export function getIcon(iconName: string) {
  switch (iconName) {
    case 'email':
      return (
        <span className="mt-8 pointer-events-none absolute inset-y-0 end-0 grid w-10 place-content-center text-gray-500">
          <EnvelopeIcon className="h-4 w-4" aria-hidden="true" />
        </span>
      );
    case 'password':
      return (
        <span className="mt-8 pointer-events-none absolute inset-y-0 end-0 grid w-10 place-content-center text-gray-500">
          <EyeIcon className="h-4 w-4" aria-hidden="true" />
        </span>
      );
    default:
      return null;
  }
}
