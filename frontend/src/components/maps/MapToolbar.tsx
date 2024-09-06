import { MapIcon, ScaleIcon } from '@heroicons/react/24/outline';

import { useMapContext } from './MapContext';

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

export default function MapToolbar() {
  const {
    activeMapTool,
    activeDataProductDispatch,
    activeMapToolDispatch,
    tileScaleDispatch,
  } = useMapContext();
  return (
    <fieldset className="border border-solid border-slate-300 p-1.5">
      <legend>Map Tools</legend>
      <div className="flex items-end justify-start gap-1.5">
        <div
          className={classNames(
            activeMapTool === 'map' ? 'bg-accent2' : '',
            'h-8 w-8 cursor-pointer shadow-sm hover:shadow-xl rounded border-2 border-solid border-slate-500 p-1.5'
          )}
          onClick={() => {
            activeDataProductDispatch({ type: 'clear', payload: null });
            activeMapToolDispatch({ type: 'set', payload: 'map' });
          }}
        >
          <MapIcon className="h-4 w-4" />
          <span className="sr-only">Map Tool</span>
        </div>
        <div
          className={classNames(
            activeMapTool === 'compare' ? 'bg-accent2' : '',
            'h-8 w-8 cursor-pointer shadow-sm hover:shadow-xl rounded border-2 border-solid border-slate-500 p-1.5'
          )}
          onClick={() => {
            activeDataProductDispatch({ type: 'clear', payload: null });
            activeMapToolDispatch({ type: 'set', payload: 'compare' });
          }}
        >
          <ScaleIcon className="h-4 w-4" />
          <span className="sr-only">Compare Tool</span>
        </div>
        <div className="mt-4">
          <input
            id="scale-checkbox"
            type="checkbox"
            name="scale"
            className="size-4 rounded text-accent2 border-gray-300"
            onChange={(e) => {
              tileScaleDispatch({
                type: 'set',
                payload: e.currentTarget.checked ? 4 : 2,
              });
            }}
          />
          <label
            htmlFor="scale-checkbox"
            className="ms-2 text-sm font-medium text-gray-900"
            title="Increases tile resolution from 512x512 to 1024x1024"
          >
            Increase tile resolution
          </label>
        </div>
      </div>
    </fieldset>
  );
}
