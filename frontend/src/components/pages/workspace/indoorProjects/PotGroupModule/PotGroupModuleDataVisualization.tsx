import chroma from 'chroma-js';
import { useMemo } from 'react';
import { Popover, PopoverButton, PopoverPanel } from '@headlessui/react';
import { ArrowPathIcon } from '@heroicons/react/24/solid';

import {
  IndoorProjectDataVizAPIResponse,
  IndoorProjectDataVizRecord,
} from '../IndoorProject';
import { useIndoorProjectContext } from '../IndoorProjectContext';

import { getNormalizedAndStretchedValues, getTextColor } from '../utils';
import ImageSequenceSlider from './ImageSequenceSlider';
import { downloadPotGroupCSV } from './csv';
// import { InformationCircleIcon } from '@heroicons/react/24/solid';

export default function PotGroupModuleDataVisualization({
  data,
  images,
}: {
  data: IndoorProjectDataVizAPIResponse;
  images?: Record<string, string[]>;
}) {
  const {
    state: { selectedDAP },
    dispatch,
  } = useIndoorProjectContext();

  console.log('selectedDAP in PotGroupModuleDataVisualization', selectedDAP);

  const result = useMemo(() => {
    const grouped = data.results.reduce((acc, item) => {
      (acc[item.group] ??= []).push(item);
      return acc;
    }, {} as Record<string, IndoorProjectDataVizRecord[]>);
    return Object.values(grouped);
  }, [data]);

  const getColor = (
    hue: number | null,
    saturation: number | null,
    intensity: number | null
  ) => {
    if (hue === null || saturation === null || intensity === null) {
      return 'transparent';
    }
    return chroma.hsv(hue, saturation, intensity).hex();
  };

  const getFilename = (url: string) => url.split('/').pop() || url;

  const handleDownloadCSV = () => downloadPotGroupCSV(data);

  return (
    <div className="relative max-h-96 flex flex-col gap-1.5 py-4 border-2 border-gray-300 bg-white rounded-md overflow-auto">
      {result.map((group, i) => {
        const { stretchedSValues, stretchedVValues } =
          getNormalizedAndStretchedValues(group.map((g) => [g]));
        return (
          <div key={i} className="flex items-center px-4 gap-4">
            <span className="truncate w-32" title={group[0].group}>
              {group[0].group}
            </span>
            {/* <InformationCircleIcon
              className="w-4 h-4 text-sky-600"
              title={group[0].group}
            /> */}
            <div className="flex justify-between gap-0.5">
              {group
                .sort((a, b) => a.interval_days - b.interval_days)
                .map((record, j) => {
                  const stretchedS = stretchedSValues[j];
                  const stretchedV = stretchedVValues[j];
                  return (
                    <Popover key={j} className="relative">
                      <PopoverButton
                        className={`w-28 h-8 flex justify-center items-center relative ${getTextColor(
                          record.hue,
                          stretchedS,
                          stretchedV
                        )} ${
                          record.interval_days === selectedDAP
                            ? 'transform shadow-lg'
                            : ''
                        }`}
                        style={{
                          backgroundColor: getColor(
                            record.hue,
                            stretchedS,
                            stretchedV
                          ),
                          border:
                            record.interval_days === selectedDAP
                              ? '2px solid salmon'
                              : '2px solid transparent',
                        }}
                        onClick={() => {
                          dispatch({
                            type: 'SET_SELECTED_DAP',
                            payload: record.interval_days,
                          });
                        }}
                        title={`H: ${record.hue?.toFixed(
                          2
                        )}, S: ${record.saturation?.toFixed(
                          2
                        )}, V: ${record.intensity?.toFixed(2)}`}
                      >
                        {images && images[record.interval_days].length > 1 && (
                          <div
                            className={`flex justify-center items-center  ${getTextColor(
                              record.hue,
                              stretchedS * 100,
                              stretchedV * 100
                            )}`}
                          >
                            360&deg;&nbsp;
                            <ArrowPathIcon className="w-4 h-4" />
                          </div>
                        )}
                      </PopoverButton>
                      {images &&
                        images[record.interval_days] &&
                        images[record.interval_days].length > 0 && (
                          <PopoverPanel
                            className="fixed z-50 bg-primary/90 rounded-lg shadow-lg p-2 min-w-[500px]"
                            style={{
                              left: '50%',
                              top: '50%',
                              transform: 'translate(-50%, -50%)',
                            }}
                          >
                            <div className="text-sm text-white mb-2">
                              {record.interval_days} days after planting
                            </div>
                            {images[record.interval_days].length === 1 ? (
                              <img
                                src={images[record.interval_days][0]}
                                alt={`Plant at ${record.interval_days} days`}
                                className="w-[32rem] h-[32rem] object-cover rounded mx-auto"
                                title={getFilename(
                                  images[record.interval_days][0]
                                )}
                              />
                            ) : (
                              <ImageSequenceSlider
                                images={images[record.interval_days]}
                                title={`Plant at ${record.interval_days} days`}
                                interval={500}
                              />
                            )}
                          </PopoverPanel>
                        )}
                    </Popover>
                  );
                })}
            </div>
          </div>
        );
      })}
      <div className="min-w-max flex items-center px-4 py-5">
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
      <button
        onClick={handleDownloadCSV}
        className="absolute bottom-2 right-2 px-3 py-1.5 bg-sky-600 text-white rounded shadow hover:bg-sky-700"
      >
        Download CSV
      </button>
    </div>
  );
}
