import { useFormikContext } from 'formik';
import { FeatureCollection } from 'geojson';
import { useEffect, useRef } from 'react';
import { GeoJSON } from 'react-leaflet/GeoJSON';
import { useLeafletContext } from '@react-leaflet/core';

import { useProjectContext } from '../../pages/projects/ProjectContext';
import { updateLocation } from '../GeomanControl';

interface Props {
  data: FeatureCollection;
  geomanLayer: L.Polygon<any> | null;
  setFeatureCollection: React.Dispatch<
    React.SetStateAction<FeatureCollection | null>
  >;
  setGeomanLayer: React.Dispatch<React.SetStateAction<L.Polygon<any> | null>>;
}

export default function UploadGeoJSON({
  data,
  geomanLayer,
  setFeatureCollection,
  setGeomanLayer,
}: Props) {
  const context = useLeafletContext();
  const { setFieldTouched, setFieldValue } = useFormikContext();
  const fcRef = useRef<L.GeoJSON | null>(null);

  const { locationDispatch } = useProjectContext();

  useEffect(() => {
    // remove any existing locations/geoman layers (only show uploaded feature collection)
    if (fcRef.current) {
      if (geomanLayer) geomanLayer.remove();
      setGeomanLayer(null);
      setFieldValue('location', {
        center_x: 0,
        center_y: 0,
        geom: '',
      });
      setFieldTouched('location', true);
      locationDispatch({ type: 'clear', payload: null });
    }
  }, [fcRef.current]);

  useEffect(() => {
    // fit the map to the bounding box of an uploaded feature collection
    if (fcRef.current) {
      context.map.fitBounds(fcRef.current.getBounds());
    }
  }, [fcRef.current]);

  useEffect(() => {
    // fcRef references a feature collection returned
    // from an uploaded shapefile. if there is only one
    // feature in the collection (e.g., a single polygon),
    // set the feature as the project location and
    // remove the feature collection.
    if (fcRef.current) {
      const layers = fcRef.current.getLayers() as L.Polygon[];
      if (layers.length === 1) {
        const layer = layers[0];
        updateLocation(layer, locationDispatch, setFieldTouched, setFieldValue);
        setFeatureCollection(null);
      }
    }
  }, [fcRef.current]);

  return (
    <GeoJSON
      ref={fcRef}
      data={data}
      onEachFeature={(_feature, layer: L.Polygon) => {
        // in the event an uploaded shapefile returns
        // a feature collection with multiple features
        // (e.g., polygons), the user must click a
        // feature to set the project location. after
        // a feature has been clicked, remove the
        // feature collection.
        layer.on('click', () => {
          updateLocation(
            layer,
            locationDispatch,
            setFieldTouched,
            setFieldValue
          );
          setFeatureCollection(null);
        });
      }}
    />
  );
}
