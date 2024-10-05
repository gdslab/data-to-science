import 'leaflet/dist/leaflet.css';
import axios, { AxiosResponse } from 'axios';
import { useEffect, useMemo, useRef, useState } from 'react';
import { MapContainer } from 'react-leaflet/MapContainer';
import { ZoomControl } from 'react-leaflet/ZoomControl';
import { useLocation } from 'react-router-dom';

import { AlertBar, Status } from '../Alert';
import ColorBarControl from './ColorBarControl';
import DataProductTileLayer from './DataProductTileLayer';
import MapLayersControl from './MapLayersControl';
import { DataProduct } from '../pages/workspace/projects/Project';
import { DSMSymbologySettings, OrthoSymbologySettings } from './Maps';

import { isSingleBand } from './utils';

function useQuery() {
  const { search } = useLocation();

  return useMemo(() => new URLSearchParams(search), [search]);
}

function parseSymbology(
  symbologyParam: string | null
): DSMSymbologySettings | OrthoSymbologySettings | undefined {
  let symbology = undefined;
  try {
    if (!symbologyParam) throw new Error();
    symbology = JSON.parse(atob(symbologyParam));
  } catch (error) {
    console.log('Unable to parse symbology');
  }
  return symbology;
}

export default function ShareMap() {
  const [bounds, setBounds] = useState<number[] | null>(null);
  const [dataProduct, setDataProduct] = useState<DataProduct | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const query = useQuery();
  const fileID = query.get('file_id');
  const symbology: DSMSymbologySettings | OrthoSymbologySettings | undefined =
    parseSymbology(query.get('symbology'));

  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    async function fetchDataProduct(fileID) {
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/public?file_id=${fileID}`
        );
        if (response) {
          setDataProduct(response.data);
        } else {
          setStatus({ type: 'error', msg: 'Unable to load data product' });
        }
      } catch (err) {
        setStatus({ type: 'error', msg: 'Unable to load data product' });
      }
    }

    if (fileID && symbology) {
      fetchDataProduct(fileID);
    }
  }, []);

  useEffect(() => {
    if (mapRef.current && bounds) {
      if (bounds.length == 4) {
        mapRef.current.fitBounds([
          [bounds[1], bounds[0]],
          [bounds[3], bounds[2]],
        ]);
      }
    }
  }, [bounds]);

  useEffect(() => {
    async function getBounds(dataProductId) {
      try {
        const response: AxiosResponse<{ bounds: [number, number, number, number] }> =
          await axios.get(
            `${
              import.meta.env.VITE_API_V1_STR
            }/public/bounds?data_product_id=${dataProductId}`
          );
        if (response) {
          setBounds(response.data.bounds);
        } else {
          setBounds(null);
        }
      } catch (err) {
        setBounds(null);
      }
    }
    if (dataProduct) {
      getBounds(dataProduct.id);
    }
  }, [dataProduct]);

  return (
    <MapContainer
      ref={mapRef}
      center={[40.428655143949925, -86.9138040788386]}
      preferCanvas={true}
      zoom={8}
      maxZoom={24}
      scrollWheelZoom={true}
      zoomControl={false}
    >
      {status ? <AlertBar alertType={status.type}>{status.msg}</AlertBar> : null}
      {dataProduct ? (
        <DataProductTileLayer
          activeDataProduct={dataProduct}
          symbology={symbology}
          tileLayerRef={tileLayerRef}
        />
      ) : null}
      {dataProduct && isSingleBand(dataProduct) ? (
        <ColorBarControl
          dataProduct={dataProduct}
          symbology={symbology as DSMSymbologySettings}
        />
      ) : null}
      <MapLayersControl />
      <ZoomControl position="bottomright" />
    </MapContainer>
  );
}
