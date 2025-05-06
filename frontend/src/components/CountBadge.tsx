import clsx from 'clsx';

interface CountBadgeProps {
  count: number;
  color: 'green' | 'sky';
  label: string;
  icon?: React.ReactNode;
}

export default function CountBadge({
  count,
  color,
  label,
  icon,
}: CountBadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center justify-center rounded-full px-2.5 py-0.5',
        {
          // Green color scheme
          'text-green-700 bg-green-50': color === 'green' && count === 0,
          'text-green-700 bg-green-100':
            color === 'green' && count > 0 && count < 5,
          'text-green-700 bg-green-200': color === 'green' && count > 4,
          // Sky color scheme
          'text-sky-700 bg-sky-50': color === 'sky' && count === 0,
          'text-sky-700 bg-sky-100': color === 'sky' && count > 0 && count < 5,
          'text-sky-700 bg-sky-200': color === 'sky' && count > 4,
        }
      )}
    >
      {icon}
      <p className="whitespace-nowrap text-sm">
        {count} {label}
      </p>
    </span>
  );
}
