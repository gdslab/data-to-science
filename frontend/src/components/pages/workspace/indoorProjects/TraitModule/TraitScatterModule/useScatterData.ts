import { useMemo } from 'react';

import { IndoorProjectDataVizScatterAPIResponse } from '../../IndoorProject';

export function useScatterData(data: IndoorProjectDataVizScatterAPIResponse) {
  const scatterData = useMemo(() => {
    const grouped = data.results.reduce((acc, item) => {
      if (!acc[item.group])
        acc[item.group] = { id: item.group, data: [] as any[] };
      acc[item.group].data.push({
        x: item.x,
        y: item.y,
        id: item.id,
        interval_days: item.interval_days,
        group: item.group,
      });
      return acc;
    }, {} as Record<string, { id: string; data: any[] }>);
    return Object.values(grouped);
  }, [data.results]);

  const uniqueGroups = useMemo(
    () => [...new Set(data.results.map((d) => d.group))],
    [data.results]
  );

  return { scatterData, uniqueGroups };
}
