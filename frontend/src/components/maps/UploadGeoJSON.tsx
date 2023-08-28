import { useEffect, useRef } from 'react';
import { GeoJSON } from 'react-leaflet/GeoJSON';
import { useLeafletContext } from '@react-leaflet/core';

import { FeatureCollection } from './MapModal';
import { SetLocation } from './MapModal';

interface Props {
  data: FeatureCollection;
  setLocation: SetLocation;
}

export default function UploadGeoJSON({ data, setLocation }: Props) {
  const context = useLeafletContext();
  const fcRef = useRef<L.GeoJSON | null>(null);

  useEffect(() => {
    if (fcRef.current) {
      context.map.fitBounds(fcRef.current.getBounds());
    }
  }, [fcRef.current]);

  return (
    <GeoJSON
      ref={fcRef}
      data={data}
      onEachFeature={(_feature, layer: L.Polygon) => {
        layer.on('click', () => {
          if (fcRef.current) {
            fcRef.current.resetStyle();
            layer.setStyle({ color: 'yellow' });
            setLocation({
              geojson: layer.toGeoJSON(),
              center: layer.getCenter(),
            });
          }
        });
      }}
    />
  );
}
