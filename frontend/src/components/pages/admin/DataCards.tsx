import { ReactNode } from 'react';

/**
 * Stacked card used below `md` in place of a table row. Mirrors the engagement
 * leaderboard cards in DashboardActivity so every admin list reads the same.
 */
export function DataCard({
  leading,
  title,
  subtitle,
  trailing,
  children,
}: {
  leading?: ReactNode;
  title: ReactNode;
  subtitle?: ReactNode;
  trailing?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <div className="rounded-sm bg-slate-100 p-3 text-left">
      <div className="flex items-center gap-2">
        {leading}
        <div className="min-w-0 flex-1">
          <div className="truncate font-medium">{title}</div>
          {subtitle && (
            <div className="truncate text-sm text-gray-500">{subtitle}</div>
          )}
        </div>
        {trailing}
      </div>
      {children}
    </div>
  );
}

export function MetricTileGrid({ children }: { children: ReactNode }) {
  return <div className="mt-3 grid grid-cols-2 gap-1">{children}</div>;
}

export function MetricTile({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: ReactNode;
  highlight?: boolean;
}) {
  return (
    <div
      className={
        highlight
          ? 'rounded-sm bg-blue-50 p-2 text-blue-700'
          : 'rounded-sm bg-slate-50 p-2'
      }
    >
      <div className="text-xs text-gray-500">{label}</div>
      <div className={highlight ? 'font-semibold' : undefined}>{value}</div>
    </div>
  );
}
