import '@maplibre/maplibre-gl-geocoder/dist/maplibre-gl-geocoder.css';
import './MaplibreGeocoderControl.css';

import maplibregl from 'maplibre-gl';
import { useEffect } from 'react';
import { useMap } from 'react-map-gl/maplibre';
import MaplibreGeocoder, {
  CarmenGeojsonFeature,
  MaplibreGeocoderApi,
  MaplibreGeocoderFeatureResults,
} from '@maplibre/maplibre-gl-geocoder';

export default function MaplibreGeocoderControl() {
  const { current: map } = useMap();

  useEffect(() => {
    if (!map) return;

    const geocoderApi: MaplibreGeocoderApi = {
      forwardGeocode: async (config) => {
        const features: CarmenGeojsonFeature[] = [];
        try {
          const request = `https://nominatim.openstreetmap.org/search?q=${config.query}&format=geojson&polygon_geojson=1&addressdetails=1`;
          const response = await fetch(request);
          const geojson = await response.json();
          geojson.features.forEach((feature, index) => {
            const center = [
              feature.bbox[0] + (feature.bbox[2] - feature.bbox[0]) / 2,
              feature.bbox[1] + (feature.bbox[3] - feature.bbox[1]) / 2,
            ];
            const point: CarmenGeojsonFeature = {
              id: `${index}`,
              type: 'Feature',
              geometry: {
                type: 'Point',
                coordinates: center,
              },
              place_name: feature.properties.display_name,
              properties: feature.properties,
              text: feature.properties.display_name,
              place_type: ['place'],
            };
            features.push(point);
          });
        } catch (e) {
          console.error(`Failed to forwardGeocode with error: ${e}`);
        }

        return {
          type: 'FeatureCollection',
          features,
        } as MaplibreGeocoderFeatureResults;
      },
      reverseGeocode: async () => {
        // No-op, added to meet MaplibreGeocoderApi type requirements
        return {
          type: 'FeatureCollection',
          features: [],
        } as MaplibreGeocoderFeatureResults;
      },
    };

    const geocoder = new MaplibreGeocoder(geocoderApi, {
      collapsed: true,
      debounceSearch: 800,
      marker: false,
      maplibregl: maplibregl,
      showResultMarkers: true,
    });
    map.addControl(geocoder, 'top-left');

    return () => {
      if (map) {
        map.removeControl(geocoder);
      }
    };
  }, [map]);

  return null;
}
