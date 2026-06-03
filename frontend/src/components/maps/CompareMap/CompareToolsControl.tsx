import clsx from 'clsx';

type CompareToolsControlProps = {
  showGrid: boolean;
  onToggleGrid: () => void;
  pointSyncActive: boolean;
  onTogglePointSync: () => void;
};

export default function CompareToolsControl({
  showGrid,
  onToggleGrid,
  pointSyncActive,
  onTogglePointSync,
}: CompareToolsControlProps) {
  return (
    <div
      className="flex gap-1"
    >
      <button
        type="button"
        onClick={onToggleGrid}
        className={clsx(
          'px-2 py-1 rounded-md font-semibold border-2 shadow-md transition-colors',
          showGrid
            ? 'bg-blue-600 border-blue-700 text-white'
            : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-100'
        )}
        title="Toggle grid overlay"
      >
        Grid
      </button>
      <button
        type="button"
        onClick={onTogglePointSync}
        className={clsx(
          'px-2 py-1 rounded-md font-semibold border-2 shadow-md transition-colors',
          pointSyncActive
            ? 'bg-blue-600 border-blue-700 text-white'
            : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-100'
        )}
        title="Toggle point sync tool"
      >
        Sync point
      </button>
    </div>
  );
}
