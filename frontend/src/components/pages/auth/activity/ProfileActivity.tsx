import { useState } from 'react';
import {
  FaChartColumn,
  FaGlobe,
  FaHeart,
  FaLayerGroup,
  FaRegEye,
} from 'react-icons/fa6';

import DataProductList from './DataProductList';
import DataProductRow from './DataProductRow';
import StatTile from './StatTile';
import ViewsTrend from './ViewsTrend';
import useProfileStats from './useProfileStats';
import { formatRelativeTime } from './relativeTime';
import { DataProductStatRow, RecentActivityRow } from './types';

type Segment = 'received' | 'activity';

function subline(
  dataType: string,
  flightDate: string,
  ownerName?: string,
): string {
  const typeLabel = dataType.split('_').join(' ');
  const parts = [typeLabel, `Flight ${flightDate}`];
  if (ownerName) parts.push(ownerName);
  return parts.join(' · ');
}

function StatTileSkeleton() {
  return <div className="h-20 animate-pulse rounded-xs bg-gray-100" />;
}

export default function ProfileActivity({ active }: { active: boolean }) {
  const [segment, setSegment] = useState<Segment>('received');
  const { data, loading, error } = useProfileStats(active);

  if (error) {
    return (
      <p className="text-sm text-red-700">
        Unable to load activity stats. Please try again later.
      </p>
    );
  }

  const received = data?.received;
  const activity = data?.activity;

  return (
    <div className="flex flex-col gap-6">
      {/* Segmented control */}
      <div
        className="inline-flex self-start rounded-lg bg-gray-100 p-1"
        role="tablist"
        aria-label="Activity perspective"
      >
        {(
          [
            ['received', 'On your data'],
            ['activity', 'Your activity'],
          ] as [Segment, string][]
        ).map(([value, label]) => (
          <button
            key={value}
            type="button"
            role="tab"
            aria-selected={segment === value}
            onClick={() => setSegment(value)}
            className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors motion-reduce:transition-none ${
              segment === value
                ? 'bg-primary text-white'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {segment === 'received' ? (
        <div className="flex flex-col gap-6">
          {/* Headline tiles */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {loading || !received ? (
              <>
                <StatTileSkeleton />
                <StatTileSkeleton />
                <StatTileSkeleton />
                <StatTileSkeleton />
              </>
            ) : (
              <>
                <StatTile
                  label="Total views"
                  value={received.total_views}
                  icon={<FaRegEye className="h-3 w-3" />}
                  tooltip="Total number of times other users have viewed data products in projects you own."
                />
                <StatTile
                  label="Total likes"
                  value={received.total_likes}
                  icon={<FaHeart className="h-3 w-3 text-accent2" />}
                  tooltip="Total number of likes other users have given to data products in projects you own."
                />
                <StatTile
                  label="Data products"
                  value={received.data_product_count}
                  icon={<FaLayerGroup className="h-3 w-3" />}
                  tooltip="Number of active data products across all projects you own."
                />
                <StatTile
                  label="Public"
                  value={received.public_count}
                  icon={<FaGlobe className="h-3 w-3" />}
                  tooltip="How many of your data products are publicly visible."
                />
              </>
            )}
          </div>

          {/* Views trend */}
          <div className="flex flex-col gap-2">
            <span className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-gray-500">
              <FaChartColumn className="h-3.5 w-3.5" />
              Views over the last 12 weeks
            </span>
            {loading || !received ? (
              <div className="h-32 animate-pulse rounded-xs bg-gray-100" />
            ) : (
              <ViewsTrend points={received.views_trend} />
            )}
          </div>

          {/* Top lists */}
          {received ? (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <DataProductList
                title="Most viewed"
                isEmpty={received.top_viewed.length === 0}
                emptyMessage="No views yet."
              >
                {received.top_viewed.map((row: DataProductStatRow, i) => (
                  <DataProductRow
                    key={row.id}
                    rank={i + 1}
                    projectName={row.project_name}
                    subline={subline(row.data_type, row.flight_date)}
                    dataProductId={row.id}
                    projectId={row.project_id}
                    flightId={row.flight_id}
                    metric={
                      <span className="flex items-center gap-1 text-gray-600">
                        <FaRegEye className="h-4 w-4" />
                        {row.views.toLocaleString()}
                      </span>
                    }
                  />
                ))}
              </DataProductList>
              <DataProductList
                title="Most liked"
                isEmpty={received.top_liked.length === 0}
                emptyMessage="No likes yet."
              >
                {received.top_liked.map((row: DataProductStatRow, i) => (
                  <DataProductRow
                    key={row.id}
                    rank={i + 1}
                    projectName={row.project_name}
                    subline={subline(row.data_type, row.flight_date)}
                    dataProductId={row.id}
                    projectId={row.project_id}
                    flightId={row.flight_id}
                    metric={
                      <span className="flex items-center gap-1 text-accent2">
                        <FaHeart className="h-4 w-4" />
                        {row.likes.toLocaleString()}
                      </span>
                    }
                  />
                ))}
              </DataProductList>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {/* Activity tiles */}
          <div className="grid grid-cols-2 gap-3">
            {loading || !activity ? (
              <>
                <StatTileSkeleton />
                <StatTileSkeleton />
              </>
            ) : (
              <>
                <StatTile
                  label="Products you viewed"
                  value={activity.viewed_count}
                  icon={<FaRegEye className="h-3 w-3" />}
                  tooltip="Number of distinct data products you have viewed across the platform."
                />
                <StatTile
                  label="Products you liked"
                  value={activity.liked_count}
                  icon={<FaHeart className="h-3 w-3 text-accent2" />}
                  tooltip="Number of distinct data products you have liked across the platform."
                />
              </>
            )}
          </div>

          {/* Recent lists */}
          {activity ? (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <DataProductList
                title="Recently viewed by you"
                isEmpty={activity.recently_viewed.length === 0}
                emptyMessage="No views yet."
              >
                {activity.recently_viewed.map((row: RecentActivityRow) => (
                  <DataProductRow
                    key={row.id}
                    projectName={row.project_name}
                    subline={subline(
                      row.data_type,
                      row.flight_date,
                      row.owner_name,
                    )}
                    dataProductId={row.id}
                    projectId={row.project_id}
                    flightId={row.flight_id}
                    metric={
                      <span className="text-xs text-gray-400">
                        {formatRelativeTime(row.last_action_at)}
                      </span>
                    }
                  />
                ))}
              </DataProductList>
              <DataProductList
                title="Recently liked by you"
                isEmpty={activity.recently_liked.length === 0}
                emptyMessage="No likes yet."
              >
                {activity.recently_liked.map((row: RecentActivityRow) => (
                  <DataProductRow
                    key={row.id}
                    projectName={row.project_name}
                    subline={subline(
                      row.data_type,
                      row.flight_date,
                      row.owner_name,
                    )}
                    dataProductId={row.id}
                    projectId={row.project_id}
                    flightId={row.flight_id}
                    metric={
                      <span className="text-xs text-gray-400">
                        {formatRelativeTime(row.last_action_at)}
                      </span>
                    }
                  />
                ))}
              </DataProductList>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
