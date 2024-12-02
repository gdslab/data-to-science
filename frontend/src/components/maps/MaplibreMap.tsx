import 'maplibre-gl/dist/maplibre-gl.css';
import './MaplibreMap.css';
import axios, { AxiosResponse } from 'axios';
import { Feature } from 'geojson';
import { StyleSpecification } from 'maplibre-gl';
import Papa from 'papaparse';
import { useEffect, useState } from 'react';
import Map, {
  GeolocateControl,
  NavigationControl,
  Popup,
  ScaleControl,
} from 'react-map-gl/maplibre';
import area from '@turf/area';
import flip from '@turf/flip';

import LoadingBars from '../LoadingBars';
import { useMapContext } from './MapContext';
import MaplibreCluster from './MaplibreCluster';
import MaplibreProjectBoundary from './MaplibreProjectBoundary';
import MaplibreProjectVectorTiles from './MaplibreProjectVectorTiles';
import MaplibreProjectRasterTiles from './MaplibreProjectRasterTiles';
import MaplibreLayerControl from './MaplibreLayerControl';
import { useMapLayerContext } from './MapLayersContext';
import { DataProduct, MapLayer, ZonalFeature } from '../pages/projects/Project';
import StripedTable from '../StripedTable';

import { download as downloadGeoJSON } from '../pages/projects/mapLayers/utils';
import { downloadFile as downloadCSV } from '../pages/projects/fieldCampaigns/utils';
import { isSingleBand, mapApiResponseToLayers } from './utils';
import { removeKeysFromFeatureProperties } from '../pages/projects/mapLayers/utils';

type ProjectPopup = {
  feature: Feature;
  latitude: number;
  longitude: number;
};

const satelliteBasemapStyle: StyleSpecification = {
  version: 8,
  glyphs: `https://api.maptiler.com/fonts/{fontstack}/{range}.pbf?key=${
    import.meta.env.VITE_MAPTILER_API_KEY
  }`,
  sources: {
    satellite: {
      type: 'raster',
      tiles: [
        `https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/tiles/{z}/{x}/{y}?access_token=${
          import.meta.env.VITE_MAPBOX_ACCESS_TOKEN
        }`,
      ],
      tileSize: 256,
    },
  },
  layers: [
    {
      id: 'satellite-layer',
      type: 'raster',
      source: 'satellite',
    },
  ],
};

export type ZonalStatistics = {
  min: number;
  max: number;
  mean: number;
  count: number;
  [key: string]: string | number;
};

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

