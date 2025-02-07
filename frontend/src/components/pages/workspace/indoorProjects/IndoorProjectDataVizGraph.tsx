import { useMemo } from 'react';

import {
  IndoorProjectDataVizAPIResponse,
  IndoorProjectDataVizRecord,
} from './IndoorProject';

import { getTextColor, hsvToHex } from './utils';

export default function IndoorProjectDataVizGraph({
  data,
}: {
  data: IndoorProjectDataVizAPIResponse;
}) {
  const result: IndoorProjectDataVizRecord[][] = useMemo(() => {
    const groupedData = data.results.reduce((acc, item) => {
      const { group } = item;
      if (!acc[group]) {
        acc[group] = [];
      }
      acc[group].push(item);
      return acc;
    }, {});

    return Object.values(groupedData);
  }, []);

  return (
    <div className="max-h-96 flex flex-col gap-4 py-4 border-2 border-gray-300 bg-white rounded-md overflow-auto">
      {result.map((group, i) => (
        <div key={i} className="min-w-max px-4">
          <span className="text-lg font-bold">{group[0].group}</span>
          <div className="flex justify-between gap-2">
            {group
              .sort((a, b) => a.interval_days - b.interval_days)
              .map((record, j) => (
                <div
                  key={j}
                  className={`min-w-44 w-44 p-2.5 flex flex-col border-2 border-gray-300 shadow-md ${getTextColor(
                    record.hue,
                    record.saturation,
                    record.intensity
                  )}`}
                  style={{
                    backgroundColor: hsvToHex(
                      record.hue,
                      record.saturation,
                      record.intensity
                    ),
                  }}
                  title={`H: ${record.hue?.toFixed(
                    2
                  )}, S: ${record.saturation?.toFixed(
                    2
                  )}, V: ${record.intensity?.toFixed(2)}`}
                />
              ))}
          </div>
        </div>
      ))}
      <div className="min-w-max px-4">
        <div className="flex justify-between gap-2">
          {result?.[0].map((record) => (
            <div
              key={`interval-${record.interval_days}`}
              className="relative min-w-44 w-44 p-2.5 flex flex-col text-center text-lg font-bold"
            >
              {/* Tick mark */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-2 h-3 w-0.5 bg-black"></div>
              {record.interval_days}
            </div>
          ))}
        </div>
        <div className="text-center font-semibold">Days after planting</div>
      </div>
    </div>
  );
}
