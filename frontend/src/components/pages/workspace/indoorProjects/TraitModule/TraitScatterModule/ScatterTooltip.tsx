import { titleCaseConversion } from '../../utils';
import { IndoorProjectDataVizScatterAPIResponse } from '../../IndoorProject';

interface ScatterTooltipProps {
  node: any;
  data: IndoorProjectDataVizScatterAPIResponse;
}

export default function ScatterTooltip({ node, data }: ScatterTooltipProps) {
  const xValue =
    typeof node.data.x === 'number' ? node.data.x.toFixed(2) : node.data.x;
  const yValue =
    typeof node.data.y === 'number' ? node.data.y.toFixed(2) : node.data.y;
  const intervalDays = (node.data as any).interval_days;

  return (
    <div
      style={{
        background: 'white',
        padding: '12px 16px',
        border: '1px solid #ccc',
        borderRadius: '4px',
        fontSize: '14px',
      }}
    >
      <strong>{node.serieId}</strong>
      <br />
      {titleCaseConversion(data.traits.x)}: {xValue}
      <br />
      {titleCaseConversion(data.traits.y)}: {yValue}
      <br />
      Days after planting: {intervalDays}
    </div>
  );
}
