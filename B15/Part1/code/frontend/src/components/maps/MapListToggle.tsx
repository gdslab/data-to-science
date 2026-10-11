import { ListBulletIcon, MapIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

type View = 'map' | 'list';

type MapListToggleProps = {
  view: View;
  onChange: (view: View) => void;
};

const tabs: { value: View; label: string; Icon: React.FC<React.SVGProps<SVGSVGElement>> }[] = [
  { value: 'list', label: 'List', Icon: ListBulletIcon },
  { value: 'map', label: 'Map', Icon: MapIcon },
];

export default function MapListToggle({ view, onChange }: MapListToggleProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      onChange(view === 'list' ? 'map' : 'list');
    }
  };

  return (
    <div
      role="tablist"
      aria-label="View mode"
      onKeyDown={handleKeyDown}
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex rounded-full shadow-lg overflow-hidden"
      style={{ marginBottom: 'env(safe-area-inset-bottom)' }}
    >
      {tabs.map(({ value, label, Icon }) => {
        const isActive = view === value;
        return (
          <button
            key={value}
            id={`tab-${value}`}
            role="tab"
            aria-selected={isActive}
            aria-controls={`panel-${value}`}
            tabIndex={isActive ? 0 : -1}
            onClick={() => onChange(value)}
            className={clsx(
              'flex items-center gap-2 px-5 h-11 text-sm font-semibold motion-safe:transition-colors motion-safe:duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent2',
              isActive
                ? 'bg-accent2 text-white'
                : 'bg-white text-slate-700 hover:bg-slate-50',
            )}
          >
            <Icon className="h-5 w-5" aria-hidden="true" />
            {label}
          </button>
        );
      })}
    </div>
  );
}
