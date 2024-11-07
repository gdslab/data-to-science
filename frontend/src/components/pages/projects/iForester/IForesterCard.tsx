import clsx from 'clsx';
import { useState } from 'react';
import {
  MagnifyingGlassPlusIcon,
  Square3Stack3DIcon,
} from '@heroicons/react/24/outline';

import { useIForesterControlContext } from './IForesterContext';
import { IForester } from '../Project';

const PropertyLabel = ({ children }) => (
  <span className="text-xs font-semibold">{children}</span>
);

const PropertyValue = ({ children }) => <span className="text-xs">{children}</span>;

export default function IForesterCard({ submission }: { submission: IForester }) {
  const [depthViewVisible, setDepthViewVisible] = useState(false);

  const { dispatch, state } = useIForesterControlContext();

  function flipImage() {
    setDepthViewVisible(!depthViewVisible);
  }

  function zoomTo(id: string) {
    dispatch({ type: 'SET_ACTIVE_MARKER_ZOOM', payload: id });
  }

  return (
    <div
      className={clsx(
        'p-1.5 h-[292px] w-44 flex flex-col gap-1.5 rounded-md drop-shadow-md border-2',
        {
          'bg-white/90 border-white/0': state.activeMarker !== submission.id,
          'bg-white border-[#6381C7]': state.activeMarker === submission.id,
        }
      )}
      onMouseEnter={() =>
        dispatch({ type: 'SET_ACTIVE_MARKER', payload: submission.id })
      }
      onMouseLeave={() => dispatch({ type: 'SET_ACTIVE_MARKER', payload: '' })}
    >
      <div>
        <span className="font-semibold text-xs">
          {`${new Date(submission.timeStamp).toLocaleDateString()} ${new Date(
            submission.timeStamp
          ).toLocaleTimeString()}`}
        </span>
      </div>
      <div className="relative h-40 w-40 flex items-center justify-between gap-4">
        <div
          className={clsx(
            'absolute w-full h-full transition-transform duration-500 ease-in-out',
            {
              '[transform:rotateY(180deg)] [backface-visibility:hidden]':
                depthViewVisible,
              '': !depthViewVisible,
            }
          )}
        >
          <img src={submission.imageFile} className="object-cover h-40 w-40" />
        </div>
        <div
          className={clsx(
            'absolute w-full h-full transition-transform duration-500 ease-in-out',
            {
              '': depthViewVisible,
              '[transform:rotateY(180deg)] [backface-visibility:hidden]':
                !depthViewVisible,
            }
          )}
        >
          <img src={submission.depthFile} className="object-cover h-40 w-40" />
        </div>
        <div className="absolute bottom-0 left-0 h-6 w-6 bg-white/80 p-1">
          <button
            className="text-slate-600 hover:text-slate-800"
            aria-label="Zoom to on map"
            onClick={() => zoomTo(submission.id)}
          >
            <MagnifyingGlassPlusIcon className="h-4 w-4" />
          </button>
        </div>
        <div className="absolute bottom-0 right-0 flex items-center justify-center h-6 w-6 bg-white/80 p-1">
          <button
            className="h-4 w-4 text-slate-600 hover:text-slate-800"
            aria-label={!depthViewVisible ? 'View Depth Image' : 'View RGB Image'}
            onClick={flipImage}
          >
            <Square3Stack3DIcon className="h-4 w-4" />
          </button>
        </div>
      </div>
      <div className="grid grid-cols-2">
        <PropertyLabel>DBH</PropertyLabel>
        <PropertyValue>{submission.dbh.toFixed(3)}</PropertyValue>
        <PropertyLabel>Distance</PropertyLabel>
        <PropertyValue>{submission.distance.toFixed(3)}</PropertyValue>
        <PropertyLabel>Height</PropertyLabel>
        <PropertyValue>Unknown</PropertyValue>
        <PropertyLabel>Species</PropertyLabel>
        <PropertyValue>{submission.species}</PropertyValue>
        <PropertyLabel>Grade</PropertyLabel>
        <PropertyValue>Unknown</PropertyValue>
      </div>
    </div>
  );
}
