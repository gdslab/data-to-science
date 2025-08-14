import { SymbolKind } from './types';

const trianglePath = (cx: number, cy: number, r: number) =>
  `M ${cx} ${cy - r} L ${cx - r} ${cy + r} L ${cx + r} ${cy + r} Z`;

const diamondPath = (cx: number, cy: number, r: number) =>
  `M ${cx} ${cy - r} L ${cx + r} ${cy} L ${cx} ${cy + r} L ${cx - r} ${cy} Z`;

export function drawSymbol(
  symbol: SymbolKind,
  cx: number,
  cy: number,
  r: number,
  fill: string,
  stroke: string
) {
  switch (symbol) {
    case 'circle':
      return (
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill={fill}
          stroke={stroke}
          strokeWidth={1.5}
        />
      );
    case 'square':
      return (
        <rect
          x={cx - r}
          y={cy - r}
          width={2 * r}
          height={2 * r}
          fill={fill}
          stroke={stroke}
          strokeWidth={1.5}
        />
      );
    case 'triangle':
      return (
        <path
          d={trianglePath(cx, cy, r)}
          fill={fill}
          stroke={stroke}
          strokeWidth={1.5}
        />
      );
    case 'diamond':
      return (
        <path
          d={diamondPath(cx, cy, r)}
          fill={fill}
          stroke={stroke}
          strokeWidth={1.5}
        />
      );
    case 'cross':
      return (
        <g stroke={stroke} strokeWidth={1.5}>
          <line x1={cx - r} y1={cy} x2={cx + r} y2={cy} />
          <line x1={cx} y1={cy - r} x2={cx} y2={cy + r} />
          <circle cx={cx} cy={cy} r={r * 0.6} fill={fill} stroke="none" />
        </g>
      );
  }
}
