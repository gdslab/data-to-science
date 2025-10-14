import '@watergis/maplibre-gl-terradraw/dist/maplibre-gl-terradraw.css';
import './MeasureTerraDrawControl.css';
import { useEffect, useRef } from 'react';
import { useMap } from 'react-map-gl/maplibre';
import { MaplibreMeasureControl } from '@watergis/maplibre-gl-terradraw';

type MeasureUnitType = 'metric' | 'imperial';

interface MeasureTerraDrawControlProps {
  unitType?: MeasureUnitType;
}

export default function MeasureTerraDrawControl({
  unitType = 'metric',
}: MeasureTerraDrawControlProps) {
  const { current: map } = useMap();
  const drawRef = useRef<MaplibreMeasureControl | null>(null);

  useEffect(() => {
    if (!map || drawRef.current) return;

    const draw = new MaplibreMeasureControl({
      modes: [
        'point',
        'linestring',
        'polygon',
        'rectangle',
        'angled-rectangle',
        'circle',
        'sector',
        'sensor',
        'freehand',
        'select',
        'delete-selection',
        'delete',
        'download',
      ],
      open: true,
      measureUnitType: unitType,
      distancePrecision: 2,
      areaPrecision: 2,
      computeElevation: true,
    });

    // Set font glyphs to use fonts available in OpenMapTiles
    draw.fontGlyphs = ['Open Sans Regular'];

    drawRef.current = draw;
    map.addControl(draw, 'bottom-right');

    return () => {
      if (drawRef.current) {
        map.removeControl(drawRef.current);
        drawRef.current = null;
      }
    };
  }, [map, unitType]);

  return null;
}
