import { createControlComponent } from '@react-leaflet/core';
import * as L from 'leaflet';
import '@geoman-io/leaflet-geoman-free';
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';

interface GeomanOptions extends L.ControlOptions {
  position: L.ControlPosition;
}

const Geoman = L.Control.extend({
  initialize(options: GeomanOptions) {
    L.setOptions(this, options);
  },

  addTo(map: L.Map) {
    if (!map.pm) return;

    map.pm.addControls({
      ...this.options,
      drawMarker: false,
      drawCircle: false,
      drawCircleMarker: false,
      drawPolyline: false,
      drawRectangle: false,
      drawText: false,
      drawPolygon: true,
      editMode: false,
      cutPolygon: false,
      rotateMode: false,
    });

    map.on('pm:create', (layer) => {
      this.options.setLocation({
        geojson: layer.layer.toGeoJSON(),
        center: layer.layer.getCenter(),
      });
    });
  },
});

const createGeomanInstance = (options: GeomanOptions) => {
  return new Geoman(options);
};

export const GeomanControl = createControlComponent(createGeomanInstance);
