import L from 'leaflet';
import { useEffect, useRef } from 'react';
import { Circle, FeatureGroup } from 'react-leaflet';
import { useMapEvents } from 'react-leaflet/hooks';
import { useMap } from 'react-leaflet/hooks';
import MarkerClusterGroup from 'react-leaflet-cluster';

type Location = {
  id: string;
  latitude: number;
  longitude: number;
};

export default function ClusterMarkers({
  activeMarker,
  markers,
  updateVisibleMarkers,
}: {
  activeMarker: string;
  markers: Location[];
  updateVisibleMarkers: (markers: string[]) => void;
}) {
  const map = useMap();

  const fgRef = useRef<L.FeatureGroup>(null);

  const _updateVisibleMarkers = () => {
    let visibleMarkers: string[] = [];
    if (markers.length > 0) {
      markers.forEach((marker) => {
        const coords = L.latLng([marker.latitude, marker.longitude]);
        if (map.getBounds().contains(coords)) {
          visibleMarkers.push(marker.id);
        }
      });
      updateVisibleMarkers(visibleMarkers);
    }
  };

  // zoom to extent of markers
  useEffect(() => {
    if (fgRef.current) {
      map.fitBounds(fgRef.current.getBounds(), { maxZoom: 16 });
      _updateVisibleMarkers();
    }
  }, [markers]);

  useMapEvents({
    moveend(_e) {
      _updateVisibleMarkers();
    },
  });

  if (markers.length === 0) return null;

  return (
    <FeatureGroup ref={fgRef}>
      <MarkerClusterGroup showCoverageOnHover={false}>
        {markers.map(({ id, latitude, longitude }) => (
          <Circle
            key={id}
            center={[latitude, longitude]}
            radius={10}
            pathOptions={{
              color: id === activeMarker ? '#3471FF' : 'white',
              fillOpacity: 1,
            }}
          />
        ))}
      </MarkerClusterGroup>
    </FeatureGroup>
  );
}
