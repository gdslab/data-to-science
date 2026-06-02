import { Band } from '../../pages/workspace/projects/Project';

export default function RasterStats({ stats }: { stats: Band['stats'] }) {
  return (
    <fieldset className="border border-solid border-slate-300 p-2">
      <legend className="block text-sm text-gray-400 font-semibold pt-1 pb-1">
        Stats
      </legend>
      <div className="grid grid-cols-2 gap-2 md:flex md:flex-row md:flex-wrap md:justify-between md:gap-1.5">
        <div className="flex flex-col">
          <span className="font-semibold">Mean</span>
          <span>{stats.mean.toFixed(2)}</span>
        </div>
        <div className="flex flex-col">
          <span className="font-semibold">Min</span>
          <span>{stats.minimum.toFixed(2)}</span>
        </div>
        <div className="flex flex-col">
          <span className="font-semibold">Max</span>
          <span>{stats.maximum.toFixed(2)}</span>
        </div>
        <div className="flex flex-col">
          <span className="font-semibold">Std. Dev</span>
          <span>{stats.stddev.toFixed(2)}</span>
        </div>
      </div>
    </fieldset>
  );
}