export default function MaplibreMap() {
  const [isCalculatingZonalStats, setIsCalculatingZonalStats] = useState(false);
  const [statistics, setStatistics] = useState<ZonalFeature | null>(null);
  const [popupInfo, setPopupInfo] = useState<
    ProjectPopup | { [key: string]: any } | null
  >(null);
  const {
    activeDataProduct,
    activeMapTool,
    activeProject,
    activeProjectDispatch,
    projects,
  } = useMapContext();
  const {
    state: { layers },
    dispatch,
  } = useMapLayerContext();

  // Fetch map layers when a project is activated
  useEffect(() => {
    const fetchMapLayers = async (projectId: string) => {
      const mapLayersUrl = `${
        import.meta.env.VITE_API_V1_STR
      }/projects/${projectId}/vector_layers`;
      try {
        const response: AxiosResponse<MapLayer[]> = await axios.get(mapLayersUrl);
        dispatch({
          type: 'SET_LAYERS',
          payload: mapApiResponseToLayers(response.data),
        });
      } catch (error) {
        console.error('Error fetching project map layers:', error);
        dispatch({ type: 'SET_LAYERS', payload: [] });
      }
    };
    if (activeProject) {
      fetchMapLayers(activeProject.id);
    }
  }, [activeProject]);

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
      console.log(response);
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

  const handleMapClick = (event) => {
    const map: maplibregl.Map = event.target;

    if (map.getLayer('unclustered-point')) {
      const features = map.queryRenderedFeatures(event.point, {
        layers: ['unclustered-point'],
      });

      if (features.length > 0) {
        const clickedFeature = features[0];

        if (clickedFeature.geometry.type === 'Point') {
          const coordinates = clickedFeature.geometry.coordinates;

          setPopupInfo({
            feature: clickedFeature,
            latitude: coordinates[1],
            longitude: coordinates[0],
          });
        }
      }
    }

    if (layers.length > 0) {
      for (const layer of layers) {
        if (layer.checked && map.getLayer(layer.id)) {
          const features = map.queryRenderedFeatures(event.point, {
            layers: [layer.id],
          });

          if (features.length > 0) {
            const clickedFeature = features[0];
            const clickCoordinates = event.lngLat;
            console.log('clickedFeature', clickedFeature);
            setPopupInfo({
              feature: clickedFeature,
              latitude: clickCoordinates.lat,
              longitude: clickCoordinates.lng,
            });

            if (
              clickedFeature.geometry.type === 'Polygon' ||
              clickedFeature.geometry.type === 'MultiPolygon'
            ) {
              // clear out previous statistics
              setStatistics(null);
              // check if zonal statistics available in local storage for active data product
              if (activeDataProduct && activeProject) {
                const precalculatedStats = localStorage.getItem(
                  `${activeDataProduct.id}::${btoa(
                    clickedFeature.geometry.coordinates.join('|')
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
                    flip(clickedFeature)
                  );
                }
              }
            }
          }
        }
      }
    }
  };

  const FeatureHeader = ({ feature }: { feature: Feature }) => {
    const attrs = feature.properties;

    if (!attrs) {
      return <div>No title</div>;
    } else {
      return (
        <div className="flex flex-col">
          <span className="text-lg font-bold">{feature.properties?.layer_name}</span>
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

  return (
    <Map
      initialViewState={{
        longitude: -86.9138040788386,
        latitude: 40.428655143949925,
        zoom: 8,
      }}
      style={{
        width: '100%',
        height: '100%',
      }}
      mapboxAccessToken={import.meta.env.VITE_MAPBOX_ACCESS_TOKEN}
      mapStyle={satelliteBasemapStyle}
      reuseMaps={true}
      onClick={handleMapClick}
    >
      {/* Display marker cluster for project centroids when no project is active */}
      {activeMapTool === 'map' && !activeProject && <MaplibreCluster />}

      {/* Display popup on click for project markers when no project is active */}
      {activeMapTool === 'map' && !activeProject && popupInfo && (
        <Popup
          anchor="top"
          longitude={popupInfo.longitude}
          latitude={popupInfo.latitude}
          onClose={() => setPopupInfo(null)}
          style={{ width: '240px' }}
        >
          <article className="flex flex-col gap-2 text-wrap">
            <h3>{popupInfo.feature.properties.title}</h3>
            <p>{popupInfo.feature.properties.title}</p>
            <button
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300"
              onClick={() => {
                const thisProject = projects?.filter(
                  ({ id }) => id === popupInfo.feature.properties.id
                );
                if (thisProject && thisProject.length === 1) {
                  activeProjectDispatch({ type: 'set', payload: thisProject[0] });
                  setPopupInfo(null);
                }
              }}
            >
              Open
            </button>
          </article>
        </Popup>
      )}

      {/* Display popup on click on map layer feature */}
      {activeMapTool === 'map' && activeProject && popupInfo && (
        <Popup
          anchor="top"
          longitude={popupInfo.longitude}
          latitude={popupInfo.latitude}
          onClose={() => setPopupInfo(null)}
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
      )}

      {/* Display project raster tiles when project active and data product active */}
      {activeMapTool === 'map' && activeProject && activeDataProduct && (
        <MaplibreProjectRasterTiles
          key={activeDataProduct.id}
          dataProduct={activeDataProduct}
        />
      )}

      {/* Display project vector layers when project active and layers selected */}
      {activeMapTool === 'map' && activeProject && <MaplibreProjectVectorTiles />}

      {/* Display project boundary when project activated */}
      {activeMapTool === 'map' && activeProject && <MaplibreProjectBoundary />}

      {/* Project map layer controls */}
      {activeMapTool === 'map' && activeProject && <MaplibreLayerControl />}

      {/* General controls */}
      <GeolocateControl />
      <NavigationControl />
      <ScaleControl />
    </Map>
  );
}
