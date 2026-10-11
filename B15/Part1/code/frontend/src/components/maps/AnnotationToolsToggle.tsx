import './AnnotationToolsToggle.css';
import { useEffect, useState } from 'react';
import { FaDrawPolygon } from 'react-icons/fa6';

import AnnotationDrawControl from './AnnotationDrawControl';
import MapToolToggleButton from './MapToolToggleButton';
import { useAnnotationContext } from './contexts/AnnotationContext';
import { useMapContext } from './MapContext';

export default function AnnotationToolsToggle() {
  const { activeDataProduct, activeProject } = useMapContext();
  const { active, toggle, deactivate } = useAnnotationContext();
  const [shouldRender, setShouldRender] = useState(false);

  // Auto-deactivate annotation mode when activeDataProduct clears
  useEffect(() => {
    if (!activeDataProduct && active) {
      deactivate();
    }
  }, [activeDataProduct, active, deactivate]);

  // Delayed unmount for slide-out animation
  useEffect(() => {
    if (active) {
      setShouldRender(true);
    } else if (shouldRender) {
      document.body.classList.add('annotation-tools-closing');
      const timer = setTimeout(() => {
        setShouldRender(false);
        document.body.classList.remove('annotation-tools-closing');
      }, 300);
      return () => {
        clearTimeout(timer);
        document.body.classList.remove('annotation-tools-closing');
      };
    }
  }, [active, shouldRender]);

  // Only render when annotation mode is active with a data product
  if (!activeDataProduct || !activeProject || !active) return null;

  return (
    <div className="absolute bottom-9 max-md:bottom-20 right-2 m-2.5 z-10 pointer-events-none">
      <div className="flex items-center">
        {shouldRender && (
          <div className="annotation-tools-container pointer-events-auto mr-[-6px] pr-[8px]">
            <AnnotationDrawControl
              projectId={activeProject.id}
              flightId={activeDataProduct.flight_id}
              dataProductId={activeDataProduct.id}
            />
          </div>
        )}
        <MapToolToggleButton
          active={active}
          aria-label={active ? 'Exit annotation mode' : 'Enter annotation mode'}
          aria-pressed={active}
          title="Annotation Tools"
          onClick={toggle}
        >
          <FaDrawPolygon className="h-5 w-5" />
        </MapToolToggleButton>
      </div>
    </div>
  );
}
