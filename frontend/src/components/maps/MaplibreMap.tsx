import 'maplibre-gl/dist/maplibre-gl.css';
import './MaplibreMap.css';
import { StyleSpecification } from 'maplibre-gl';
import { useState } from 'react';
import Map, {
  GeolocateControl,
  NavigationControl,
  Popup,
  ScaleControl,
} from 'react-map-gl/maplibre';

import MaplibreCluster from './MaplibreCluster';

type ProjectPopup = {
  title: string;
  description: string;
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

export default function MaplibreMap() {
  const [popupInfo, setPopupInfo] = useState<ProjectPopup | null>(null);

  const markerIconUrl = 'https://docs.mapbox.com/mapbox-gl-js/assets/custom_marker.png';

  const handleMapLoad = (event) => {
    const map = event.target;
    // Add the custom marker icon to the map
    map.loadImage(markerIconUrl, (error, image) => {
      console.log('loadImage');
      if (error) throw error;
      if (!map.hasImage('marker-icon')) {
        console.log('adding image');
        map.addImage('marker-icon', image);
      }
    });
  };

  const handleMapClick = (event) => {
    const map = event.target;
    const features = map.queryRenderedFeatures(event.point, {
      layers: ['unclustered-point'],
    });

    if (features.length > 0) {
      const clickedFeature = features[0];
      const coordinates = clickedFeature.geometry.coordinates;
      setPopupInfo({
        ...features[0].properties,
        latitude: coordinates[1],
        longitude: coordinates[0],
      });
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
      onLoad={handleMapLoad}
    >
      {/* Marker Cluster for Project Centroids */}
      <MaplibreCluster />
      {popupInfo && (
        <Popup
          anchor="top"
          longitude={popupInfo.longitude}
          latitude={popupInfo.latitude}
          onClose={() => setPopupInfo(null)}
        >
          <div className="flex flex-col gap-2">
            <span className="text-lg font-bold">{popupInfo.title}</span>
            <p>{popupInfo.description}</p>
            <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300">
              Go To
            </button>
          </div>
        </Popup>
      )}
      {/* Controls */}
      <GeolocateControl />
      <NavigationControl />
      <ScaleControl />
    </Map>
  );
}
