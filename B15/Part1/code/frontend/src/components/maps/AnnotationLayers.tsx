import maplibregl from 'maplibre-gl';
import { useMemo, useEffect, useRef } from 'react';
import { Layer, Source, useMap } from 'react-map-gl/maplibre';

import { getAnnotationLayer } from './layerProps';
import {
  Annotation,
  useAnnotationContext,
  defaultAnnotationStyle,
} from './contexts/AnnotationContext';
import { formatArea, formatLength } from './LayerPane/utils';

function getMeasurement(annotation: Annotation): string | null {
  const geomType = annotation.geom.geometry?.type;
  if (geomType === 'LineString') return formatLength(annotation.geom);
  if (geomType === 'Polygon') return formatArea(annotation.geom);
  return null;
}

export default function AnnotationLayers() {
  const {
    active,
    annotations,
    checkedIds,
    styles,
    visible,
    hoveredAnnotationId,
    setHoveredAnnotationId,
    setSelectedAnnotationId,
  } = useAnnotationContext();
  const { current: map } = useMap();
  const previousIdsRef = useRef<Set<string>>(new Set());

  // Clean up layers that were unchecked or removed
  useEffect(() => {
    if (!map) return;

    const mapInstance = map.getMap();

    const currentIds = new Set(
      annotations
        .filter((a) => checkedIds.has(a.id))
        .map((a) => `annotation-${a.id}`)
    );

    // Find sources that were removed
    const removedIds = Array.from(previousIdsRef.current).filter(
      (id) => !currentIds.has(id)
    );

    removedIds.forEach((sourceId) => {
      // Remove label layer
      const labelLayerId = `${sourceId}-label`;
      if (mapInstance.getLayer(labelLayerId)) {
        mapInstance.removeLayer(labelLayerId);
      }

      // Remove border layer (for polygon annotations)
      const borderLayerId = `${sourceId}-border`;
      if (mapInstance.getLayer(borderLayerId)) {
        mapInstance.removeLayer(borderLayerId);
      }

      // Remove main layer
      if (mapInstance.getLayer(sourceId)) {
        mapInstance.removeLayer(sourceId);
      }

      // Remove source last
      if (mapInstance.getSource(sourceId)) {
        mapInstance.removeSource(sourceId);
      }
    });

    previousIdsRef.current = currentIds;
  }, [annotations, checkedIds, map]);

  // Build the list of annotation layer IDs to query against.
  // Kept as a ref so map event handlers always see the latest value
  // without needing to re-register on every change.
  const annotationLayerIdsRef = useRef<string[]>([]);
  useEffect(() => {
    const ids: string[] = [];
    for (const a of annotations) {
      if (!checkedIds.has(a.id)) continue;
      const sourceId = `annotation-${a.id}`;
      ids.push(sourceId);
      const geomType = a.geom.geometry?.type;
      if (geomType === 'Polygon') ids.push(`${sourceId}-border`);
    }
    annotationLayerIdsRef.current = ids;
  }, [annotations, checkedIds]);

  // Register map-level click and mousemove handlers using queryRenderedFeatures.
  // This avoids timing issues with per-layer registration since layers may not
  // exist on the map when the effect first runs.
  useEffect(() => {
    if (!map || active) return;
    const mapInstance = map.getMap();
    let currentHoverId: string | null = null;

    const queryAnnotationLayers = (point: maplibregl.PointLike) => {
      const ids = annotationLayerIdsRef.current.filter((id) =>
        mapInstance.getLayer(id)
      );
      if (ids.length === 0) return null;
      const features = mapInstance.queryRenderedFeatures(point, { layers: ids });
      if (features.length === 0) return null;
      const match = features[0].layer.id.match(/^annotation-([0-9a-f-]+)/);
      return match ? match[1] : null;
    };

    const handleClick = (e: maplibregl.MapMouseEvent) => {
      const annotationId = queryAnnotationLayers(e.point);
      if (annotationId) {
        setSelectedAnnotationId(annotationId);
      }
    };

    const handleMouseMove = (e: maplibregl.MapMouseEvent) => {
      const annotationId = queryAnnotationLayers(e.point);
      if (annotationId) {
        mapInstance.getCanvas().style.cursor = 'pointer';
        if (annotationId !== currentHoverId) {
          currentHoverId = annotationId;
          setHoveredAnnotationId(annotationId);
        }
      } else if (currentHoverId) {
        mapInstance.getCanvas().style.cursor = '';
        currentHoverId = null;
        setHoveredAnnotationId(null);
      }
    };

    mapInstance.on('click', handleClick);
    mapInstance.on('mousemove', handleMouseMove);

    return () => {
      mapInstance.off('click', handleClick);
      mapInstance.off('mousemove', handleMouseMove);
      if (currentHoverId) {
        mapInstance.getCanvas().style.cursor = '';
        setHoveredAnnotationId(null);
      }
    };
  }, [map, active, setSelectedAnnotationId, setHoveredAnnotationId]);

  const enrichedAnnotations = useMemo(
    () =>
      annotations
        .filter((a) => checkedIds.has(a.id))
        .map((annotation) => {
          const measurement = getMeasurement(annotation);
          const data = measurement
            ? {
                ...annotation.geom,
                properties: {
                  ...annotation.geom.properties,
                  measurement,
                },
              }
            : annotation.geom;
          return { annotation, data };
        }),
    [annotations, checkedIds]
  );

  if (!visible) return null;

  return enrichedAnnotations.map(({ annotation, data }) => {
    const sourceId = `annotation-${annotation.id}`;
    const geomType = annotation.geom.geometry?.type || 'Point';
    const style = styles[annotation.id] || defaultAnnotationStyle;
    const highlighted = hoveredAnnotationId === annotation.id;
    const layerProps = getAnnotationLayer(annotation.id, geomType, style, highlighted);
    const renderLayer = (props: React.ComponentProps<typeof Layer>) => (
      <Layer key={props.id} {...props} />
    );

    return (
      <Source key={sourceId} id={sourceId} type="geojson" data={data}>
        {Array.isArray(layerProps)
          ? layerProps.map(renderLayer)
          : renderLayer(layerProps)}
      </Source>
    );
  });
}
