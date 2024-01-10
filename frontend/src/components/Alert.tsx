import { useState } from 'react';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  FlagIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';

type AlertType = 'success' | 'info' | 'warning' | 'error';

interface AlertProps {
  alertType: AlertType;
  children: React.ReactNode;
}

export interface Status {
  type: AlertType;
  msg: string;
}

function getAlertProps(alertType: AlertType) {
  switch (alertType) {
    case 'success':
      return {
        title: 'Success',
        color: [
          'rounded border-s-4 border-green-500 bg-green-50 p-4',
          'flex items-center gap-2 text-green-800',
          'mt-2 text-sm text-green-700',
        ],
        Icon: (
          <CheckCircleIcon
            className={`block h-6 w-6 text-green-500`}
            aria-hidden="true"
          />
        ),
      };
    case 'info':
      return {
        title: 'Info',
        color: [
          'rounded border-s-4 border-sky-500 bg-sky-50 p-4',
          'flex items-center gap-2 text-sky-800',
          'mt-2 text-sm text-sky-700',
        ],
        Icon: (
          <InformationCircleIcon
            className={`block h-6 w-6 text-sky-500`}
            aria-hidden="true"
          />
        ),
      };
    case 'warning':
      return {
        title: 'Warning',
        color: [
          'rounded border-s-4 border-amber-500 bg-amber-50 p-4',
          'flex items-center gap-2 text-amber-800',
          'mt-2 text-sm text-amber-700',
        ],
        Icon: (
          <ExclamationCircleIcon
            className={`block h-6 w-6 text-amber-500`}
            aria-hidden="true"
          />
        ),
      };
    case 'error':
      return {
        title: 'Error',
        color: [
          'rounded border-s-4 border-red-500 bg-red-50 p-4',
          'flex items-center gap-2 text-red-800',
          'mt-2 text-sm text-red-700',
        ],
        Icon: (
          <ExclamationTriangleIcon
            className={`block h-6 w-6 text-red-500`}
            aria-hidden="true"
          />
        ),
      };
    default:
      return {
        title: 'Please read',
        color: [
          'rounded border-s-4 border-neutral-500 bg-neutral-50 p-4',
          'flex items-center gap-2 text-neutral-800',
          'mt-2 text-sm text-neutral-700',
        ],
        Icon: (
          <FlagIcon className={`block h-6 w-6 text-neutral-500`} aria-hidden="true" />
        ),
      };
  }
}

function getAlertBarProps(alertType: AlertType) {
  switch (alertType) {
    case 'success':
      return {
        title: 'Success',
        color: [
          'absolute bottom-4 left-4 right-4 m-auto p-4 h-16 border-s-4 border-green-500 bg-green-50',
          'h-full flex items-center justify-between text-green-500',
          'mt-2 text-sm text-green-700',
        ],
        Icon: (
          <CheckCircleIcon
            className={`block h-6 w-6 text-green-500`}
            aria-hidden="true"
          />
        ),
      };
    case 'info':
      return {
        title: 'Info',
        color: [
          'absolute bottom-4 left-4 right-4 m-auto p-4 h-16 border-s-4 border-sky-500 bg-sky-50',
          'h-full flex items-center justify-between text-sky-500',
          'mt-2 text-sm text-sky-700',
        ],
        Icon: (
          <InformationCircleIcon
            className={`block h-6 w-6 text-sky-500`}
            aria-hidden="true"
          />
        ),
      };
    case 'warning':
      return {
        title: 'Warning',
        color: [
          'absolute bottom-4 left-4 right-4 m-auto p-4 h-16 border-s-4 border-amber-500 bg-amber-50',
          'h-full flex items-center justify-between text-amber-500',
          'mt-2 text-sm text-amber-700',
        ],
        Icon: (
          <ExclamationCircleIcon
            className={`block h-6 w-6 text-amber-500`}
            aria-hidden="true"
          />
        ),
      };
    case 'error':
      return {
        title: 'Error',
        color: [
          'absolute bottom-4 left-4 right-4 m-auto p-4 h-16 border-s-4 border-red-500 bg-red-50',
          'h-full flex items-center justify-between text-red-500',
          'mt-2 text-sm text-red-700',
        ],
        Icon: (
          <ExclamationTriangleIcon
            className={`block h-6 w-6 text-red-500`}
            aria-hidden="true"
          />
        ),
      };
    default:
      return {
        title: 'Please read',
        color: [
          'absolute bottom-4 left-4 right-4 m-auto p-4 h-16 border-s-4 border-neutral-500 bg-neutral-50',
          'h-full flex items-center justify-between text-neutral-500',
          'mt-2 text-sm text-neutral-700',
        ],
        Icon: (
          <FlagIcon className={`block h-6 w-6 text-neutral-500`} aria-hidden="true" />
        ),
      };
  }
}

export default function Alert({ alertType, children }: AlertProps) {
  const { color, Icon, title } = getAlertProps(alertType);
  return (
    <div role="alert" className={color[0]}>
      <div className={color[1]}>
        {Icon}
        <strong className="block font-medium"> {title} </strong>
      </div>

      <p className={color[2]}>{children}</p>
    </div>
  );
}

export function AlertBar({ alertType, children }: AlertProps) {
  const [hide, toggleHide] = useState(false);
  const { color, Icon } = getAlertBarProps(alertType);

  if (hide) {
    return null;
  } else {
    return (
      <div role="alert" className={color[0]} style={{ zIndex: 1000 }}>
        <div className={color[1]}>
          <div className="flex flex-cols gap-4 items-center">
            {Icon}
            <span>{children}</span>
          </div>
          <div className="flex">
            <button className="transition" onClick={() => toggleHide(true)}>
              <span className="sr-only">Dismiss popup</span>

              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
                className="h-6 w-6"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    );
  }
}
