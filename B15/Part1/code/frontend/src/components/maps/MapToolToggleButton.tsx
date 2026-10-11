import { type ComponentPropsWithoutRef } from 'react';

interface MapToolToggleButtonProps extends Omit<
  ComponentPropsWithoutRef<'button'>,
  'className' | 'type'
> {
  active: boolean;
}

export default function MapToolToggleButton({
  active,
  children,
  ...props
}: MapToolToggleButtonProps) {
  return (
    <button
      type="button"
      className={`relative z-10 h-12 w-12 border-0 rounded-md shadow-md flex items-center justify-center focus:outline-hidden focus:ring-2 focus:ring-accent2 transition-colors pointer-events-auto ${
        active
          ? 'bg-accent2 text-white'
          : 'bg-white text-slate-600 hover:text-slate-800 hover:bg-slate-50'
      }`}
      {...props}
    >
      {children}
    </button>
  );
}
