import {
  ClockIcon,
  CogIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

const ErrorIcon = () => (
  <div>
    <span className="sr-only">Failed</span>
    <ExclamationTriangleIcon
      className="h-5 w-5 text-red-600"
      title="Processing of uploaded raw data failed"
    />
  </div>
);

const PendingIcon = () => (
  <div>
    <span className="sr-only">Pending</span>
    <ClockIcon
      className="h-5 w-5"
      title="Waiting for processing of uploaded raw data to begin"
    />
  </div>
);

const ProgressIcon = () => (
  <div>
    <span className="sr-only">Processing</span>
    <CogIcon className="h-5 w-5 animate-spin" title="Processing uploaded raw data" />
  </div>
);

export { ErrorIcon, ProgressIcon, PendingIcon };
