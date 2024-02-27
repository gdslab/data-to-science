import { useEffect, useRef } from 'react';
import { GeoJSON } from 'react-leaflet/GeoJSON';
import { useLeafletContext } from '@react-leaflet/core';

import { FeatureCollection, SetLocation } from '../pages/projects/Project';

interface Props {
  data: FeatureCollection;
  setLocation: SetLocation;
  setUploadResponse: React.Dispatch<React.SetStateAction<FeatureCollection | null>>;
}

export default function UploadGeoJSON({ data, setLocation, setUploadResponse }: Props) {
  const context = useLeafletContext();
  const fcRef = useRef<L.GeoJSON | null>(null);

  useEffect(() => {
    setLocation(null);
  }, []);

  useEffect(() => {
    if (fcRef.current) {
      context.map.fitBounds(fcRef.current.getBounds());
    }
  }, [fcRef.current]);

  useEffect(() => {
    if (fcRef.current) {
      const layers = fcRef.current.getLayers() as L.Polygon[];
      if (layers.length === 1) {
        setLocation({
          geojson: layers[0].toGeoJSON(),
          center: layers[0].getCenter(),
          type: 'uploaded',
        });
        setUploadResponse(null);
      }
    }
  }, [fcRef.current]);

  return (
    <GeoJSON
      ref={fcRef}
      data={data}
      onEachFeature={(_feature, layer: L.Polygon) => {
        layer.on('click', () => {
          setLocation({
            geojson: layer.toGeoJSON(),
            center: layer.getCenter(),
            type: 'uploaded',
          });
          setUploadResponse(null);
        });
      }}
    />
  );
}
