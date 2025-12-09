import Papa from 'papaparse';

import { DataProduct, ZonalFeature } from '../pages/projects/Project';
import LoadingBars from '../LoadingBars';
import StripedTable from '../StripedTable';

import { download as downloadGeoJSON } from '../pages/projects/mapLayers/utils';
import { downloadFile as downloadCSV } from '../pages/projects/fieldCampaigns/utils';
import { isSingleBand } from './utils';
import { removeKeysFromFeatureProperties } from '../pages/projects/mapLayers/utils';

export type ZonalStatistics = {
  min: number;
  max: number;
  mean: number;
  count: number;
  [key: string]: string | number;
};

export const ZonalStatistics = ({
  dataProduct,
  zonalFeature,
}: {
  dataProduct: DataProduct | null;
  zonalFeature: ZonalFeature | null;
}) => {
  if (!dataProduct || !isSingleBand(dataProduct) || !zonalFeature) {
    return null;
  }

  return (
    <div className="grid grid-flow-row auto-rows-max">
      <span className="text-base font-semibold">Zonal Statistics Result</span>
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <StripedTable
          headers={['Statistic', 'Value']}
          values={[
            { label: 'Min', value: zonalFeature.properties.min.toFixed(2) },
            { label: 'Max', value: zonalFeature.properties.max.toFixed(2) },
            { label: 'Mean', value: zonalFeature.properties.mean.toFixed(2) },
            {
              label: 'Median',
              value: zonalFeature.properties.median.toFixed(2),
            },
            { label: 'StDev', value: zonalFeature.properties.std.toFixed(2) },
            { label: 'Count', value: zonalFeature.properties.count.toString() },
          ]}
        />
      </div>
    </div>
  );
};

export const ZonalStatisticsLoading = ({
  dataProduct,
  zonalFeature,
}: {
  dataProduct: DataProduct | null;
  zonalFeature: ZonalFeature | null;
}) =>
  dataProduct && isSingleBand(dataProduct) && !zonalFeature ? (
    <div className="h-full flex flex-col items-center justify-center gap-2 text-lg">
      <span>Loading Zonal Statistics...</span>
      <LoadingBars />
    </div>
  ) : null;

export const DownloadZonalStatistic = ({
  zonalFeature,
}: {
  zonalFeature: ZonalFeature;
}) => (
  <div>
    <span className="text-base font-semibold">
      Download Zonal Statistic Result
    </span>
    <div>
      <button
        type="button"
        className="cursor-pointer"
        onClick={() => {
          const csvData = Papa.unparse([
            Object.fromEntries(
              Object.entries(zonalFeature.properties).filter(
                ([key]) =>
                  ![
                    'id',
                    'layer_id',
                    'is_active',
                    'project_id',
                    'flight_id',
                    'data_product_id',
                  ].includes(key)
              )
            ),
          ]);
          const csvFile = new Blob([csvData], { type: 'text/csv' });
          downloadCSV(csvFile, 'zonal_statistics.csv');
        }}
      >
        <span className="text-sky-600">Download CSV</span>
      </button>
    </div>
    <div>
      <button
        type="button"
        className="cursor-pointer"
        onClick={() => {
          downloadGeoJSON(
            'json',
            removeKeysFromFeatureProperties(
              {
                type: 'FeatureCollection',
                features: [zonalFeature],
              },
              [
                'id',
                'feature_id',
                'layer_id',
                'is_active',
                'project_id',
                'flight_id',
                'data_product_id',
              ]
            ),
            'zonal_statistics.geojson'
          );
        }}
      >
        <span className="text-sky-600">Download GeoJSON</span>
      </button>
    </div>
  </div>
);
