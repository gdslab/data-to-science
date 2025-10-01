import { useMemo, useState } from 'react';
import { ResponsiveScatterPlot, ScatterPlotNodeProps } from '@nivo/scatterplot';

import ColorMapSelect from '../ColorMapSelect';
import { IndoorProjectDataVizScatterAPIResponse } from '../../IndoorProject';
import { titleCaseConversion, nivoCategoricalColors } from '../../utils';

import { useScatterData } from './useScatterData';
import { useSymbolMapping } from './useSymbolMapping';
import { drawSymbol } from './SymbolRenderer';
import ScatterLegend from './ScatterLegend';
import ScatterTooltip from './ScatterTooltip';

function makeNodeComponent(getSymbolForSerie: (serieId: string) => string) {
  return function SymbolNode(props: ScatterPlotNodeProps<any>) {
    const {
      node,
      style,
      blendMode,
      onMouseEnter,
      onMouseMove,
      onMouseLeave,
      onClick,
    } = props;
    const cx = style.x.get();
    const cy = style.y.get();
    const r = (style.size.get() ?? 8) / 2;
    const stroke = '#333'; // Use a default border color or derive from theme
    const fill = style.color.get();
    const symbol = getSymbolForSerie(String(node.serieId)) as any;

    return (
      <g
        style={{ mixBlendMode: blendMode }}
        onMouseEnter={onMouseEnter ? (e) => onMouseEnter(node, e) : undefined}
        onMouseMove={onMouseMove ? (e) => onMouseMove(node, e) : undefined}
        onMouseLeave={onMouseLeave ? (e) => onMouseLeave(node, e) : undefined}
        onClick={onClick ? (e) => onClick(node, e) : undefined}
      >
        {drawSymbol(symbol, cx, cy, r, fill, stroke)}
      </g>
    );
  };
}

export default function TraitScatterModuleDataVisualization({
  data,
}: {
  data: IndoorProjectDataVizScatterAPIResponse;
}) {
  const [colorOption, setColorOption] = useState('paired');

  const { scatterData, uniqueGroups } = useScatterData(data);
  const { getSymbolForSerie } = useSymbolMapping(uniqueGroups);

  const NodeWithSymbols = useMemo(
    () => makeNodeComponent(getSymbolForSerie),
    [getSymbolForSerie]
  );

  const pairedColorOption = nivoCategoricalColors.find(
    (option) => option.value === 'paired'
  );

  return (
    <div className="bg-white p-4">
      {scatterData.length > 0 && (
        <div className="h-[400px] p-4 relative">
          <ResponsiveScatterPlot
            data={scatterData}
            margin={{ top: 20, right: 20, bottom: 60, left: 90 }}
            xScale={{ type: 'linear', min: 'auto', max: 'auto' }}
            yScale={{ type: 'linear', min: 'auto', max: 'auto' }}
            colors={{ scheme: colorOption as any }}
            nodeSize={8}
            nodeComponent={NodeWithSymbols}
            blendMode="normal"
            axisTop={null}
            axisRight={null}
            axisBottom={{
              tickSize: 5,
              tickPadding: 5,
              tickRotation: 0,
              legend: titleCaseConversion(data.traits.x),
              legendOffset: 46,
              legendPosition: 'middle',
            }}
            axisLeft={{
              tickSize: 5,
              tickPadding: 5,
              tickRotation: 0,
              legend: titleCaseConversion(data.traits.y),
              legendOffset: -75,
              legendPosition: 'middle',
            }}
            theme={{
              text: { fontSize: 14 },
              legends: {
                text: { fontSize: 14, fontFamily: 'inherit', fill: '#333333' },
              },
              axis: {
                legend: { text: { fontSize: 16, fontWeight: 500 } },
                ticks: { text: { fontSize: 14 } },
              },
            }}
            legends={[]}
            animate
            motionConfig="gentle"
            tooltip={({ node }) => <ScatterTooltip node={node} data={data} />}
            role="application"
            ariaLabel="Scatter plot showing relationship between two traits"
          />
        </div>
      )}
      <div className="w-full flex justify-between">
        <div className="w-96">
          <ColorMapSelect
            colorPreviewCount={uniqueGroups.length}
            setColorOption={setColorOption}
            defaultValue={pairedColorOption}
            categoricalOnly
          />
        </div>
        <ScatterLegend uniqueGroups={uniqueGroups} colorOption={colorOption} />
      </div>
    </div>
  );
}
