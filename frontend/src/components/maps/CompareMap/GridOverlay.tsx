const GRID_CELL_PX = 200;

type GridOverlayProps = {
  style: React.CSSProperties;
  side: 'left' | 'right';
};

export default function GridOverlay({ style, side }: GridOverlayProps) {
  const patternId = `compare-grid-${side}`;
  return (
    <div
      style={{
        ...style,
        borderRight: 'none',
        zIndex: 999,
        pointerEvents: 'none',
      }}
    >
      <svg width="100%" height="100%">
        <defs>
          <pattern
            id={patternId}
            patternUnits="userSpaceOnUse"
            width={GRID_CELL_PX}
            height={GRID_CELL_PX}
          >
            <path
              d={`M ${GRID_CELL_PX} 0 L 0 0 0 ${GRID_CELL_PX}`}
              fill="none"
              stroke="#ffffff"
              strokeOpacity={0.4}
              strokeWidth={2}
              strokeDasharray="4 4"
            />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill={`url(#${patternId})`} />
      </svg>
    </div>
  );
}
