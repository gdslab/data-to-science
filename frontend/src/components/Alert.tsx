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

function getAlertProps(alertType: AlertType) {
  switch (alertType) {
    case 'success':
      return {
        title: 'Request completed',
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
        title: 'More details',
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
        title: 'Something unexpected happened',
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
        title: 'Something went wrong',
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
