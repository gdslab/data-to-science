import clsx from 'clsx';
import { useState } from 'react';

import filterIcon from './filter-icon.png';
import FilterOptions from './FilterOptions';

function IForesterControl() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div
      className={clsx(
        'absolute top-28 right-2 bg-white bg-clip-padding border-2 border-solid border-black/20 rounded',
        !isExpanded && 'w-11 h-11',
        isExpanded && 'w-auto h-auto'
      )}
    >
      {!isExpanded && (
        <button
          type="button"
          className="h-full w-full bg-no-repeat bg-center"
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
  );
}

export default IForesterControl;
