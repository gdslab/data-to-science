import { IndoorProjectDataVizAPIResponse } from '../IndoorProject';
import { downloadCSV } from '../utils';

export const downloadPotGroupCSV = (
  data: IndoorProjectDataVizAPIResponse,
  filename: string = `pot-group-data-${new Date()
    .toISOString()
    .slice(0, 10)}.csv`
) => {
  const headers = ['Group', 'DAP', 'Hue', 'Saturation', 'Value'];
  const rows = data.results
    .slice()
    .sort(
      (a, b) =>
        a.group.localeCompare(b.group) || a.interval_days - b.interval_days
    )
    .map((record) => [
      record.group,
      record.interval_days,
      record.hue,
      record.saturation,
      record.intensity,
    ]);

  downloadCSV(filename, headers, rows);
};
