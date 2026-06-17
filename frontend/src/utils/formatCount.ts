// Compact number formatting for engagement metrics.
// 124 -> "124", 3200 -> "3.2k", 8700 -> "8.7k"
export const formatCount = (n: number): string =>
  n >= 1000 ? `${(n / 1000).toFixed(1).replace(/\.0$/, '')}k` : `${n}`;
