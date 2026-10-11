import { useEffect, useMemo, useRef, useState } from 'react';
import { ResponsiveBar } from '@nivo/bar';
import { ResponsiveCalendar } from '@nivo/calendar';
import { ResponsiveLine } from '@nivo/line';

import { User } from '../../../AuthContext';

const MONTH_ABBREVS = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
];

// Charts share these horizontal margins so the cumulative line and the monthly
// bars below it stay aligned on the same month positions.
const CHART_MARGIN_LEFT = 60;
const CHART_MARGIN_RIGHT = 30;

const CALENDAR_MARGIN = { top: 20, right: 40, bottom: 40, left: 40 };
// A year spans at most 53 week columns of 7 day rows.
const CALENDAR_WEEKS = 53;
const CALENDAR_DAYS = 7;

/**
 * Format a date as YYYY-MM-DD in the viewer's local time zone. Signup dates are
 * grouped by local day everywhere so the calendar and the monthly charts agree.
 */
function toLocalDay(date: Date): string {
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  return `${date.getFullYear()}-${month}-${day}`;
}

/**
 * Return count of created users by date.
 * @param users Array of users.
 * @returns Each unique creation date and a count for users created on that date.
 */
function countByDate(users: User[]): { day: string; value: number }[] {
  const dateCounts: { [key: string]: number } = {};

  users.forEach((user) => {
    const day = toLocalDay(new Date(user.created_at));
    dateCounts[day] = (dateCounts[day] || 0) + 1;
  });

  return Object.entries(dateCounts).map(([day, value]) => ({ day, value }));
}

type MonthlySignup = {
  /** Sortable YYYY-MM key. */
  key: string;
  /** Axis label, e.g. "Jan 2025". */
  label: string;
  /** Accounts created during this month. */
  count: number;
  /** Accounts created on or before the end of this month. */
  cumulative: number;
};

/**
 * Build a gap-free monthly series from the first signup through the current
 * month, carrying a running total alongside each month's new signups.
 * @param users Array of users.
 * @returns One entry per month, oldest first.
 */
function monthlySignups(users: User[]): MonthlySignup[] {
  if (users.length === 0) return [];

  const counts: { [key: string]: number } = {};
  users.forEach((user) => {
    const key = toLocalDay(new Date(user.created_at)).slice(0, 7);
    counts[key] = (counts[key] || 0) + 1;
  });

  const earliest = users.reduce(
    (oldest, user) => Math.min(oldest, new Date(user.created_at).getTime()),
    Infinity
  );

  const now = new Date();
  const start = new Date(earliest);
  const cursor = new Date(start.getFullYear(), start.getMonth(), 1);
  const end = new Date(now.getFullYear(), now.getMonth(), 1);

  const series: MonthlySignup[] = [];
  let cumulative = 0;
  while (cursor <= end) {
    const key = `${cursor.getFullYear()}-${`${cursor.getMonth() + 1}`.padStart(
      2,
      '0'
    )}`;
    cumulative += counts[key] || 0;
    series.push({
      key,
      label: `${MONTH_ABBREVS[cursor.getMonth()]} ${cursor.getFullYear()}`,
      count: counts[key] || 0,
      cumulative,
    });
    cursor.setMonth(cursor.getMonth() + 1);
  }

  return series;
}

