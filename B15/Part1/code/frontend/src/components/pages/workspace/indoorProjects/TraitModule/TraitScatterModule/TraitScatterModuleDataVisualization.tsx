import { useMemo, useState } from 'react';
import { ResponsiveScatterPlot, ScatterPlotNodeProps } from '@nivo/scatterplot';
import { ColorSchemeId } from '@nivo/colors';
import { animated } from '@react-spring/web';

import ColorMapSelect from '../ColorMapSelect';
import { IndoorProjectDataVizScatterAPIResponse } from '../../IndoorProject';
import { titleCaseConversion, nivoCategoricalColors } from '../../utils';

import { useScatterData } from './useScatterData';
import { useSymbolMapping } from './useSymbolMapping';
import ScatterLegend from './ScatterLegend';
import ScatterTooltip from './ScatterTooltip';
import { ScatterDataPoint, SymbolKind } from './types';

function makeNodeComponent(getSymbolForSerie: (serieId: string) => SymbolKind) {
  return function SymbolNode(props: ScatterPlotNodeProps<ScatterDataPoint>) {
    const {
      node,
      style,
      blendMode,
      onMouseEnter,
      onMouseMove,
      onMouseLeave,
      onClick,
    } = props;
    const symbol = getSymbolForSerie(String(node.serieId));
    const stroke = '#333';

    // Extract static values for position/size (these don't change during color transitions)
    const cx = style.x.get();
    const cy = style.y.get();
    const r = (style.size.get() ?? 8) / 2;

    const renderSymbol = () => {
      switch (symbol) {
        case 'circle':
          return (
            <animated.circle
              cx={cx}
              cy={cy}
              r={r}
              fill={style.color}
              stroke={stroke}
              strokeWidth={1.5}
            />
          );
        case 'square':
          return (
            <animated.rect
              x={cx - r}
              y={cy - r}
              width={2 * r}
              height={2 * r}
              fill={style.color}
              stroke={stroke}
              strokeWidth={1.5}
            />
          );
        case 'triangle':
          return (
            <animated.path
              d={`M ${cx} ${cy - r} L ${cx - r} ${cy + r} L ${cx + r} ${
                cy + r
              } Z`}
              fill={style.color}
              stroke={stroke}
              strokeWidth={1.5}
            />
          );
        case 'diamond':
          return (
            <animated.path
              d={`M ${cx} ${cy - r} L ${cx + r} ${cy} L ${cx} ${cy + r} L ${
                cx - r
              } ${cy} Z`}
              fill={style.color}
              stroke={stroke}
              strokeWidth={1.5}
            />
          );
        case 'cross':
          return (
            <g stroke={stroke} strokeWidth={1.5}>
              <line x1={cx - r} y1={cy} x2={cx + r} y2={cy} />
              <line x1={cx} y1={cy - r} x2={cx} y2={cy + r} />
              <animated.circle
                cx={cx}
                cy={cy}
                r={r * 0.6}
                fill={style.color}
                stroke="none"
              />
            </g>
          );
      }
    };

    return (
      <g
        style={{ mixBlendMode: blendMode }}
        onMouseEnter={onMouseEnter ? (e) => onMouseEnter(node, e) : undefined}
        onMouseMove={onMouseMove ? (e) => onMouseMove(node, e) : undefined}
        onMouseLeave={onMouseLeave ? (e) => onMouseLeave(node, e) : undefined}
        onClick={onClick ? (e) => onClick(node, e) : undefined}
      >
        {renderSymbol()}
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
            colors={{ scheme: colorOption as ColorSchemeId }}
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
