import axios, { AxiosResponse } from 'axios';
import { Feature } from 'geojson';
import { LatLngExpression } from 'leaflet';
import Papa from 'papaparse';
import { useEffect, useState } from 'react';
import {
  Circle,
  FeatureGroup,
  LayersControl,
  Polygon,
  Polyline,
  Popup,
} from 'react-leaflet';
import area from '@turf/area';
import flip from '@turf/flip';

import LoadingBars from '../LoadingBars';
import { useMapContext } from './MapContext';
import { MapLayerTableRow, prepMapLayers } from '../pages/projects/mapLayers/utils';
import {
  DataProduct,
  MapLayerFeatureCollection,
  ZonalFeature,
} from '../pages/projects/Project';
import { Project } from '../pages/projects/ProjectList';
import StripedTable from '../StripedTable';

import { isSingleBand } from './utils';
import { removeKeysFromFeatureProperties } from '../pages/projects/mapLayers/utils';
import { download as downloadGeoJSON } from '../pages/projects/mapLayers/utils';
import { downloadFile as downloadCSV } from '../pages/projects/fieldCampaigns/utils';

export type ZonalStatistics = {
  min: number;
  max: number;
  mean: number;
  count: number;
  [key: string]: string | number;
};

/**
 * Flips GeoJSON coordinates from long/lat to lat/long.
 * @param {MapLayerTableRow[]} layers Feature collections for the selected project.
 * @returns {MapLayerTableRow[]} Same as input, but with coordinates flipped.
 */
function flipCoordinates(layers: MapLayerTableRow[]): MapLayerTableRow[] {
  layers.forEach((layer) => {
    const flippedFeatureCollection = flip(layer.featureCollection);
    layer.featureCollection = flippedFeatureCollection;
  });
  return layers;
}

const FeatureAttributes = ({ feature }: { feature: Feature }) => (
  <div>
    <span className="text-base font-semibold">Attributes</span>
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <StripedTable
        headers={['Name', 'Value']}
        values={Object.keys(feature.properties?.properties).map((key) => ({
          label: key,
          value: feature.properties?.properties[key],
        }))}
      />
    </div>
  </div>
);

const FeatureTitle = ({ feature }: { feature: Feature }) => (
  <div className="flex flex-col">
    <span className="text-lg font-bold">{feature.properties?.layer_name}</span>
    {feature.geometry.type === 'Polygon' ? (
      <span className="text-md text-slate-600">
        Area: {area(feature).toFixed(2)} m&sup2;
      </span>
    ) : null}
  </div>
);

const ZonalStatistics = ({
  dataProduct,
  zonalFeature,
}: {
  dataProduct: DataProduct | null;
  zonalFeature: ZonalFeature | null;
}) =>
  dataProduct && isSingleBand(dataProduct) && zonalFeature ? (
    <div className="grid grid-flow-row auto-rows-max">
      <span className="text-base font-semibold">Zonal Statistics Result</span>
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <StripedTable
          headers={['Statistic', 'Value']}
          values={[
            { label: 'Min', value: zonalFeature.properties.min.toFixed(2) },
            { label: 'Max', value: zonalFeature.properties.max.toFixed(2) },
            { label: 'Mean', value: zonalFeature.properties.mean.toFixed(2) },
            { label: 'Median', value: zonalFeature.properties.median.toFixed(2) },
            { label: 'StDev', value: zonalFeature.properties.std.toFixed(2) },
            { label: 'Count', value: zonalFeature.properties.count.toString() },
          ]}
        />
      </div>
    </div>
  ) : null;

