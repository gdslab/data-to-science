import { useEffect, useMemo, useState } from 'react';
import { useLoaderData } from 'react-router';
import { ResponsiveLine } from '@nivo/line';
import { FaCircleInfo, FaXmark } from 'react-icons/fa6';

import {
  ActivitySummary,
  ActivityTrendPoint,
  EngagementLeaderRow,
  LeaderboardMetric,
} from './DashboardTypes';
import StatCard from './StatCard';
import Modal from '../../Modal';
import Pagination from '../../Pagination';

import api from '../../../api';

const MAX_ITEMS = 10; // leaderboard rows per page
const LEADERBOARD_LIMIT = 50;

const METRIC_OPTIONS: { value: LeaderboardMetric; label: string }[] = [
  { value: 'data_products', label: 'Data products' },
  { value: 'projects', label: 'Projects' },
  { value: 'flights', label: 'Flights' },
  { value: 'views', label: 'Views' },
  { value: 'likes', label: 'Likes' },
  { value: 'storage', label: 'Data usage' },
];

// Maps the selected metric to the leaderboard row field it ranks on, so the
// matching table column can be highlighted.
const METRIC_TO_FIELD: Record<LeaderboardMetric, keyof EngagementLeaderRow> = {
  projects: 'project_count',
  flights: 'flight_count',
  data_products: 'data_product_count',
  views: 'total_views',
  likes: 'total_likes',
  storage: 'total_storage',
};

function bytesToGB(bytes: number): string {
  return (bytes / 1024 ** 3).toFixed(2);
}

type InfoKey = 'active' | 'trend' | 'funnel' | 'leaderboard';

// Per-section explanations surfaced through the info icon next to each heading.
const SECTION_INFO: Record<InfoKey, { title: string; body: React.ReactNode }> =
  {
    active: {
      title: 'Active users',
      body: (
        <>
          <p>
            <strong>Active (24h / 7d / 30d)</strong> count the distinct users
            who performed any authenticated action within the trailing window,
            based on each user's most recent activity. These are the daily,
            weekly, and monthly active user (DAU / WAU / MAU) totals as of now.
          </p>
          <p>
            <strong>Active users</strong> is the total number of approved and
            email-confirmed accounts — your activated user base.
          </p>
        </>
      ),
    },
    trend: {
      title: 'Active users over time (DAU / WAU / MAU)',
      body: (
        <>
          <p>
            Daily, weekly, and monthly active-user counts recorded once per day.
            Because only each user's most recent activity is stored, this
            history builds going forward from when daily snapshots began and
            cannot be backfilled.
          </p>
          <p>
            <strong>Stickiness (DAU/MAU)</strong> is the share of monthly-active
            users who were also active in the last 24 hours — higher means users
            return more often.
          </p>
        </>
      ),
    },
    funnel: {
      title: 'Activation funnel',
      body: (
        <>
          <p>
            Shows how far new users progress: signed up → confirmed email →
            approved by an admin → created their first project.
          </p>
          <p>
            Each stage is a subset of the one before it, so the drop-off between
            bars highlights where users stall.
          </p>
        </>
      ),
    },
    leaderboard: {
      title: 'Engagement leaderboard (power users)',
      body: (
        <>
          <p>
            Ranks users by the content they created (projects, flights, data
            products), the engagement their data products received (views,
            likes), or their data usage. Use the <strong>Rank by</strong>{' '}
            buttons to change the metric.
          </p>
          <p>
            All totals are credited to the project owner. Data usage sums stored
            data product and raw data file sizes; vector layers are not
            included.
          </p>
        </>
      ),
    },
  };

function SectionHeading({
  infoKey,
  onInfo,
  className = 'mb-4',
}: {
  infoKey: InfoKey;
  onInfo: (key: InfoKey) => void;
  className?: string;
}) {
  const { title } = SECTION_INFO[infoKey];
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <h2 className="text-xl font-semibold">{title}</h2>
      <button
        type="button"
        onClick={() => onInfo(infoKey)}
        aria-label={`About ${title}`}
        className="text-gray-400 hover:text-blue-600"
      >
        <FaCircleInfo className="h-4 w-4" />
      </button>
    </div>
  );
}

function SectionInfoModal({
  activeInfo,
  onClose,
}: {
  activeInfo: InfoKey | null;
  onClose: () => void;
}) {
  // Adapt the shared Modal's boolean setter to clearing the active section.
  const setOpen: React.Dispatch<React.SetStateAction<boolean>> = (value) => {
    const next =
      typeof value === 'function' ? value(activeInfo !== null) : value;
    if (!next) onClose();
  };

  return (
    <Modal open={activeInfo !== null} setOpen={setOpen}>
      {activeInfo && (
        <div className="p-6">
          <div className="flex items-start justify-between gap-4">
            <h3 className="text-lg font-semibold text-gray-900">
              {SECTION_INFO[activeInfo].title}
            </h3>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close"
              className="text-gray-400 hover:text-gray-600"
            >
              <FaXmark className="h-5 w-5" />
            </button>
          </div>
          <div className="mt-3 space-y-2 text-sm text-gray-600">
            {SECTION_INFO[activeInfo].body}
          </div>
        </div>
      )}
    </Modal>
  );
}

