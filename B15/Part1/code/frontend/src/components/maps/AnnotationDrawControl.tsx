import '@watergis/maplibre-gl-terradraw/dist/maplibre-gl-terradraw.css';
import { useEffect, useRef, useState } from 'react';
import { useMap } from 'react-map-gl/maplibre';
import { MaplibreTerradrawControl } from '@watergis/maplibre-gl-terradraw';
import { Feature } from 'geojson';

import api from '../../api';
import AnnotationCreateModal from './AnnotationCreateModal';
import { useAnnotationContext } from './contexts/AnnotationContext';

interface AnnotationDrawControlProps {
  projectId: string;
  flightId: string;
  dataProductId: string;
}

export default function AnnotationDrawControl({
  projectId,
  flightId,
  dataProductId,
}: AnnotationDrawControlProps) {
  const { current: map } = useMap();
  const { deactivate, editingAnnotation, refetch } = useAnnotationContext();
  const drawRef = useRef<MaplibreTerradrawControl | null>(null);

  // Refs to access current values inside the long-lived TerraDraw finish handler
  const editingRef = useRef(editingAnnotation);
  const deactivateRef = useRef(deactivate);
  const refetchRef = useRef(refetch);
  const projectIdRef = useRef(projectId);
  const flightIdRef = useRef(flightId);
  const dataProductIdRef = useRef(dataProductId);
  const containerRef = useRef<HTMLDivElement>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [drawnFeature, setDrawnFeature] = useState<Feature | null>(null);
  const [drawnFeatureId, setDrawnFeatureId] = useState<string | number | null>(
    null
  );

  // Keep refs in sync for the long-lived TerraDraw finish handler
  useEffect(() => { editingRef.current = editingAnnotation; }, [editingAnnotation]);
  useEffect(() => { deactivateRef.current = deactivate; }, [deactivate]);
  useEffect(() => { refetchRef.current = refetch; }, [refetch]);
  useEffect(() => { projectIdRef.current = projectId; }, [projectId]);
  useEffect(() => { flightIdRef.current = flightId; }, [flightId]);
  useEffect(() => { dataProductIdRef.current = dataProductId; }, [dataProductId]);

  useEffect(() => {
    if (!map || drawRef.current || !containerRef.current) return;

    const draw = new MaplibreTerradrawControl({
      modes: ['point', 'linestring', 'polygon', 'rectangle', 'delete'],
      open: true,
    });

    drawRef.current = draw;

    // Manually call onAdd to get the control DOM element,
    // then mount it in our own container instead of a MapLibre control slot.
    // This lets us position the toolbar inline next to the toggle button.
    const controlElement = draw.onAdd(map.getMap());
    containerRef.current.appendChild(controlElement);

    const terraDraw = draw.getTerraDrawInstance();
    const handleFinish = async (
      id: string | number,
      context: { mode: string; action: string }
    ) => {
      if (context.mode === 'delete') return;

      const feature = terraDraw?.getSnapshotFeature(id);
      if (!feature) return;

      const { mode: _mode, ...restProperties } = feature.properties || {};
      const cleanFeature: Feature = {
        type: 'Feature',
        geometry: feature.geometry,
        properties: restProperties,
      };

      if (editingRef.current) {
        // Redraw mode: PUT new geometry to existing annotation
        try {
          await api.put(
            `/projects/${projectIdRef.current}/flights/${flightIdRef.current}/data_products/${dataProductIdRef.current}/annotations/${editingRef.current.id}`,
            { geom: cleanFeature }
          );
          try { terraDraw?.removeFeatures([id]); } catch { /* already removed */ }
          refetchRef.current();
          deactivateRef.current();
        } catch (err) {
          console.error('Failed to update annotation geometry', err);
        }
      } else {
        // Create mode: open the create modal
        setDrawnFeature(cleanFeature);
        setDrawnFeatureId(id);
        setModalOpen(true);
      }
    };
    terraDraw?.on('finish', handleFinish);

    return () => {
      terraDraw?.off('finish', handleFinish);
      if (drawRef.current) {
        drawRef.current.onRemove();
        drawRef.current = null;
      }
    };
  }, [map]);

  const removeDrawnFeature = () => {
    try {
      const terraDraw = drawRef.current?.getTerraDrawInstance();
      if (terraDraw && drawnFeatureId !== null) {
        terraDraw.removeFeatures([drawnFeatureId]);
      }
    } catch {
      // Feature may already have been removed
    }
    setDrawnFeature(null);
    setDrawnFeatureId(null);
  };

  const handleAnnotationSuccess = () => {
    removeDrawnFeature();
    refetch();
    deactivate();
  };

  const handleAnnotationCancel = () => {
    removeDrawnFeature();
  };

  return (
    <>
      <div ref={containerRef} />
      <AnnotationCreateModal
        open={modalOpen}
        setOpen={setModalOpen}
        feature={drawnFeature}
        projectId={projectId}
        flightId={flightId}
        dataProductId={dataProductId}
        onSuccess={handleAnnotationSuccess}
        onCancel={handleAnnotationCancel}
      />
    </>
  );
}