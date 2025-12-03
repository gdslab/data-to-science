import { AxiosResponse } from 'axios';
import clsx from 'clsx';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  ArrowDownTrayIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';

import Alert, { Status } from '../../../Alert';
import { Measurement } from './FieldCampaign';
import { useFieldCampaignContext } from './FieldCampaignContext';

import api from '../../../../api';
import { downloadFile, getFilenameFromContentDisposition } from './utils';

type FieldTimepoints = {
  campaignId: string;
  measurement: Measurement;
  measurementIdx: number;
  treatmentIdx: number;
};
function FieldTimepoints({
  campaignId,
  measurement,
  measurementIdx,
  treatmentIdx,
}: FieldTimepoints) {
  const { addSelectedTimepoint, removeSelectedTimepoint, selectedTimepoints } =
    useFieldCampaignContext();

  const { projectId } = useParams();

  return (
    <div className="w-full flex flex-col gap-1">
      {measurement.timepoints.map((timepoint, timepointIdx) => (
        <div
          key={`ft-${measurementIdx}-${treatmentIdx}-${timepointIdx}`}
          className="w-full h-12 px-4 flex flex-row items-center justify-between bg-white"
        >
          <div className="flex flex-row gap-1">
            <div className="flex items-center">
              <input
                name={`treatment.${treatmentIdx}.measurement.${measurementIdx}.timepoint.${timepointIdx}`}
                type="checkbox"
                className="w-4 h-4 size-4 rounded-sm text-accent2 bg-gray-100 border-gray-300 rounded-sm focus:ring-slate-500 focus:ring-2"
                onChange={(e) => {
                  if (e.target.checked) {
                    addSelectedTimepoint(
                      treatmentIdx.toString() +
                        measurementIdx.toString() +
                        timepointIdx.toString()
                    );
                  } else {
                    removeSelectedTimepoint(
                      treatmentIdx.toString() +
                        measurementIdx.toString() +
                        timepointIdx.toString()
                    );
                  }
                }}
                checked={selectedTimepoints.includes(
                  treatmentIdx.toString() +
                    measurementIdx.toString() +
                    timepointIdx.toString()
                )}
              />
              <label htmlFor="selectTimepoint" className="sr-only">
                Select Timepoint
              </label>
            </div>
            <div className="w-52 flex items-center">
              <span>{timepoint.timepointIdentifier}</span>
            </div>
          </div>
          <div className="flex flex-row items-center justify-between gap-4">
            <button
              className="flex flex-row items-center justify-between gap-2"
              title="Download template"
              onClick={() => {
                async function fetchCsvTemplate() {
                  try {
                    const data = {
                      timepoints: [
                        {
                          treatment: treatmentIdx,
                          measurement: measurementIdx,
                          timepoint: timepointIdx,
                        },
                      ],
                    };
                    const response: AxiosResponse<Blob> = await api.post(
                      `/projects/${projectId}/campaigns/${campaignId}/download`,
                      data,
                      { responseType: 'blob' }
                    );
                    if (response.status === 200) {
                      // get blob from response data
                      const blob = new Blob([response.data], {
                        type: response.headers['content-type'],
                      });
                      // get filename from content-disposition header
                      const filename = getFilenameFromContentDisposition(
                        response.headers['content-disposition']
                      );
                      // download file
                      downloadFile(blob, filename ? filename : 'template.csv');
                    }
                  } catch {}
                }
                fetchCsvTemplate();
              }}
            >
              <span className="text-sm sr-only">Download Template</span>
              <ArrowDownTrayIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

type FieldCampaignRow = { measurementIdx: number; measurement: Measurement };
function FieldCampaignRow({ measurementIdx, measurement }: FieldCampaignRow) {
  const [isVisible, setIsVisible] = useState(false);

  const { fieldCampaign } = useFieldCampaignContext();

  useEffect(() => {
    setIsVisible(false);
  }, [fieldCampaign]);

  function toggleVisibility() {
    setIsVisible(!isVisible);
  }

  return (
    <tr
      className={clsx('h-12 border-b border-gray-400', {
        'border-t': measurementIdx === 0,
      })}
    >
      <td className="w-1/5 min-w-[200px] bg-white text-center">
        {measurement.name} {measurement.units ? `(${measurement.units})` : null}
      </td>
      <td className="w-4/5 min-w-[800px] text-center">
        <div className={clsx('flex gap-1', { hidden: !isVisible })}>
          {fieldCampaign &&
            fieldCampaign.form_data.treatments.map((_, treatmentIdx) => (
              <FieldTimepoints
                key={`ft-${measurementIdx}-${treatmentIdx}`}
                campaignId={fieldCampaign.id}
                measurement={measurement}
                measurementIdx={measurementIdx}
                treatmentIdx={treatmentIdx}
              />
            ))}
        </div>
        <div
          className={clsx(
            'flex flex-row items-center justify-center gap-4 h-12 cursor-pointer text-sky-600',
            {
              'mt-1 bg-slate-100': isVisible,
              'bg-white': !isVisible,
            }
          )}
          onClick={toggleVisibility}
        >
          {!isVisible ? (
            <span>{measurement.timepoints.length} Templates</span>
          ) : (
            <span>Collapse</span>
          )}
          {!isVisible ? (
            <ChevronDownIcon className="h-4 w-4" />
          ) : (
            <ChevronUpIcon className="h-4 w-4" />
          )}
        </div>
      </td>
    </tr>
  );
}

type FieldCampaignHeaderRow = { treatments: string[] };
function FieldCampaignHeaderRow({ treatments }) {
  return (
    <thead>
      <tr className="h-12 text-slate-600">
        <th className="w-1/5 min-w-[200px] bg-slate-300">Measurement (unit)</th>
        <th className="w-4/5 min-w-[800px]">
          <div className="flex flex-col gap-1">
            <div className="h-12 flex items-center justify-center bg-slate-300">
              Treatment
            </div>
            <div className="h-12 flex gap-1 justify-around">
              {treatments.map((name, treatmentIdx) => (
                <div
                  key={`fchr-${treatmentIdx}`}
                  className="w-full flex items-center justify-center gap-4 bg-slate-300"
                >
                  <span>{name}</span>
                </div>
              ))}
            </div>
          </div>
        </th>
      </tr>
    </thead>
  );
}

export default function FieldCampaignTable() {
  const [isDownloading, setIsDownloading] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);

  const { projectId } = useParams();

  const {
    addSelectedTimepoints,
    fieldCampaign,
    resetSelectedTimepoints,
    selectedTimepoints,
  } = useFieldCampaignContext();

  useEffect(() => {
    resetSelectedTimepoints();
  }, [fieldCampaign]);

  if (fieldCampaign) {
    return (
      <div className="flex flex-col justify-center gap-4">
        <table className="min-w-full border-separate border-spacing-1">
          <FieldCampaignHeaderRow
            treatments={fieldCampaign.form_data.treatments.map(
              ({ name }) => name
            )}
          />
          <tbody>
            {/* add one row for each measurement */}
            {fieldCampaign.form_data.measurements.map(
              (measurement, measurementIdx) => (
                <FieldCampaignRow
                  key={`fcr-${measurementIdx}`}
                  measurementIdx={measurementIdx}
                  measurement={measurement}
                />
              )
            )}
          </tbody>
        </table>
        <div className="h-10 flex justify-between gap-4">
          <div className="flex gap-4">
            <button
              className="bg-primary/90 hover:bg-primary text-white font-semibold py-1.5 px-4 rounded-sm"
              onClick={() => {
                let allTimepoints: string[] = [];
                for (
                  let treatmentIdx = 0;
                  treatmentIdx < fieldCampaign.form_data.treatments.length;
                  treatmentIdx++
                ) {
                  for (
                    let measurementIdx = 0;
                    measurementIdx <
                    fieldCampaign.form_data.measurements.length;
                    measurementIdx++
                  ) {
                    for (
                      let timepointIdx = 0;
                      timepointIdx <
                      fieldCampaign.form_data.measurements[measurementIdx]
                        .timepoints.length;
                      timepointIdx++
                    ) {
                      allTimepoints.push(
                        treatmentIdx.toString() +
                          measurementIdx.toString() +
                          timepointIdx.toString()
                      );
                    }
                  }
                  addSelectedTimepoints(allTimepoints);
                }
              }}
            >
              Select all timepoints
            </button>

            {selectedTimepoints.length > 0 ? (
              <button
                className="bg-white hover:bg-white/90 text-primary border-2 border-primary font-semibold py-1.5 px-4 rounded-sm"
                onClick={() => resetSelectedTimepoints()}
              >
                Clear selection
              </button>
            ) : null}
          </div>
          {selectedTimepoints.length > 0 ? (
            <button
              className="w-52 bg-accent2/90 hover:bg-accent2 text-white font-semibold py-1.5 px-4 rounded-sm"
              onClick={() => {
                async function fetchCsvTemplate() {
                  setIsDownloading(true);
                  try {
                    const data = {
                      timepoints: selectedTimepoints.map((timepoint) => {
                        // example timepoint value: "012"
                        // 0 - treatment idx, 1 - measurement idx, 2 - timepoint idx
                        const indexes = timepoint.split('');
                        return {
                          treatment: parseInt(indexes[0]),
                          measurement: parseInt(indexes[1]),
                          timepoint: parseInt(indexes[2]),
                        };
                      }),
                    };
                    const response: AxiosResponse<Blob> = await api.post(
                      `/projects/${projectId}/campaigns/${fieldCampaign?.id}/download`,
                      data,
                      { responseType: 'blob' }
                    );
                    if (response.status === 200) {
                      // get blob from response data
                      const blob = new Blob([response.data], {
                        type: response.headers['content-type'],
                      });
                      // get filename from content-disposition header
                      const filename = getFilenameFromContentDisposition(
                        response.headers['content-disposition']
                      );
                      // download file
                      downloadFile(
                        blob,
                        filename
                          ? filename
                          : selectedTimepoints.length > 0
                          ? 'templates.zip'
                          : 'template.csv'
                      );
                      setIsDownloading(false);
                    }
                  } catch {
                    setIsDownloading(false);
                    setStatus({
                      type: 'error',
                      msg: 'Unable to process request',
                    });
                  }
                }
                fetchCsvTemplate();
              }}
            >
              {isDownloading
                ? 'Preparing templates...'
                : `Download ${selectedTimepoints.length} templates`}
            </button>
          ) : null}
        </div>
        {status ? <Alert alertType={status.type}>{status.msg}</Alert> : null}
      </div>
    );
  } else {
    return null;
  }
}
