export type SymbolKind = 'circle' | 'square' | 'triangle' | 'diamond' | 'cross';

export interface ScatterDataPoint {
  x: number;
  y: number;
  id: string;
  interval_days: number;
  group: string;
}

export interface ScatterSeries {
  id: string;
  data: ScatterDataPoint[];
}