type ActivityLoaderData = {
  summary: ActivitySummary;
  trends: ActivityTrendPoint[];
  leaderboard: EngagementLeaderRow[];
};

export async function loader(): Promise<ActivityLoaderData> {
  const [summaryRes, trendsRes, leaderboardRes] = await Promise.all([
    api.get('/admin/activity/summary'),
    api.get('/admin/activity/trends?days=90'),
    api.get(
      `/admin/activity/leaderboard?metric=data_products&limit=${LEADERBOARD_LIMIT}`,
    ),
  ]);

  return {
    summary: summaryRes.data,
    trends: trendsRes.data,
    leaderboard: leaderboardRes.data,
  };
}

function ActiveUserCards({ summary }: { summary: ActivitySummary }) {
  return (
    <div className="flex flex-row flex-wrap gap-4">
      <StatCard
        title="Active (24h)"
        value={summary.active_24h}
        subtitle="DAU"
      />
      <StatCard title="Active (7d)" value={summary.active_7d} subtitle="WAU" />
      <StatCard
        title="Active (30d)"
        value={summary.active_30d}
        subtitle="MAU"
      />
      <StatCard
        title="Active users"
        value={summary.total_users}
        subtitle="Approved & confirmed"
      />
    </div>
  );
}

function ActivationFunnel({ summary }: { summary: ActivitySummary }) {
  const { funnel } = summary;
  const stages = [
    { label: 'Signed up', value: funnel.signed_up },
    { label: 'Email confirmed', value: funnel.email_confirmed },
    { label: 'Approved', value: funnel.approved },
    { label: 'Created a project', value: funnel.created_project },
  ];
  const maxValue = funnel.signed_up || 1;

  return (
    <div className="flex flex-col gap-2">
      {stages.map((stage) => {
        const pct = Math.round((stage.value / maxValue) * 100);
        return (
          <div key={stage.label} className="flex items-center gap-3">
            <span className="w-40 shrink-0 text-sm font-medium text-gray-600">
              {stage.label}
            </span>
            <div className="relative h-6 flex-1 rounded-sm bg-gray-100">
              <div
                className="flex h-6 items-center justify-end rounded-sm bg-blue-600 px-2 text-xs font-medium text-white"
                style={{ width: `${Math.max(pct, 4)}%` }}
              >
                {stage.value}
              </div>
            </div>
            <span className="w-12 shrink-0 text-right text-sm text-gray-500">
              {pct}%
            </span>
          </div>
        );
      })}
    </div>
  );
}

function ActiveUsersTrend({ trends }: { trends: ActivityTrendPoint[] }) {
  if (trends.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-center text-sm text-gray-500">
        Active-user trends will appear here once daily snapshots have been
        recorded (history begins the day the snapshot job is deployed).
      </div>
    );
  }

  const data = [
    {
      id: 'MAU (30d)',
      data: trends.map((t) => ({ x: t.snapshot_date, y: t.active_30d })),
    },
    {
      id: 'WAU (7d)',
      data: trends.map((t) => ({ x: t.snapshot_date, y: t.active_7d })),
    },
    {
      id: 'DAU (24h)',
      data: trends.map((t) => ({ x: t.snapshot_date, y: t.active_24h })),
    },
  ];

  // Thin out the x-axis ticks so dense windows stay readable.
  const step = Math.max(1, Math.ceil(trends.length / 8));
  const tickValues = trends
    .filter((_, idx) => idx % step === 0)
    .map((t) => t.snapshot_date);

  return (
    <ResponsiveLine
      data={data}
      margin={{ top: 20, right: 120, bottom: 70, left: 60 }}
      xScale={{ type: 'point' }}
      yScale={{ type: 'linear', min: 0, max: 'auto', stacked: false }}
      axisBottom={{
        tickRotation: -45,
        tickValues,
        legend: 'Date',
        legendOffset: 56,
        legendPosition: 'middle',
      }}
      axisLeft={{
        legend: 'Active users',
        legendOffset: -45,
        legendPosition: 'middle',
        format: (val) => (Math.trunc(Number(val)) === val ? val : ''),
      }}
      colors={{ scheme: 'category10' }}
      pointSize={6}
      pointBorderWidth={1}
      pointBorderColor={{ from: 'serieColor' }}
      useMesh={true}
      enableTouchCrosshair={true}
      legends={[
        {
          anchor: 'bottom-right',
          direction: 'column',
          translateX: 110,
          itemWidth: 90,
          itemHeight: 20,
          symbolSize: 12,
          symbolShape: 'circle',
        },
      ]}
    />
  );
}