export default function SignupCharts({ users }: { users: User[] }) {
  const series = useMemo(() => monthlySignups(users), [users]);

  // Years with at least one signup, most recent first, for the calendar picker.
  const years = useMemo(() => {
    const unique = new Set(
      users.map((user) => new Date(user.created_at).getFullYear())
    );
    return Array.from(unique).sort((a, b) => b - a);
  }, [users]);

  const [selectedYear, setSelectedYear] = useState<number | null>(
    years.length > 0 ? years[0] : null
  );

  const calendarData = useMemo(
    () =>
      selectedYear === null
        ? []
        : countByDate(users).filter((entry) =>
            entry.day.startsWith(`${selectedYear}-`)
          ),
    [users, selectedYear]
  );

  // nivo sizes calendar cells to fit both dimensions, so a fixed height leaves
  // the year short of the page width. Track the container width and give it
  // exactly the height a full-width year needs.
  const calendarRef = useRef<HTMLDivElement>(null);
  const [calendarWidth, setCalendarWidth] = useState(0);

  useEffect(() => {
    const element = calendarRef.current;
    if (!element) return;
    const observer = new ResizeObserver(([entry]) => {
      setCalendarWidth(entry.contentRect.width);
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const calendarHeight = useMemo(() => {
    const plotWidth =
      calendarWidth - CALENDAR_MARGIN.left - CALENDAR_MARGIN.right;
    if (plotWidth <= 0) return 240; // pre-measurement fallback
    const cellSize = plotWidth / CALENDAR_WEEKS;
    return Math.round(
      cellSize * CALENDAR_DAYS + CALENDAR_MARGIN.top + CALENDAR_MARGIN.bottom
    );
  }, [calendarWidth]);

  // Thin out shared x-axis labels so long histories stay readable.
  const tickValues = useMemo(() => {
    const step = Math.max(1, Math.ceil(series.length / 12));
    return series
      .filter((_, idx) => idx % step === 0)
      .map((point) => point.label);
  }, [series]);

  if (users.length === 0 || selectedYear === null) {
    return <div className="text-sm text-gray-500">No users yet</div>;
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <div className="flex flex-wrap items-center gap-3">
          <h3 className="text-base font-medium text-gray-700">
            Signup activity calendar
          </h3>
          <select
            value={selectedYear}
            onChange={(event) => setSelectedYear(Number(event.target.value))}
            aria-label="Calendar year"
            className="rounded-sm border border-gray-300 py-1 pl-2 pr-8 text-sm text-gray-700"
          >
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </div>
        <div ref={calendarRef} style={{ height: `${calendarHeight}px` }}>
          <ResponsiveCalendar
            data={calendarData}
            // Date objects rather than "YYYY-MM-DD" strings: nivo parses bare
            // date strings as UTC, which shifts the range into the previous
            // year for viewers behind UTC and renders a second, empty year row.
            from={new Date(selectedYear, 0, 1)}
            to={new Date(selectedYear, 11, 31)}
            emptyColor="#eeeeee"
            colors={['#61cdbb', '#97e3d5', '#e8c1a0', '#f47560']}
            margin={CALENDAR_MARGIN}
            monthBorderColor="#d1d5db"
            dayBorderWidth={2}
            dayBorderColor="#ffffff"
            legends={[
              {
                anchor: 'bottom-right',
                direction: 'row',
                translateY: 36,
                itemCount: 4,
                itemWidth: 42,
                itemHeight: 36,
                itemsSpacing: 14,
                itemDirection: 'right-to-left',
              },
            ]}
          />
        </div>
      </div>

      <div>
        <h3 className="text-base font-medium text-gray-700">Total accounts</h3>
        <div className="h-80">
          <ResponsiveLine
            data={[
              {
                id: 'Total accounts',
                data: series.map((point) => ({
                  x: point.label,
                  y: point.cumulative,
                })),
              },
            ]}
            margin={{
              top: 20,
              right: CHART_MARGIN_RIGHT,
              bottom: 70,
              left: CHART_MARGIN_LEFT,
            }}
            xScale={{ type: 'point' }}
            yScale={{ type: 'linear', min: 0, max: 'auto', stacked: false }}
            axisBottom={{
              tickRotation: -45,
              tickValues,
            }}
            axisLeft={{
              legend: 'Total accounts',
              legendOffset: -45,
              legendPosition: 'middle',
              format: (val) => (Math.trunc(Number(val)) === val ? val : ''),
            }}
            colors={['#2563eb']}
            pointSize={6}
            pointBorderWidth={1}
            pointBorderColor={{ from: 'serieColor' }}
            enableTouchCrosshair={true}
            useMesh={true}
          />
        </div>
      </div>

      <div>
        <h3 className="text-base font-medium text-gray-700">
          New signups per month
        </h3>
        <div className="h-72">
          <ResponsiveBar
            data={series.map((point) => ({
              month: point.label,
              signups: point.count,
            }))}
            keys={['signups']}
            indexBy="month"
            margin={{
              top: 20,
              right: CHART_MARGIN_RIGHT,
              bottom: 70,
              left: CHART_MARGIN_LEFT,
            }}
            colors={['#60a5fa']}
            enableLabel={false}
            axisBottom={{
              tickRotation: -45,
              tickValues,
            }}
            axisLeft={{
              legend: 'New signups',
              legendOffset: -45,
              legendPosition: 'middle',
              format: (val) => (Number.isInteger(Number(val)) ? `${val}` : ''),
            }}
          />
        </div>
      </div>
    </div>
  );
}
