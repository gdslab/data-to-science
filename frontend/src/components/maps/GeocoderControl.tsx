import 'leaflet-control-geocoder/dist/Control.Geocoder.css';
import L from 'leaflet';
import Geocoder, { geocoders } from 'leaflet-control-geocoder';
import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet/hooks';

export default function GeocoderControl({
  position = 'topleft',
  showMarker = false,
}: {
  position?: L.ControlPosition;
  showMarker?: boolean;
}) {
  const map = useMap();

  const bboxPolyRef = useRef<L.Polygon | null>(null);

  useEffect(() => {
    // Create geocoder control with default OSM/Nominatim geocoding provider
    const GeocoderControl = new Geocoder({
      defaultMarkGeocode: showMarker,
      geocoder: new geocoders.Nominatim(),
      position: position,
    });
    GeocoderControl.addTo(map);

    // Create polygon for geocode bounding box and add to map
    if (!showMarker) {
      GeocoderControl.on('markgeocode', function (e) {
        // Remove bounding box polygon if one exists
        if (bboxPolyRef.current) {
          map.removeLayer(bboxPolyRef.current);
        }
        // Create new bounding box polygon and add to map
        const bbox = e.geocode.bbox;
        const poly = L.polygon(
          [
            bbox.getSouthEast(),
            bbox.getNorthEast(),
            bbox.getNorthWest(),
            bbox.getSouthWest(),
          ],
          { fill: false, color: '#f9ff33' }
        ).addTo(map);
        // Update state with new bounding box polygon
        bboxPolyRef.current = poly;
        // Zoom map to extent of bounding box polygon
        map.fitBounds(poly.getBounds());
        // Add event to remove polygon when clicked
        // poly.addEventListener('click', () => {
        //   if (confirm('Remove boundary?') && bboxPolyRef.current) {
        //     map.removeLayer(bboxPolyRef.current);
        //   }
        // });
      });
    }

    // Cleanup control after component unmounts or effect re-runs
    return () => {
      GeocoderControl.remove();

      if (bboxPolyRef.current) {
        map.removeLayer(bboxPolyRef.current);
      }
    };
  }, [map]);

  return null;
}
