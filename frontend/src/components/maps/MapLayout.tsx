import clsx from 'clsx';
import { useEffect, useState } from 'react';

import { useIsMobile } from '../hooks';
import LayerPane from './LayerPane';
import MapListToggle from './MapListToggle';

import { AnnotationProvider } from './contexts/AnnotationContext';
import { MapApiKeysContextProvider } from './MapApiKeysContext';
import { MapContextProvider, useMapContext } from './MapContext';
import { MapLayerProvider } from './MapLayersContext';
import MapViewMode from './MapViewMode';
import ProjectLoader from './ProjectLoader';
import { RasterSymbologyProvider } from './RasterSymbologyContext';

type MobileView = 'map' | 'list';

function MapLayoutContent() {
  const {
    activeDataProduct,
    activeMapTool,
    activeProject,
    pointCloudViewer,
  } = useMapContext();

  const isMobile = useIsMobile();
  const [hidePane, toggleHidePane] = useState(false);
  const [mobileView, setMobileView] = useState<MobileView>('list');

  // Default view based on whether a project is active
  useEffect(() => {
    if (!isMobile) return;
    setMobileView(activeProject ? 'map' : 'list');
  }, [isMobile, activeProject]);

  const isFullScreenViewer =
    activeDataProduct?.data_type === 'panoramic' ||
    activeDataProduct?.data_type === '3dgs' ||
    (activeDataProduct?.data_type === 'point_cloud' &&
      pointCloudViewer === 'potree') ||
    activeMapTool === 'compare';

  // Hide toggle for full-screen viewers that have no meaningful list to switch to
  const showToggle = isMobile && !isFullScreenViewer;

  const listHidden = isMobile && mobileView !== 'list';
  const mapHidden = isMobile && mobileView !== 'map';

  return (
    <div className="relative h-full md:flex md:flex-row">
      {/* sidebar / list panel */}
      <div
        id="panel-list"
        role={isMobile ? 'tabpanel' : undefined}
        aria-labelledby={isMobile ? 'tab-list' : undefined}
        inert={listHidden ? true : undefined}
        className={clsx(
          'bg-slate-100',
          'md:shrink-0',
          hidePane ? 'md:w-[48px]' : 'md:w-[450px]',
          'max-md:absolute max-md:inset-0 max-md:z-10 max-md:w-full',
          listHidden && 'invisible',
        )}
      >
        <LayerPane
          hidePane={!isMobile && hidePane}
          toggleHidePane={toggleHidePane}
        />
      </div>

      {/* map panel */}
      <div
        id="panel-map"
        role={isMobile ? 'tabpanel' : undefined}
        aria-labelledby={isMobile ? 'tab-map' : undefined}
        inert={mapHidden ? true : undefined}
        className={clsx(
          'md:w-full md:h-full',
          'max-md:absolute max-md:inset-0',
          mapHidden && 'invisible',
        )}
      >
        <MapApiKeysContextProvider>
          <MapViewMode />
        </MapApiKeysContextProvider>
      </div>

      {showToggle && (
        <MapListToggle view={mobileView} onChange={setMobileView} />
      )}
    </div>
  );
}

export default function MapLayout() {
  return (
    <MapContextProvider>
      <ProjectLoader />
      <MapLayerProvider>
        <AnnotationProvider>
          <RasterSymbologyProvider>
            <MapLayoutContent />
          </RasterSymbologyProvider>
        </AnnotationProvider>
      </MapLayerProvider>
    </MapContextProvider>
  );
}
