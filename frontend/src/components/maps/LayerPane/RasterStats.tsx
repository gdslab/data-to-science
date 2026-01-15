import { Band } from '../../pages/workspace/projects/Project';

export default function RasterStats({ stats }: { stats: Band['stats'] }) {
  return (
    <fieldset className="border border-solid border-slate-300 p-2">
      <legend className="block text-sm text-gray-400 font-semibold pt-1 pb-1">
        Stats
      </legend>
      <div className="flex flex-row flex-wrap justify-between gap-1.5">
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
