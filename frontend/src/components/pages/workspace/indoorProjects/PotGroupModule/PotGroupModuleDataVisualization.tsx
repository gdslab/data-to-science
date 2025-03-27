import chroma from 'chroma-js';
import { useMemo } from 'react';
import { Popover, PopoverButton, PopoverPanel } from '@headlessui/react';

import {
  IndoorProjectDataVizAPIResponse,
  IndoorProjectDataVizRecord,
} from '../IndoorProject';

import { getTextColor } from '../utils';

export default function PotGroupModuleDataVisualization({
  data,
  images,
}: {
  data: IndoorProjectDataVizAPIResponse;
  images?: Record<string, string[]>;
}) {
  const result = useMemo(() => {
    const grouped = data.results.reduce((acc, item) => {
      (acc[item.group] ??= []).push(item);
      return acc;
    }, {} as Record<string, IndoorProjectDataVizRecord[]>);
    return Object.values(grouped);
  }, [data]);

  const getColor = (record: IndoorProjectDataVizRecord) =>
    chroma
      .hsv(
        record.hue,
        record.saturation ? record.saturation / 100 : 0,
        record.intensity ? record.intensity / 100 : 0
      )
      .hex();

  const getFilename = (url: string) => url.split('/').pop() || url;

  return (
    <div className="relative max-h-96 flex flex-col gap-1.5 py-4 border-2 border-gray-300 bg-white rounded-md overflow-auto">
      {result.map((group, i) => (
        <div key={i} className="flex items-center px-4 gap-4">
          <span className="truncate w-32">{group[0].group}</span>
          <div className="flex justify-between gap-0.5">
            {group
              .sort((a, b) => a.interval_days - b.interval_days)
              .map((record, j) => {
                return (
                  <Popover key={j} className="relative">
                    <PopoverButton
                      className={`w-28 h-8 p-2.5 flex flex-col ${getTextColor(
                        record.hue,
                        record.saturation,
                        record.intensity
                      )}`}
                      style={{ backgroundColor: getColor(record) }}
                    />
                    <PopoverPanel className="fixed z-50 bg-white rounded-lg shadow-lg p-2">
                      <div className="text-sm mb-2">
                        {record.interval_days} days after planting
                      </div>
                      {images &&
                        images[record.interval_days] &&
                        (images[record.interval_days].length === 1 ? (
                          <img
                            src={images[record.interval_days][0]}
                            alt={`Plant at ${record.interval_days} days`}
                            className="max-w-xl max-h-xl rounded"
                            title={getFilename(images[record.interval_days][0])}
                          />
                        ) : (
                          <div className="grid grid-cols-4 gap-2">
                            {images[record.interval_days].map(
                              (image, index) => (
                                <img
                                  key={index}
                                  src={image}
                                  alt={`Plant at ${
                                    record.interval_days
                                  } days - Image ${index + 1}`}
                                  className="w-48 h-48 object-cover rounded"
                                  title={getFilename(image)}
                                />
                              )
                            )}
                          </div>
                        ))}
                    </PopoverPanel>
                  </Popover>
                );
              })}
          </div>
        </div>
      ))}
      <div className="min-w-max flex items-center px-4 py-4">
        <div className="flex justify-between gap-0.5">
          <div className="relative w-36 p-2.5 flex flex-col text-center" />
          {result[0]?.map(({ interval_days }) => (
            <div
              key={`interval-${interval_days}`}
              className="relative w-28 p-2.5 flex flex-col text-center"
            >
              {/* Tick mark */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-2 h-3 w-0.5 bg-black" />
              {interval_days}
            </div>
          ))}
        </div>
        <div className="text-center">Days after planting</div>
      </div>
    </div>
  );
}
