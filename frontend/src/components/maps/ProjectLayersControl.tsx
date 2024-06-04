import axios, { AxiosResponse } from 'axios';
import { Feature, FeatureCollection } from 'geojson';
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
import { DataProduct } from '../pages/projects/Project';
import { Project } from '../pages/projects/ProjectList';
import { LatLngExpression } from 'leaflet';

type ZonalStatistics = {
  min: number;
  max: number;
  mean: number;
  count: number;
};

/**
 * Returns true if data product has a single band.
 * @param dataProduct Active data product.
 * @returns True if single band, otherwise False.
 */
function isSingleBand(dataProduct: DataProduct): boolean {
  return dataProduct.stac_properties && dataProduct.stac_properties.raster.length === 1;
}

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

export default function ProjectLayersControl({ project }: { project: Project }) {
  const [statistics, setStatistics] = useState<ZonalStatistics[] | null>(null);

  const { activeDataProduct, projectLayers, projectLayersDispatch } = useMapContext();

  useEffect(() => {
    async function getProjectLayers(projectId: string) {
      try {
        const response: AxiosResponse<FeatureCollection[]> = await axios.get(
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
    try {
      const response: AxiosResponse<ZonalStatistics[]> = await axios.post(
        `${import.meta.env.VITE_API_V1_STR}/projects/${
          project.id
        }/flights/${flightId}/data_products/${dataProductId}/zonal_statistics`,
        zoneFeature
      );
      if (response.status === 200) {
        setStatistics(response.data);
      } else {
        setStatistics(null);
      }
    } catch (err) {
      console.error(err);
      setStatistics(null);
    }
  }

  const FeatureAttributes = ({ feature }: { feature: Feature }) => (
    <div>
      <span className="text-md font-semibold">Attributes</span>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y-2 divide-gray-200 bg-white text-sm">
          <thead>
            <tr>
              {Object.keys(feature.properties?.properties).map((key, index) => (
                <th
                  key={`${key}::${index}`}
                  className="whitespace-nowrap px-4 py-2 font-medium text-gray-900"
                >
                  {key}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            <tr>
              {Object.keys(feature.properties?.properties).map((key, index) => (
                <td
                  key={`${key}::${index}`}
                  className="whitespace-nowrap px-4 py-2 text-gray-700"
                >
                  {feature.properties?.properties[key]}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
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
    stats,
  }: {
    dataProduct: DataProduct | null;
    stats: ZonalStatistics[] | null;
  }) =>
    dataProduct && isSingleBand(dataProduct) && stats && stats.length > 0 ? (
      <div className="grid grid-flow-row auto-rows-max">
        <span className="text-md font-semibold">Zonal Stats</span>
        <span>Min: {stats[0].min.toFixed(2)}</span>
        <span>Max: {stats[0].max.toFixed(2)}</span>
        <span>Mean: {stats[0].mean.toFixed(2)}</span>
        <span>Count: {stats[0].count}</span>
      </div>
    ) : null;

  const ZonalStatisticsLoading = ({
    dataProduct,
    stats,
  }: {
    dataProduct: DataProduct | null;
    stats: ZonalStatistics[] | null;
  }) =>
    dataProduct && isSingleBand(dataProduct) && !stats ? (
      <div className="h-full flex flex-col items-center justify-center gap-2 text-lg">
        <span>Loading Zonal Statistics...</span>
        <LoadingBars />
      </div>
    ) : null;

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
                        if (activeDataProduct && feature.geometry.type === 'Polygon') {
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
                    <Popup>
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
                          <ZonalStatisticsLoading
                            dataProduct={activeDataProduct}
                            stats={statistics}
                          />
                          <ZonalStatistics
                            dataProduct={activeDataProduct}
                            stats={statistics}
                          />
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
