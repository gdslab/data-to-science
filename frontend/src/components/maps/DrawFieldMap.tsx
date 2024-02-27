import 'leaflet/dist/leaflet.css';
import { useEffect, useRef, useState } from 'react';
import { MapContainer } from 'react-leaflet/MapContainer';
import { Polygon } from 'react-leaflet/Polygon';
import { ZoomControl } from 'react-leaflet/ZoomControl';
import { useLeafletContext } from '@react-leaflet/core';

import GeomanControl from './GeomanControl';
import MapLayersControl from './MapLayersControl';
import UploadGeoJSON from './UploadGeoJSON';
import { FeatureCollection, Location, SetLocation } from '../pages/projects/Project';

// updates map (loads tiles) after container size changes
const InvalidateSize = () => {
  const context = useLeafletContext();
  if (context.map) context.map.invalidateSize(true);
  return null;
};

function getGCKey(location, fc) {
  if (location) {
    return location.geojson.properties.id;
  } else if (fc) {
    return 'feature-collection';
  } else {
    return 'none';
  }
}

interface Props {
  featureCollection: FeatureCollection | null;
  location: Location | null;
  setLocation: SetLocation;
  setUploadResponse: React.Dispatch<React.SetStateAction<FeatureCollection | null>>;
}

export default function DrawFieldMap({
  featureCollection,
  location,
  setLocation,
  setUploadResponse,
}: Props) {
  const layerRef = useRef(null);
  const [geomanLayer, setGeomanLayer] = useState<L.Polygon | null>(null);

  useEffect(() => {
    if (geomanLayer) {
      geomanLayer.remove();
      setGeomanLayer(null);
    }
  }, [featureCollection]);

  return (
    <MapContainer
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
          setLocation={setLocation}
          setUploadResponse={setUploadResponse}
        />
      ) : null}
      <MapLayersControl />
      {location && location.type === 'uploaded' ? (
        <Polygon
          key={getGCKey(location, featureCollection) + 'poly'}
          ref={layerRef}
          positions={location.geojson.geometry.coordinates[0].map((coordPair) => [
            coordPair[1],
            coordPair[0],
          ])}
        />
      ) : null}
      <GeomanControl
        key={getGCKey(location, featureCollection)}
        layerRef={layerRef}
        options={{ position: 'topleft' }}
        location={location}
        setLocation={setLocation}
        setGeomanLayer={setGeomanLayer}
        disableDraw={featureCollection ? true : false}
        disableEdit={location ? false : true}
      />
      <ZoomControl
        key={getGCKey(location, featureCollection) + 'zc'}
        position="topleft"
      />
    </MapContainer>
  );
}
