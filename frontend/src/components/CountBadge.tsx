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
          [`text-${color}-700`]: true,
          [`bg-${color}-50`]: count === 0,
          [`bg-${color}-100`]: count > 0 && count < 5,
          [`bg-${color}-200`]: count > 4,
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
