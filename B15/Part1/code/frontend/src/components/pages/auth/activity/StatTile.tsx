import { ReactNode } from 'react';

export default function StatTile({
  label,
  value,
  icon,
  sub,
  tooltip,
}: {
  label: string;
  value: number;
  icon: ReactNode;
  sub?: string;
  tooltip?: string;
}) {
  return (
    <div
      className="flex flex-col gap-1 rounded-xs bg-white p-4 drop-shadow-md"
      title={tooltip}
    >
      <div className="flex min-w-0 items-center gap-1 text-[10px] font-medium uppercase text-gray-500">
        <span className="shrink-0">{icon}</span>
        <span className="truncate whitespace-nowrap">{label}</span>
      </div>
      <span className="text-3xl font-bold text-accent3">
        {value.toLocaleString()}
      </span>
      {sub ? <span className="text-xs text-gray-500">{sub}</span> : null}
    </div>
  );
}
