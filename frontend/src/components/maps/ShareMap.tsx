import { AxiosResponse } from 'axios';
import { useEffect, useMemo, useRef, useState } from 'react';
import Map, {
  MapRef,
  NavigationControl,
  ScaleControl,
} from 'react-map-gl/maplibre';
import { useLocation } from 'react-router';

import { AlertBar, Status } from '../Alert';
import ColorBarControl from './ColorBarControl';
import ProjectRasterTiles from './ProjectRasterTiles';
import {
  MultibandSymbology,
  SingleBandSymbology,
  useRasterSymbologyContext,
} from './RasterSymbologyContext';
import { DataProduct } from '../pages/projects/Project';

import {
  getMapboxSatelliteBasemapStyle,
  getWorldImageryTopoBasemapStyle,
} from './styles/basemapStyles';

import api from '../../api';
import { isSingleBand } from './utils';

function useQuery() {
  const { search } = useLocation();

  return useMemo(() => new URLSearchParams(search), [search]);
}

function parseSymbology(
  symbologyQueryParams: string | null
): SingleBandSymbology | MultibandSymbology | undefined {
  let symbology = undefined;
  try {
    if (!symbologyQueryParams) throw new Error();
    symbology = JSON.parse(atob(symbologyQueryParams));
  } catch (error) {
    console.error(`Unable to parse symbology: ${error}`);
  }
  return symbology;
}

export default function ShareMap() {
  const [fetchedBounds, setFetchedBounds] = useState<
    [number, number, number, number] | null
  >(null);
  const [dataProduct, setDataProduct] = useState<DataProduct | null>(null);
  const [status, setStatus] = useState<Status | null>(null);

  const [mapboxAccessToken, setMapboxAccessToken] = useState(
    import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || ''
  );
  const [maptilerApiKey, setMaptilerApiKey] = useState(
    import.meta.env.VITE_MAPTILER_API_KEY || ''
  );
  const { state, dispatch } = useRasterSymbologyContext();

  const mapRef = useRef<MapRef | null>(null);

  const query = useQuery();
  const fileId = query.get('file_id');
  const symbologyQueryParam = query.get('symbology');
  const symbologyFromQueryParams = useMemo(
    () => parseSymbology(symbologyQueryParam),
    [symbologyQueryParam]
  );

  // Derive the actual bounds to use (prefer dataProduct.bbox, fallback to fetched)
  const bounds = dataProduct?.bbox || fetchedBounds;

  useEffect(() => {
    if (!mapboxAccessToken || !maptilerApiKey) {
      fetch('/config.json')
        .then((response) => response.json())
        .then((config) => {
          if (!mapboxAccessToken && config.mapboxAccessToken) {
            setMapboxAccessToken(config.mapboxAccessToken);
          }
          if (!maptilerApiKey && config.maptilerApiKey) {
            setMaptilerApiKey(config.maptilerApiKey);
          }
        })
        .catch((error) => {
          console.error('Failed to load config.json:', error);
        });
    }
  }, [mapboxAccessToken, maptilerApiKey]);

  useEffect(() => {
    async function fetchDataProduct(fileID) {
      try {
        const response = await api.get(`/public?file_id=${fileID}`);
        if (response) {
          setDataProduct(response.data);
        } else {
          setStatus({ type: 'error', msg: 'Unable to load data product' });
        }
      } catch {
        setStatus({ type: 'error', msg: 'Unable to load data product' });
      }
    }

    if (fileId) {
      fetchDataProduct(fileId);
    }
  }, [fileId]);

  // Fetch bounds from API when dataProduct doesn't have bbox
  useEffect(() => {
    if (!dataProduct || dataProduct.bbox) {
      return; // No need to fetch if bbox already exists
    }

    async function getBounds(dataProductId: string) {
      try {
        const response: AxiosResponse<{
          bounds: [number, number, number, number];
        }> = await api.get(`/public/bounds?data_product_id=${dataProductId}`);
        setFetchedBounds(response ? response.data.bounds : null);
      } catch {
        setFetchedBounds(null);
      }
    }

    getBounds(dataProduct.id);
  }, [dataProduct]);

  // Fit map to bounds when bounds change
  useEffect(() => {
    if (mapRef.current && bounds && bounds.length === 4) {
      mapRef.current.fitBounds(bounds, {
        padding: 20,
        duration: 1000,
      });
    }
  }, [bounds]);

  useEffect(() => {
    if (dataProduct && symbologyFromQueryParams) {
      dispatch({
        type: 'SET_SYMBOLOGY',
        rasterId: dataProduct.id,
        payload: symbologyFromQueryParams,
      });
      dispatch({
        type: 'SET_READY_STATE',
        rasterId: dataProduct.id,
        payload: true,
      });
    }
  }, [dataProduct, dispatch, symbologyFromQueryParams]);

  const mapStyle = useMemo(() => {
    return mapboxAccessToken
      ? getMapboxSatelliteBasemapStyle(mapboxAccessToken)
      : getWorldImageryTopoBasemapStyle(maptilerApiKey);
  }, [mapboxAccessToken, maptilerApiKey]);

  return (
    <Map
      ref={mapRef}
      initialViewState={{
        longitude: -86.9138040788386,
        latitude: 40.428655143949925,
        zoom: 8,
      }}
      style={{
        width: '100%',
        height: '100%',
      }}
      mapboxAccessToken={mapboxAccessToken || undefined}
      mapStyle={mapStyle}
      maxZoom={25}
      reuseMaps={true}
    >
      {/* Display raster tiles */}
      {dataProduct && state[dataProduct.id]?.symbology && (
        <ProjectRasterTiles
          boundingBox={dataProduct.bbox}
          dataProduct={dataProduct}
        />
      )}

      {/* Display color bar when single band data product */}
      {dataProduct &&
        isSingleBand(dataProduct) &&
        state[dataProduct.id]?.symbology && (
          <ColorBarControl dataProduct={dataProduct} />
        )}

      {/* General controls */}
      <NavigationControl />
      <ScaleControl />

      {/* Display alerts */}
      {status && <AlertBar alertType={status.type}>{status.msg}</AlertBar>}
    </Map>
  );
}
