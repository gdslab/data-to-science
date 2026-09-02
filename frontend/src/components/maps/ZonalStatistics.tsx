import Papa from 'papaparse';

import { ZonalFeature } from '../pages/workspace/projects/Project';
import { ZonalStatisticsState } from './useZonalStatistics';

import { download as downloadGeoJSON } from '../pages/workspace/projects/mapLayers/utils';
import { downloadFile as downloadCSV } from '../pages/workspace/projects/fieldCampaigns/utils';
import {
  removeKeysFromFeatureProperties,
  RESERVED_FEATURE_PROPERTY_KEYS,
} from '../pages/workspace/projects/mapLayers/utils';

type Stat = { label: string; value: string };
type ZonalProps = ZonalFeature['properties'];

// One list drives both the loaded grid and the loading skeleton
const STATS: { label: string; pick: (props: ZonalProps) => string }[] = [
  { label: 'Min', pick: (p) => p.min.toFixed(2) },
  { label: 'Max', pick: (p) => p.max.toFixed(2) },
  { label: 'Mean', pick: (p) => p.mean.toFixed(2) },
  { label: 'Median', pick: (p) => p.median.toFixed(2) },
  { label: 'StDev', pick: (p) => p.std.toFixed(2) },
  { label: 'Count', pick: (p) => p.count.toString() },
];

const StatGrid = ({ stats }: { stats: Stat[] }) => (
  <dl className="grid grid-cols-3 gap-2 text-sm">
    {stats.map(({ label, value }) => (
      <div key={label} className="min-w-0 rounded-md bg-slate-50 px-2 py-1.5">
        <dt className="text-xs text-slate-500">{label}</dt>
        <dd
          className="truncate font-medium tabular-nums text-slate-900"
          title={value}
        >
          {value}
        </dd>
      </div>
    ))}
  </dl>
);

const ZonalStatisticsSummary = ({
  zonalFeature,
}: {
  zonalFeature: ZonalFeature;
}) => (
  <StatGrid
    stats={STATS.map(({ label, pick }) => ({
      label,
      value: pick(zonalFeature.properties),
    }))}
  />
);

// Same shape as the loaded state so the panel height does not change on load
const ZonalStatisticsLoading = () => (
  <div className="flex flex-col gap-3">
    <div className="animate-pulse">
      <StatGrid stats={STATS.map(({ label }) => ({ label, value: '—' }))} />
    </div>
    <p className="text-sm text-slate-500">Calculating zonal statistics...</p>
  </div>
);

const ZonalStatisticsError = ({ onRetry }: { onRetry: () => void }) => (
  <div className="flex flex-col items-start gap-2 text-sm">
    <span className="text-red-700">
      Unable to calculate zonal statistics for this feature.
    </span>
    <button
      type="button"
      className="text-sky-600 hover:underline"
      onClick={onRetry}
    >
      Retry
    </button>
  </div>
);

const DownloadZonalStatistic = ({
  zonalFeature,
}: {
  zonalFeature: ZonalFeature;
}) => (
  <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
    <button
      type="button"
      className="text-sky-600 hover:underline"
      onClick={() => {
        const csvData = Papa.unparse([
          Object.fromEntries(
            Object.entries(zonalFeature.properties).filter(
              ([key]) => !RESERVED_FEATURE_PROPERTY_KEYS.includes(key)
            )
          ),
        ]);
        const csvFile = new Blob([csvData], { type: 'text/csv' });
        downloadCSV(csvFile, 'zonal_statistics.csv');
      }}
    >
      Download CSV
    </button>
    <button
      type="button"
      className="text-sky-600 hover:underline"
      onClick={() => {
        downloadGeoJSON(
          'json',
          removeKeysFromFeatureProperties(
            {
              type: 'FeatureCollection',
              features: [zonalFeature],
            },
            RESERVED_FEATURE_PROPERTY_KEYS
          ),
          'zonal_statistics.geojson'
        );
      }}
    >
      Download GeoJSON
    </button>
  </div>
);

export const ZonalStatisticsPanel = ({
  data,
  loading,
  error,
  refetch,
}: ZonalStatisticsState) => {
  if (loading) return <ZonalStatisticsLoading />;
  if (error) return <ZonalStatisticsError onRetry={refetch} />;
  if (!data) return null;

  return (
    <div className="flex flex-col gap-3">
      <ZonalStatisticsSummary zonalFeature={data} />
      <DownloadZonalStatistic zonalFeature={data} />
    </div>
  );
};
