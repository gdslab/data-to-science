import { useState } from 'react';

import LayerPane from './LayerPane';

import { MapContextProvider } from './MapContext';
import { MapLayerProvider } from './MapLayersContext';
import MaplibreMap from './MaplibreMap';

function classNames(...classes: [string, string]) {
  return classes.filter(Boolean).join(' ');
}

export default function MapLayout() {
  const [hidePane, toggleHidePane] = useState(false);

  return (
    <MapContextProvider>
      <MapLayerProvider>
        {/* sidebar */}
        <div className="flex flex-row h-full">
          <div
            className={classNames(
              hidePane ? 'w-[48px]' : 'w-[450px]',
              'shrink-0 bg-slate-100'
            )}
          >
            <LayerPane hidePane={hidePane} toggleHidePane={toggleHidePane} />
          </div>
          {/* page content */}
          <div className="w-full">
            <MaplibreMap />
            {/* <Map layerPaneHidden={hidePane} /> */}
          </div>
        </div>
      </MapLayerProvider>
    </MapContextProvider>
  );
}
