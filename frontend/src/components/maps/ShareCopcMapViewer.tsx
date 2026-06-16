import 'maplibre-gl-lidar/style.css';
import { AxiosResponse } from 'axios';
import { useEffect, useMemo, useRef, useState } from 'react';
import Map, { MapRef, NavigationControl, ScaleControl } from 'react-map-gl/maplibre';
import { useLocation } from 'react-router';

import { AlertBar, Status } from '../Alert';
import { DataProduct } from '../pages/workspace/projects/Project';
import ProjectPointCloudLayer from './ProjectPointCloudLayer';
import {
  getMapboxSatelliteBasemapStyle,
  getWorldImageryTopoBasemapStyle,
} from './styles/basemapStyles';

import api from '../../api';
import { recordDataProductView } from '../../utils/recordDataProductView';

function useQuery() {
  const { search } = useLocation();
  return useMemo(() => new URLSearchParams(search), [search]);
}

export default function ShareCopcMapViewer() {
  const [dataProduct, setDataProduct] = useState<DataProduct | null>(null);
  const [fetchedBounds, setFetchedBounds] = useState<
    [number, number, number, number] | null
  >(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [mapboxAccessToken, setMapboxAccessToken] = useState(
    import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || ''
  );
  const [maptilerApiKey, setMaptilerApiKey] = useState(
    import.meta.env.VITE_MAPTILER_API_KEY || ''
  );

  const mapRef = useRef<MapRef | null>(null);
  const query = useQuery();
  const fileId = query.get('file_id');

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
    async function fetchDataProduct(fileID: string) {
      try {
        const response = await api.get(`/public?file_id=${fileID}`);
        if (response) {
          setDataProduct(response.data);
          recordDataProductView(response.data.id);
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

  useEffect(() => {
    if (!dataProduct || dataProduct.bbox) return;

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

  useEffect(() => {
    if (mapRef.current && bounds && bounds.length === 4) {
      mapRef.current.fitBounds(bounds, { padding: 20, duration: 1000 });
    }
  }, [bounds]);

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
      style={{ width: '100%', height: '100%' }}
      mapboxAccessToken={mapboxAccessToken || undefined}
      mapStyle={mapStyle}
      maxZoom={25}
      reuseMaps={true}
    >
      {dataProduct && <ProjectPointCloudLayer dataProduct={dataProduct} />}
      <NavigationControl />
      <ScaleControl />
      {status && <AlertBar alertType={status.type}>{status.msg}</AlertBar>}
    </Map>
  );
}
