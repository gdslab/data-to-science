import clsx from 'clsx';

interface CountBadgeProps {
  count: number;
  color: 'green' | 'sky';
  label: string;
  icon?: React.ReactNode;
  rank: 'low' | 'medium' | 'high';
}

export default function CountBadge({
  count,
  color,
  label,
  icon,
  rank,
}: CountBadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center justify-center rounded-full px-2.5 py-0.5',
        {
          // Green color scheme
          'text-green-700 bg-green-50': color === 'green' && rank === 'low',
          'text-green-700 bg-green-100': color === 'green' && rank === 'medium',
          'text-green-700 bg-green-200': color === 'green' && rank === 'high',
          // Sky color scheme
          'text-sky-700 bg-sky-50': color === 'sky' && rank === 'low',
          'text-sky-700 bg-sky-100': color === 'sky' && rank === 'medium',
          'text-sky-700 bg-sky-200': color === 'sky' && rank === 'high',
        }
      )}
    >
      {icon}
      <p className="whitespace-nowrap text-xs">
        {count} {label}
      </p>
    </span>
  );
}
