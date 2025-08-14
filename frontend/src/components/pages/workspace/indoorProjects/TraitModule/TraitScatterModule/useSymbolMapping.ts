import { useMemo } from 'react';
import { SymbolKind } from './types';

export function useSymbolMapping(uniqueGroups: string[]) {
  const symbolChoices: SymbolKind[] = [
    'circle',
    'square',
    'triangle',
    'diamond',
    'cross',
  ];

  const symbolMap = useMemo(() => {
    const m: Record<string, SymbolKind> = {};
    uniqueGroups.forEach((g, i) => {
      m[g] = symbolChoices[i % symbolChoices.length];
    });
    return m;
  }, [uniqueGroups]);

  const getSymbolForSerie = (serieId: string) => symbolMap[serieId] ?? 'circle';

  return { symbolMap, getSymbolForSerie };
}
