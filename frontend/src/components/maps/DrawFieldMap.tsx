import 'leaflet/dist/leaflet.css';
import { useEffect, useRef, useState } from 'react';
import { MapContainer } from 'react-leaflet/MapContainer';
import { Polygon } from 'react-leaflet/Polygon';
import { ZoomControl } from 'react-leaflet/ZoomControl';
import { useLeafletContext } from '@react-leaflet/core';

import GeomanControl from './GeomanControl';
import MapLayersControl from './MapLayersControl';
import UploadGeoJSON from './UploadGeoJSON';
import { FeatureCollection } from '../pages/projects/Project';
import { useProjectContext } from '../pages/projects/ProjectContext';

// updates map (loads tiles) after container size changes
const InvalidateSize = () => {
  const context = useLeafletContext();
  if (context.map) context.map.invalidateSize(true);
  return null;
};

function getGCKey(location, fc) {
  if (location) {
    return location.properties.id;
  } else if (fc) {
    return 'feature-collection';
  } else {
    return 'none';
  }
}

interface Props {
  isUpdate?: boolean;
  featureCollection: FeatureCollection | null;
  setFeatureCollection: React.Dispatch<React.SetStateAction<FeatureCollection | null>>;
}

export default function DrawFieldMap({
  isUpdate = false,
  featureCollection,
  setFeatureCollection,
}: Props) {
  const layerRef = useRef(null);
  const mapRef = useRef<L.Map>(null);
  const [geomanLayer, setGeomanLayer] = useState<L.Polygon | null>(null);

  const { location } = useProjectContext();

  useEffect(() => {
    if (mapRef.current) {
      mapRef.current.setZoom(8);
    }
  }, []);

  return (
    <MapContainer
      ref={mapRef}
      center={[40.428655143949925, -86.9138040788386]}
      preferCanvas={true}
      zoom={8}
      maxZoom={26}
      scrollWheelZoom={true}
      zoomControl={false}
      style={{ height: '100%', width: '100%' }}
      worldCopyJump={true}
    >
      <InvalidateSize />
      {featureCollection ? (
        <UploadGeoJSON
          data={featureCollection}
          geomanLayer={geomanLayer}
          setFeatureCollection={setFeatureCollection}
          setGeomanLayer={setGeomanLayer}
        />
      ) : null}
      <MapLayersControl />
      {location && !geomanLayer ? (
        <Polygon
          key={getGCKey(location, featureCollection) + 'poly'}
          ref={layerRef}
          positions={location.geometry.coordinates[0].map((coordPair) => [
            coordPair[1],
            coordPair[0],
          ])}
        />
      ) : null}
      <GeomanControl
        key={getGCKey(location, featureCollection)}
        isUpdate={isUpdate}
        layerRef={layerRef}
        options={{ position: 'topleft' }}
        disableDraw={featureCollection ? true : false}
        disableEdit={location ? false : true}
        setGeomanLayer={setGeomanLayer}
      />
      <ZoomControl
        key={getGCKey(location, featureCollection) + 'zc'}
        position="topleft"
      />
    </MapContainer>
  );
}
