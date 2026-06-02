import clsx from 'clsx';
import { useEffect, useState } from 'react';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

import { useIsMobile } from '../hooks';
import LayerPane from './LayerPane';
import MapListToggle from './MapListToggle';
import { MobileViewProvider } from './MobileViewContext';

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
    activeDataProductDispatch,
    activeMapTool,
    activeMapToolDispatch,
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

  // Auto-switch to map panel when a full-screen viewer activates on mobile
  useEffect(() => {
    if (!isMobile) return;
    if (isFullScreenViewer) setMobileView('map');
  }, [isMobile, isFullScreenViewer]);

  // Auto-switch when point cloud is activated in map mode (no in-list controls to stay for)
  const isPointCloudMapMode =
    activeDataProduct?.data_type === 'point_cloud' && pointCloudViewer === 'map';

  useEffect(() => {
    if (!isMobile) return;
    if (isPointCloudMapMode) setMobileView('map');
  }, [isMobile, isPointCloudMapMode]);

  const handleExitFullScreenViewer = () => {
    activeDataProductDispatch({ type: 'clear', payload: null });
    if (activeMapTool === 'compare') {
      activeMapToolDispatch({ type: 'set', payload: 'map' });
    }
    setMobileView('list');
  };

  // Hide toggle for full-screen viewers that have no meaningful list to switch to
  const showToggle = isMobile && !isFullScreenViewer;

  const listHidden = isMobile && mobileView !== 'list';
  const mapHidden = isMobile && mobileView !== 'map';

  return (
    <MobileViewProvider value={{ setMobileView }}>
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

      {isMobile && isFullScreenViewer && (
        <button
          type="button"
          onClick={handleExitFullScreenViewer}
          aria-label="Exit viewer and return to list"
          className="fixed bottom-6 right-3 z-[60] h-11 w-11 flex items-center justify-center rounded-full bg-white shadow-lg text-slate-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent2"
          style={{ marginBottom: 'env(safe-area-inset-bottom)' }}
        >
          <ArrowLeftIcon className="h-5 w-5" />
        </button>
      )}
    </div>
    </MobileViewProvider>
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
