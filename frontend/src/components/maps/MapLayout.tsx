import { useState } from 'react';

import LayerPane from './LayerPane';

import { MapContextProvider } from './MapContext';
import { MapApiKeysContextProvider } from './MapApiKeysContext';
import { MapLayerProvider } from './MapLayersContext';
import MapViewMode from './MapViewMode';
import ProjectLoader from './ProjectLoader';
import { RasterSymbologyProvider } from './RasterSymbologyContext';

function classNames(...classes: [string, string]) {
  return classes.filter(Boolean).join(' ');
}

export default function MapLayout() {
  const [hidePane, toggleHidePane] = useState(false);

  return (
    <MapApiKeysContextProvider>
      <MapContextProvider>
        <ProjectLoader />
        <MapLayerProvider>
          <RasterSymbologyProvider>
            {/* sidebar */}
            <div className="flex flex-row h-full">
              <div
                className={classNames(
                  hidePane ? 'w-[48px]' : 'w-[450px]',
                  'shrink-0 bg-slate-100'
                )}
              >
                <LayerPane
                  hidePane={hidePane}
                  toggleHidePane={toggleHidePane}
                />
              </div>
              {/* page content */}
              <div className="w-full h-full">
                <MapViewMode />
              </div>
            </div>
          </RasterSymbologyProvider>
        </MapLayerProvider>
      </MapContextProvider>
    </MapApiKeysContextProvider>
  );
}
