import axios, { AxiosResponse } from 'axios';
import { Feature } from 'geojson';
import { useState } from 'react';
import { Popup } from 'react-map-gl/maplibre';
import area from '@turf/area';

import { PopupInfoProps } from './HomeMap';
import { ZonalFeature } from '../pages/workspace/projects/Project';
import { useMapContext } from './MapContext';
import StripedTable from '../StripedTable';
import {
  DownloadZonalStatistic,
  ZonalStatistics,
  ZonalStatisticsLoading,
} from './ZonalStatistics';

import { isSingleBand } from './utils';

type FeaturePopupProps = {
  popupInfo: PopupInfoProps | { [key: string]: any };
  onClose: () => void;
};

export default function FeaturePopup({
  popupInfo,
  onClose,
}: FeaturePopupProps) {
  const [isCalculatingZonalStats, setIsCalculatingZonalStats] = useState(false);
  const [statistics, setStatistics] = useState<ZonalFeature | null>(null);

  const { activeDataProduct, activeProject } = useMapContext();

  const FeatureHeader = ({ feature }: { feature: Feature }) => {
    const attrs = feature.properties;

    if (!attrs) {
      return <div>No title</div>;
    } else {
      return (
        <div className="flex flex-col">
          <span className="text-lg font-bold">
            {feature.properties?.layer_name}
          </span>
          {feature.geometry.type === 'Polygon' ? (
            <span className="text-md text-slate-600">
              Area: {area(feature).toFixed(2)} m&sup2;
            </span>
          ) : null}
        </div>
      );
    }
  };

  const FeatureAttributes = ({ feature }: { feature: Feature }) => {
    const attrs = feature.properties;

    if (!attrs) {
      return (
        <div>
          <span>No attributes</span>
        </div>
      );
    } else {
      return (
        <div>
          <span className="text-base font-semibold">Attributes</span>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <StripedTable
              headers={['Name', 'Value']}
              values={Object.keys(attrs).map((key) => ({
                label: key,
                value: attrs[key],
              }))}
            />
          </div>
        </div>
      );
    }
  };

  async function fetchZonalStatistics(
    dataProductId: string,
    flightId: string,
    projectId: string,
    zoneFeature: Feature
  ) {
    setIsCalculatingZonalStats(true);
    try {
      const response: AxiosResponse<ZonalFeature> = await axios.post(
        `${
          import.meta.env.VITE_API_V1_STR
        }/projects/${projectId}/flights/${flightId}/data_products/${dataProductId}/zonal_statistics`,
        zoneFeature
      );
      if (response.status === 200) {
        setStatistics(response.data);
        setIsCalculatingZonalStats(false);
      } else {
        setStatistics(null);
        setIsCalculatingZonalStats(false);
      }
    } catch (_err) {
      console.log('Unable to fetch zonal statistics');
      setStatistics(null);
      setIsCalculatingZonalStats(false);
    }
  }

  const handleOnOpen = () => {
    if (
      popupInfo.feature.geometry.type === 'Polygon' ||
      popupInfo.feature.geometry.type === 'MultiPolygon'
    ) {
      // clear out previous statistics
      setStatistics(null);
      // check if zonal statistics available in local storage for active data product
      if (activeDataProduct && activeProject) {
        const precalculatedStats = localStorage.getItem(
          `${activeDataProduct.id}::${btoa(
            popupInfo.feature.geometry.coordinates.join('|')
          )}`
        );
        if (precalculatedStats) {
          setStatistics(JSON.parse(precalculatedStats));
        } else {
          // fetch zonal statistics from endpoint
          fetchZonalStatistics(
            activeDataProduct.id,
            activeDataProduct.flight_id,
            activeProject.id,
            popupInfo.feature
          );
        }
      }
    }
  };

  return (
    <Popup
      anchor="top"
      longitude={popupInfo.longitude}
      latitude={popupInfo.latitude}
      onOpen={handleOnOpen}
      onClose={onClose}
      maxWidth="400px"
    >
      <article className="p-2">
        <div className="flex flex-col gap-4">
          <FeatureHeader feature={popupInfo.feature} />
          <FeatureAttributes feature={popupInfo.feature} />
          {!activeDataProduct || !isSingleBand(activeDataProduct) ? (
            <div className="h-full flex flex-col items-center justify-center gap-2 text-lg">
              Select single band data product to view statistics for this zone.
            </div>
          ) : null}
          {isCalculatingZonalStats && (
            <ZonalStatisticsLoading
              dataProduct={activeDataProduct}
              zonalFeature={statistics}
            />
          )}
          <ZonalStatistics
            dataProduct={activeDataProduct}
            zonalFeature={statistics}
          />
          {statistics && <DownloadZonalStatistic zonalFeature={statistics} />}
        </div>
      </article>
    </Popup>
  );
}
