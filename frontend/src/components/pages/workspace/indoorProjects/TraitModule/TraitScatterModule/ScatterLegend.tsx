import { drawSymbol } from './SymbolRenderer';
import { useSymbolMapping } from './useSymbolMapping';
import { nivoColorSchemeMap } from '../nivoColorSchemeMap';

interface ScatterLegendProps {
  uniqueGroups: string[];
  colorOption: string;
}

export default function ScatterLegend({
  uniqueGroups,
  colorOption,
}: ScatterLegendProps) {
  const { getSymbolForSerie } = useSymbolMapping(uniqueGroups);

  return (
    <div className="bg-white p-3 rounded shadow-sm border">
      <div className="flex flex-col gap-2">
        {uniqueGroups.map((group, index) => {
          const symbol = getSymbolForSerie(group);
          // Use the same color scheme as the chart
          const colors = nivoColorSchemeMap[colorOption] || ['#000'];
          const color = colors[index % colors.length];
          return (
            <div key={group} className="flex items-center gap-2">
              <svg width="16" height="16" viewBox="0 0 16 16">
                {drawSymbol(symbol, 8, 8, 6, color, '#000')}
              </svg>
              <span className="text-sm">{group}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