const ZonalStatisticsLoading = ({
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

const DownloadZonalStatistic = ({ zonalFeature }: { zonalFeature: ZonalFeature }) => (
  <div>
    <span className="text-base font-semibold">Download Zonal Statistic Result</span>
    <div>
      <button
        type="button"
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

export default function ProjectLayersControl({ project }: { project: Project }) {
  const [isCalculatingZonalStats, setIsCalculatingZonalStats] = useState(false);
  const [statistics, setStatistics] = useState<ZonalFeature | null>(null);

  const { activeDataProduct, projectLayers, projectLayersDispatch } = useMapContext();

  useEffect(() => {
    async function getProjectLayers(projectId: string) {
      try {
        const response: AxiosResponse<MapLayerFeatureCollection[]> = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}/vector_layers`
        );
        if (response.status === 200) {
          projectLayersDispatch({ type: 'set', payload: response.data });
        } else {
          projectLayersDispatch({ type: 'clear' });
        }
      } catch (err) {
        console.error(err);
      }
    }
    if (project) {
      getProjectLayers(project.id);
    }
  }, [project]);

  async function fetchZonalStatistics(
    dataProductId: string,
    flightId: string,
    zoneFeature: Feature
  ) {
    setIsCalculatingZonalStats(true);
    try {
      const response: AxiosResponse<ZonalFeature> = await axios.post(
        `${import.meta.env.VITE_API_V1_STR}/projects/${
          project.id
        }/flights/${flightId}/data_products/${dataProductId}/zonal_statistics`,
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

  return projectLayers.length > 0 ? (
    <LayersControl position="topright" collapsed={false} sortLayers={true}>
      {flipCoordinates(prepMapLayers(projectLayers)).map((layer) => (
        <LayersControl.Overlay key={layer.id} name={layer.name}>
          <FeatureGroup>
            {layer.featureCollection.features.map((feature, index) => {
              if (
                feature.geometry.type === 'Point' ||
                feature.geometry.type === 'MultiPoint'
              ) {
                return (
                  <Circle
                    key={`${layer.id}::${index}`}
                    center={feature.geometry.coordinates as LatLngExpression}
                    pathOptions={{ color: '#ece7f2' }}
                    radius={0.5}
                    eventHandlers={{
                      mouseover: (e) => {
                        e.target.setStyle({ color: '#addd8e' });
                      },
                      mouseout: (e) => {
                        e.target.setStyle({ color: '#ece7f2' });
                      },
                    }}
                  >
                    <Popup>
                      <div className="p-2">
                        <div className="flex flex-col gap-4">
                          <FeatureTitle feature={feature} />
                          <FeatureAttributes feature={feature} />
                        </div>
                      </div>
                    </Popup>
                  </Circle>
                );
              } else if (
                feature.geometry.type === 'LineString' ||
                feature.geometry.type === 'MultiLineString'
              ) {
                return (
                  <Polyline
                    key={`${layer.id}::${index}`}
                    pathOptions={{ color: '#ece7f2', weight: 3 }}
                    positions={feature.geometry.coordinates as LatLngExpression[]}
                    eventHandlers={{
                      mouseover: (e) => {
                        e.target.setStyle({ color: '#addd8e' });
                      },
                      mouseout: (e) => {
                        e.target.setStyle({ color: '#ece7f2' });
                      },
                    }}
                  >
                    <Popup>
                      <div className="p-2">
                        <div className="flex flex-col gap-4">
                          <FeatureTitle feature={feature} />
                          <FeatureAttributes feature={feature} />
                        </div>
                      </div>
                    </Popup>
                  </Polyline>
                );
              } else if (
                feature.geometry.type === 'Polygon' ||
                feature.geometry.type === 'MultiPolygon'
              ) {
                return (
                  <Polygon
                    key={`${layer.id}::${index}`}
                    pathOptions={{ color: '#ece7f2' }}
                    positions={feature.geometry.coordinates as LatLngExpression[][]}
                    eventHandlers={{
                      mouseover: (e) => {
                        e.target.setStyle({ color: '#addd8e' });
                      },
                      mouseout: (e) => {
                        e.target.setStyle({ color: '#ece7f2' });
                      },
                      click: () => {
                        // clear out previous statistics
                        setStatistics(null);
                        // check if zonal statistics available in local storage for active data product
                        if (
                          activeDataProduct &&
                          (feature.geometry.type === 'Polygon' ||
                            feature.geometry.type === 'MultiPolygon')
                        ) {
                          const precalculatedStats = localStorage.getItem(
                            `${activeDataProduct.id}::${btoa(
                              feature.geometry.coordinates.join('|')
                            )}`
                          );
                          if (precalculatedStats) {
                            setStatistics(JSON.parse(precalculatedStats));
                          } else {
                            // fetch zonal statistics from endpoint
                            fetchZonalStatistics(
                              activeDataProduct.id,
                              activeDataProduct.flight_id,
                              flip(feature)
                            );
                          }
                        }
                      },
                    }}
                  >
                    <Popup maxHeight={450} minWidth={300}>
                      <section className="p-2">
                        <div className="flex flex-col gap-4">
                          <FeatureTitle feature={feature} />
                          <FeatureAttributes feature={feature} />
                          {!activeDataProduct || !isSingleBand(activeDataProduct) ? (
                            <div className="h-full flex flex-col items-center justify-center gap-2 text-lg">
                              Select single band data product to view statistics for
                              this zone.
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
                          {statistics && (
                            <DownloadZonalStatistic zonalFeature={statistics} />
                          )}
                        </div>
                      </section>
                    </Popup>
                  </Polygon>
                );
              }
            })}
          </FeatureGroup>
        </LayersControl.Overlay>
      ))}
    </LayersControl>
  ) : null;
}