function EngagementLeaderboard({
  rows,
  metric,
  onMetricChange,
}: {
  rows: EngagementLeaderRow[];
  metric: LeaderboardMetric;
  onMetricChange: (metric: LeaderboardMetric) => void;
}) {
  const [currentPage, setCurrentPage] = useState(0);
  const totalPages = Math.ceil(rows.length / MAX_ITEMS);
  const activeField = METRIC_TO_FIELD[metric];

  // Reset to the first page whenever the ranked metric (and row order) changes.
  useEffect(() => {
    setCurrentPage(0);
  }, [metric]);

  function updateCurrentPage(newPage: number): void {
    if (newPage + 1 > totalPages) {
      setCurrentPage(totalPages - 1);
    } else if (newPage < 0) {
      setCurrentPage(0);
    } else {
      setCurrentPage(newPage);
    }
  }

  const pageRows = rows.slice(
    currentPage * MAX_ITEMS,
    MAX_ITEMS + currentPage * MAX_ITEMS,
  );

  const columns: {
    label: string;
    field: keyof EngagementLeaderRow;
    format?: (value: number) => string;
  }[] = [
    { label: 'Projects', field: 'project_count' },
    { label: 'Flights', field: 'flight_count' },
    { label: 'Data products', field: 'data_product_count' },
    { label: 'Views', field: 'total_views' },
    { label: 'Likes', field: 'total_likes' },
    { label: 'Data usage (GB)', field: 'total_storage', format: bytesToGB },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-medium text-gray-600">Rank by:</span>
        {METRIC_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onMetricChange(option.value)}
            className={
              option.value === metric
                ? 'rounded-sm bg-blue-600 px-3 py-1 text-sm font-medium text-white'
                : 'rounded-sm bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-200'
            }
          >
            {option.label}
          </button>
        ))}
      </div>

      {rows.length === 0 ? (
        <section className="w-full bg-white">No activity yet</section>
      ) : (
        <>
          <table className="w-full border-separate border-spacing-y-1 border-spacing-x-1">
            <thead>
              <tr className="h-12 text-slate-700 bg-slate-300">
                <th className="p-2 text-left">User</th>
                {columns.map((column) => (
                  <th
                    key={column.field}
                    className={
                      column.field === activeField ? 'p-2 text-blue-700' : 'p-2'
                    }
                  >
                    {column.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pageRows.map((row) => (
                <tr key={row.user_id} className="text-center">
                  <td className="max-w-96 truncate bg-slate-100 p-2 text-left">
                    <span className="font-medium">{row.name}</span>
                    <span className="ml-2 text-sm text-gray-500">
                      {row.email}
                    </span>
                  </td>
                  {columns.map((column) => (
                    <td
                      key={column.field}
                      className={
                        column.field === activeField
                          ? 'bg-blue-50 p-2 font-semibold text-blue-700'
                          : 'bg-slate-50 p-2'
                      }
                    >
                      {column.format
                        ? column.format(row[column.field] as number)
                        : row[column.field]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination
            currentPage={currentPage}
            updateCurrentPage={updateCurrentPage}
            totalPages={totalPages}
          />
        </>
      )}
    </div>
  );
}

export default function DashboardActivity() {
  const {
    summary,
    trends,
    leaderboard: initialLeaderboard,
  } = useLoaderData() as ActivityLoaderData;

  const [metric, setMetric] = useState<LeaderboardMetric>('data_products');
  const [leaderboard, setLeaderboard] =
    useState<EngagementLeaderRow[]>(initialLeaderboard);
  const [activeInfo, setActiveInfo] = useState<InfoKey | null>(null);

  // Re-rank server-side when the metric changes so users outside the initial
  // top-N (by data products) can still surface for views, likes, etc.
  useEffect(() => {
    if (metric === 'data_products') {
      setLeaderboard(initialLeaderboard);
      return;
    }
    let active = true;
    api
      .get(
        `/admin/activity/leaderboard?metric=${metric}&limit=${LEADERBOARD_LIMIT}`,
      )
      .then((res) => {
        if (active) setLeaderboard(res.data);
      });
    return () => {
      active = false;
    };
  }, [metric, initialLeaderboard]);

  const stickiness = useMemo(() => {
    if (trends.length === 0) return null;
    return trends[trends.length - 1].stickiness;
  }, [trends]);

  return (
    <section className="h-full w-full overflow-y-auto bg-white p-4">
      <div className="flex flex-col gap-10">
        <div>
          <SectionHeading infoKey="active" onInfo={setActiveInfo} />
          <ActiveUserCards summary={summary} />
        </div>

        <div>
          <SectionHeading
            infoKey="trend"
            onInfo={setActiveInfo}
            className="mb-1"
          />
          {stickiness !== null && (
            <p className="mb-3 text-sm text-gray-500">
              Latest stickiness (DAU/MAU): {(stickiness * 100).toFixed(0)}%
            </p>
          )}
          <div className="h-96">
            <ActiveUsersTrend trends={trends} />
          </div>
        </div>

        <div>
          <SectionHeading infoKey="funnel" onInfo={setActiveInfo} />
          <ActivationFunnel summary={summary} />
        </div>

        <div>
          <SectionHeading infoKey="leaderboard" onInfo={setActiveInfo} />
          <EngagementLeaderboard
            rows={leaderboard}
            metric={metric}
            onMetricChange={setMetric}
          />
        </div>
      </div>

      <SectionInfoModal
        activeInfo={activeInfo}
        onClose={() => setActiveInfo(null)}
      />
    </section>
  );
}
