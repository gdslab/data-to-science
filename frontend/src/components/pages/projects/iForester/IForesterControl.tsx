import { useEffect, useState } from 'react';
import { useMap } from 'react-leaflet/hooks';

import Control from './CustomControl';
import filterIcon from './filter-icon.png';
import FilterOptions from './FilterOptions';

function IForesterControl({ position }: { position: L.ControlPosition }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const map = useMap();

  useEffect(() => {
    // disable major map events when control is expanded
    if (isExpanded) {
      map.dragging.disable();
      map.doubleClickZoom.disable();
      map.scrollWheelZoom.disable();
    } else {
      map.dragging.enable();
      map.doubleClickZoom.enable();
      map.scrollWheelZoom.enable();
    }
  }, [isExpanded]);

  return (
    <Control prepend position={position}>
      <div className="bg-white bg-clip-padding border-2 border-solid border-black/20 rounded">
        {!isExpanded && (
          <button
            type="button"
            className="h-11 w-11 bg-no-repeat bg-center"
            style={{
              backgroundImage: `url(${filterIcon})`,
              backgroundSize: '26px 26px',
            }}
            onMouseOver={() => {
              setIsExpanded(true);
            }}
          />
        )}
        {isExpanded && (
          <div className="absolute -left-10 bg-white bg-clip-padding border-left-2 border-top-2 border-bottom-2 border-solid border-black/20 rounded-left rounded-top rounded-bottom">
            <button
              type="button"
              className="h-11 w-11 bg-no-repeat bg-center"
              style={{
                backgroundImage: `url(${filterIcon})`,
                backgroundSize: '26px 26px',
              }}
              onClick={() => {
                setIsExpanded(false);
              }}
            />
          </div>
        )}
        {isExpanded && <FilterOptions />}
      </div>
    </Control>
  );
}

export default IForesterControl;
