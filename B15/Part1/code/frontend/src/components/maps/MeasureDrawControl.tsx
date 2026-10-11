import '@watergis/maplibre-gl-terradraw/dist/maplibre-gl-terradraw.css';
import { useEffect, useRef } from 'react';
import { useMap } from 'react-map-gl/maplibre';
import { MaplibreMeasureControl } from '@watergis/maplibre-gl-terradraw';

export default function MeasureDrawControl() {
  const { current: map } = useMap();
  const drawRef = useRef<MaplibreMeasureControl | null>(null);

  useEffect(() => {
    if (!map || drawRef.current) return;

    const draw = new MaplibreMeasureControl({
      modes: ['linestring', 'polygon', 'rectangle', 'circle', 'delete'],
      open: true,
      measureUnitType: 'metric',
      distancePrecision: 2,
      areaPrecision: 2,
      computeElevation: true,
    });

    // Set font glyphs to use fonts available in OpenMapTiles
    draw.fontGlyphs = ['Open Sans Regular'];

    drawRef.current = draw;
    map.addControl(draw, 'top-left');

    return () => {
      if (drawRef.current) {
        map.removeControl(drawRef.current);
        drawRef.current = null;
      }
    };
  }, [map]);

  return null;
}
