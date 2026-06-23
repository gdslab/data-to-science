import { ViewsTrendPoint } from './types';

/**
 * Pure CSS/flex bar chart of weekly views. The final (current) bar is tinted
 * coral; earlier bars use the light-blue secondary token. Heights are
 * normalized to the max in the series. Bar transitions are disabled when the
 * user prefers reduced motion.
 */
export default function ViewsTrend({ points }: { points: ViewsTrendPoint[] }) {
  const max = points.reduce((acc, p) => Math.max(acc, p.views), 0);

  // The backend always returns 12 zero-filled weeks, so an empty series isn't
  // possible — the meaningful empty state is "no views anywhere in the window",
  // which would otherwise render as a row of invisible zero-height bars.
  if (max === 0) {
    return (
      <p className="text-sm text-gray-500">
        No views in the last 12 weeks yet. This chart will fill in as your data
        products are viewed.
      </p>
    );
  }

  // Tick labels: show an abbreviated month under the first bar of each month.
  let lastMonth = -1;

  return (
    <div className="flex flex-col gap-1">
      <div className="flex h-32 items-end gap-1">
        {points.map((point, index) => {
          const isCurrent = index === points.length - 1;
          const heightPct = max > 0 ? (point.views / max) * 100 : 0;
          return (
            <div
              key={point.week_start}
              className="flex h-full flex-1 items-end"
              title={`Week of ${point.week_start}: ${point.views.toLocaleString()} views`}
            >
              <div
                className={`w-full rounded-t-xs transition-[height] motion-reduce:transition-none ${
                  isCurrent ? 'bg-accent2' : 'bg-secondary'
                }`}
                style={{ height: `${Math.max(heightPct, 2)}%` }}
              />
            </div>
          );
        })}
      </div>
      <div className="flex gap-1">
        {points.map((point) => {
          const month = new Date(point.week_start).getUTCMonth();
          const showTick = month !== lastMonth;
          lastMonth = month;
          return (
            <div
              key={point.week_start}
              className="flex-1 text-center text-[10px] text-gray-400"
            >
              {showTick
                ? new Date(point.week_start).toLocaleDateString(undefined, {
                    month: 'short',
                    timeZone: 'UTC',
                  })
                : ''}
            </div>
          );
        })}
      </div>
    </div>
  );
}
