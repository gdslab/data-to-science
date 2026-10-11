import { useMemo } from 'react';
import { createPortal } from 'react-dom';
import { useControl } from 'react-map-gl/maplibre';
import { FaCircleInfo } from 'react-icons/fa6';

type IdentifyControlProps = {
  active: boolean;
  disabled: boolean;
  onClick: () => void;
};

/**
 * A toggle button that sits directly below the map's NavigationControl zoom
 * buttons, styled to match the native 29×29 px maplibre control buttons.
 * When active the button highlights blue; when disabled it is muted.
 */
export default function IdentifyControl({
  active,
  disabled,
  onClick,
}: IdentifyControlProps) {
  // Create the maplibre ctrl DOM container once and register it as a control
  const container = useMemo(() => {
    const el = document.createElement('div');
    el.className = 'maplibregl-ctrl maplibregl-ctrl-group';
    el.style.overflow = 'hidden';
    return el;
  }, []);

  useControl(
    () => ({
      onAdd: () => container,
      onRemove: () => container.remove(),
    }),
    { position: 'top-right' }
  );

  // Portal a React-managed button into the maplibre ctrl container so we get
  // full React event handling while the button lives in the map's DOM hierarchy.
  return createPortal(
    <button
      type="button"
      title="Identify"
      disabled={disabled}
      onClick={onClick}
      style={{
        width: 29,
        height: 29,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: active ? 'var(--color-accent2)' : undefined,
        color: active ? '#ffffff' : '#333333',
        opacity: disabled ? 0.4 : undefined,
        cursor: disabled ? 'not-allowed' : 'pointer',
      }}
      className="border-0 outline-none transition-colors"
    >
      <FaCircleInfo className="w-3.5 h-3.5" />
    </button>,
    container
  );
}
