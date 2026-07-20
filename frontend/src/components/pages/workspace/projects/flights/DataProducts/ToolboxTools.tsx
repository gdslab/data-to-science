import { AxiosResponse } from 'axios';
import { Field, useFormikContext } from 'formik';
import Papa from 'papaparse';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router';

import HintText from '../../../../../HintText';
import { useInterval } from '../../../../../hooks';
import { SelectField } from '../../../../../InputFields';
import { DataProduct, ZonalFeatureCollection } from '../../Project';
import { ToolboxFields } from './ToolboxModal';
import {
  removeKeysFromFeatureProperties,
  RESERVED_FEATURE_PROPERTY_KEYS,
} from '../../mapLayers/utils';
import { useProjectContext } from '../../ProjectContext';
import { downloadFile as downloadCSV } from '../../fieldCampaigns/utils';
import { download as downloadGeoJSON } from '../../mapLayers/utils';
import { isElevationDataProduct } from '../../../../../maps/utils';

import api from '../../../../../../api';

const EXGBandSelection = ({ dataProduct }: { dataProduct: DataProduct }) => {
  const bandOptions = dataProduct.stac_properties.eo.map((band, idx) => ({
    label: `${band.name} (${band.description})`,
    value: idx + 1,
  }));

  return (
    <div>
      <HintText>Select Red, Green, and Blue Bands</HintText>
      <div className="flex flex-row gap-4">
        <SelectField name="exgRed" label="Red Band" options={bandOptions} />
        <SelectField name="exgGreen" label="Green Band" options={bandOptions} />
        <SelectField name="exgBlue" label="Blue Band" options={bandOptions} />
      </div>
    </div>
  );
};

const NDVIBandSelection = ({ dataProduct }: { dataProduct: DataProduct }) => {
  const bandOptions = dataProduct.stac_properties.eo.map((band, idx) => ({
    label: `${band.name} (${band.description})`,
    value: idx + 1,
  }));

  return (
    <div>
      <HintText>Select Red and Near-Infrared Bands</HintText>
      <div className="flex flex-row gap-4">
        <SelectField name="ndviRed" label="Red Band" options={bandOptions} />
        <SelectField name="ndviNIR" label="NIR Band" options={bandOptions} />
      </div>
    </div>
  );
};

const VARIBandSelection = ({ dataProduct }: { dataProduct: DataProduct }) => {
  const bandOptions = dataProduct.stac_properties.eo.map((band, idx) => ({
    label: `${band.name} (${band.description})`,
    value: idx + 1,
  }));

  return (
    <div>
      <HintText>Select Red, Green, and Blue Bands</HintText>
      <div className="flex flex-row gap-4">
        <SelectField name="variRed" label="Red Band" options={bandOptions} />
        <SelectField
          name="variGreen"
          label="Green Band"
          options={bandOptions}
        />
        <SelectField name="variBlue" label="Blue Band" options={bandOptions} />
      </div>
    </div>
  );
};

const HillshadeTools = () => {
  return (
    <ul>
      <li>
        <div className="flex flex-col gap-4">
          <div className="flex items-center">
            <Field id="hillshade" type="checkbox" name="hillshade" />
            <label
              htmlFor="hillshade"
              className="ms-2 text-sm font-medium text-gray-900"
            >
              Hillshade
            </label>
          </div>
        </div>
      </li>
    </ul>
  );
};

const PointCloudTools = ({
  otherDataProducts,
}: {
  otherDataProducts: DataProduct[];
}) => {
  const { values } = useFormikContext<ToolboxFields>();
  const elevationDataProducts = useMemo(
    () => otherDataProducts.filter(isElevationDataProduct),
    [otherDataProducts]
  );

  return (
    <ul className="space-y-6">
      {elevationDataProducts.length > 0 ? (
        <li>
          <div className="flex flex-col gap-4">
            <div className="flex items-center">
              <Field id="chm-checkbox" type="checkbox" name="chm" />
              <label
                htmlFor="chm-checkbox"
                className="ms-2 text-sm font-medium text-gray-900"
              >
                Canopy Height Model (CHM)
              </label>
            </div>
            {values.chm && (
              <div className="flex flex-col gap-4">
                <HintText>
                  The height data (e.g., DTM, DSM, DEM) for this process should
                  indicate terrain height.
                </HintText>
                <SelectField
                  name="dem_id"
                  label="DTM"
                  options={elevationDataProducts.map((dp) => ({
                    label: dp.data_type.toUpperCase(),
                    value: dp.id,
                  }))}
                />
                <div className="flex flex-row gap-4 items-center">
                  <div className="flex flex-col">
                    <label
                      htmlFor="chmResolution"
                      className="block text-sm text-gray-400 font-bold pt-2 pb-1"
                    >
                      Resolution*
                    </label>
                    <Field
                      name="chmResolution"
                      type="number"
                      min={0.1}
                      step={0.1}
                    />
                  </div>
                  <div className="flex flex-col">
                    <label
                      htmlFor="chmPercentile"
                      className="block text-sm text-gray-400 font-bold pt-2 pb-1"
                    >
                      Percentile*
                    </label>
                    <Field
                      name="chmPercentile"
                      type="number"
                      min={0}
                      max={100}
                      step={0.1}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>
        </li>
      ) : (
        <li>
          <div>
            <HintText>
              CHM unavailable. No DTM data products found. "DTM", "DSM", or
              "DEM" must be in the name of the data product for it to be
              detected.
            </HintText>
          </div>
        </li>
      )}
      <li>
        <div className="flex flex-col gap-4">
          <div className="flex items-center">
            <Field id="dtm-checkbox" type="checkbox" name="dtm" />
            <label
              htmlFor="dtm-checkbox"
              className="ms-2 text-sm font-medium text-gray-900"
            >
              Digital Terrain Model (DTM)
            </label>
          </div>
          {values.dtm && (
            <div className="flex flex-col gap-4">
              <HintText>
                Generate a digital terrain model from point cloud data using
                ground points.
              </HintText>
              <div className="flex flex-row gap-4 items-center">
                <div className="flex flex-col">
                  <label
                    htmlFor="dtmResolution"
                    className="block text-sm text-gray-400 font-bold pt-2 pb-1"
                  >
                    Resolution*
                  </label>
                  <Field
                    name="dtmResolution"
                    type="number"
                    min={0.1}
                    step={0.1}
                  />
                </div>
                <div className="flex flex-col">
                  <label
                    htmlFor="dtmRigidness"
                    className="block text-sm text-gray-400 font-bold pt-2 pb-1"
                  >
                    Rigidness*
                  </label>
                  <Field
                    name="dtmRigidness"
                    type="number"
                    min={1}
                    max={3}
                    step={1}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </li>
    </ul>
  );
};

const RGBTools = ({ dataProduct }: { dataProduct: DataProduct }) => {
  const { values } = useFormikContext<ToolboxFields>();

  return (
    <ul>
      <li>
        <div className="flex flex-col gap-4 mb-4">
          <div className="flex items-center">
            <Field id="exg-checkbox" type="checkbox" name="exg" />
            <label
              htmlFor="exg-checkbox"
              className="ms-2 text-sm font-medium text-gray-900"
            >
              Excess Green Vegetation Index (ExG)
            </label>
          </div>
          {values.exg ? <EXGBandSelection dataProduct={dataProduct} /> : null}
        </div>
      </li>
      <li>
        <div className="flex flex-col gap-4">
          <div className="flex items-center">
            <Field id="vari-checkbox" type="checkbox" name="vari" />
            <label
              htmlFor="vari-checkbox"
              className="ms-2 text-sm font-medium text-gray-900"
            >
              Visible Atmospherically Resistant Index (VARI)
            </label>
          </div>
          {values.vari ? <VARIBandSelection dataProduct={dataProduct} /> : null}
        </div>
      </li>
    </ul>
  );
};

const MultiSpectralTools = ({ dataProduct }: { dataProduct: DataProduct }) => {
  const { values } = useFormikContext<ToolboxFields>();

  return (
    <ul>
      <li>
        <div className="flex flex-col gap-4">
          <div className="flex items-center">
            <Field id="nvdi-checkbox" type="checkbox" name="ndvi" />
            <label
              htmlFor="nvdi-checkbox"
              className="ms-2 text-sm font-medium text-gray-900"
            >
              Normalized Difference Vegetation Index (NDVI)
            </label>
          </div>
          {values.ndvi ? <NDVIBandSelection dataProduct={dataProduct} /> : null}
        </div>
      </li>
    </ul>
  );
};

const DownloadZonalStatistics = ({
  dataProduct,
  layerId,
}: {
  dataProduct: DataProduct;
  layerId: string;
}) => {
  const [zonalFeatureCollection, setZonalFeatureCollection] =
    useState<ZonalFeatureCollection | null>(null);

  const { projectId, flightId } = useParams();
  const { project, flights } = useProjectContext();

  const keysToSkip = RESERVED_FEATURE_PROPERTY_KEYS;

  const generateFilename = (extension: string): string => {
    // Helper function to sanitize filename parts
    const sanitize = (str: string | null | undefined): string => {
      if (!str) return '';
      return str.replace(/[^a-zA-Z0-9-]/g, '-');
    };

    // Get project title
    const projectTitle = sanitize(project?.title);

    // Get current flight data
    const currentFlight = flights?.find((f) => f.id === flightId);
    const acquisitionDate = currentFlight?.acquisition_date || '';
    const sensor = sanitize(currentFlight?.sensor);

    // Get data type
    const dataType = sanitize(dataProduct.data_type);

    // Build filename parts (exclude empty strings)
    const parts = [
      projectTitle,
      acquisitionDate,
      sensor,
      dataType,
      'zonal_statistics',
    ].filter(Boolean);

    // Fallback to original filename if we don't have enough data
    if (parts.length < 2) {
      return `zonal_statistics.${extension}`;
    }

    return `${parts.join('_')}.${extension}`;
  };

  useEffect(() => {
    async function fetchZonalStats() {
      try {
        const response: AxiosResponse<ZonalFeatureCollection | null> =
          await api.get(
            `/projects/${projectId}/flights/${flightId}/data_products/${dataProduct.id}/zonal_statistics?layer_id=${layerId}`
          );
        if (response.status === 200) {
          setZonalFeatureCollection(response.data);
        } else {
          console.log(
            'Unable to check for previously calculated zonal statistics'
          );
        }
      } catch {
        console.log(
          'Unable to check for previously calculated zonal statistics'
        );
      }
    }
    if (projectId && flightId && dataProduct.id) {
      fetchZonalStats();
    }
  }, [dataProduct.id, layerId, flightId, projectId]);

  if (
    !zonalFeatureCollection ||
    (zonalFeatureCollection && zonalFeatureCollection.features.length === 0)
  )
    return null;

  return (
    <div className="inline">
      <button
        className="ml-2 text-sky-600"
        type="button"
        onClick={() => {
          const csvData = Papa.unparse(
            zonalFeatureCollection.features.map((feature) =>
              Object.fromEntries(
                Object.entries(feature.properties).filter(
                  ([key]) => !keysToSkip.includes(key)
                )
              )
            )
          );
          const csvFile = new Blob([csvData], { type: 'text/csv' });
          downloadCSV(csvFile, generateFilename('csv'));
        }}
      >
        Download CSV
      </button>
      <button
        className="ml-2 text-sky-600"
        type="button"
        onClick={() => {
          downloadGeoJSON(
            'json',
            removeKeysFromFeatureProperties(zonalFeatureCollection, keysToSkip),
            generateFilename('geojson')
          );
        }}
      >
        Download GeoJSON
      </button>
    </div>
  );
};

interface ZonalJob {
  id: string;
  name: string;
  state: string;
  status: 'WAITING' | 'INPROGRESS' | 'SUCCESS' | 'FAILED';
  start_time: string;
  end_time: string | null;
  extra: {
    layer_id?: string;
    detail?: string;
    zones_total?: number;
    zones_with_data?: number;
  } | null;
}

const isActiveJob = (job: ZonalJob) =>
  job.status === 'WAITING' || job.status === 'INPROGRESS';

const ZonalLayerStatus = ({
  dataProduct,
  layerId,
  job,
}: {
  dataProduct: DataProduct;
  layerId: string;
  job: ZonalJob | null;
}) => {
  if (job && isActiveJob(job)) {
    return (
      <span className="ml-2 inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
        <span className="h-2 w-2 animate-pulse rounded-full bg-amber-500"></span>
        Processing...
      </span>
    );
  }

  // per-run zone summary (present on jobs run after zone-summary tracking)
  const zonesTotal = job?.extra?.zones_total;
  const zonesWithData = job?.extra?.zones_with_data;
  const summaryKnown =
    job?.status === 'SUCCESS' &&
    typeof zonesTotal === 'number' &&
    typeof zonesWithData === 'number';
  const noOverlap = summaryKnown && zonesWithData === 0;
  const partialOverlap =
    summaryKnown && zonesWithData > 0 && zonesWithData < zonesTotal;

  // no zone overlapped the raster: a retry won't help, so report it as an
  // informational outcome rather than a failure and skip the download links
  if (noOverlap) {
    return (
      <span
        className="ml-2 inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700"
        title="The selected zones fall outside this data product's extent or cover only no-data pixels."
      >
        No overlapping raster data
      </span>
    );
  }

  // job finished (or predates job tracking); offer downloads for any
  // previously computed results, alongside the latest run's outcome
  return (
    <span className="inline-flex items-center">
      {job && job.status === 'FAILED' && (
        <span
          className="ml-2 inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800"
          title={job.extra?.detail || 'Zonal statistics could not be calculated'}
        >
          Failed &mdash; select the layer and click Start to retry
        </span>
      )}
      <DownloadZonalStatistics dataProduct={dataProduct} layerId={layerId} />
      {partialOverlap ? (
        <span className="ml-2 text-xs font-normal text-amber-700">
          {zonesWithData} of {zonesTotal} zones had data
        </span>
      ) : (
        job &&
        job.status === 'SUCCESS' &&
        job.end_time && (
          <span className="ml-2 text-xs font-normal text-gray-400">
            computed {new Date(job.end_time).toLocaleString()}
          </span>
        )
      )}
    </span>
  );
};

const ZonalStatisticTools = ({ dataProduct }: { dataProduct: DataProduct }) => {
  const { isSubmitting, submitCount, values } =
    useFormikContext<ToolboxFields>();
  const { mapLayers } = useProjectContext();
  const { projectId, flightId } = useParams();

  const [jobs, setJobs] = useState<ZonalJob[]>([]);

  const fetchJobs = useCallback(async () => {
    if (!projectId || !flightId || !dataProduct.id) return;
    try {
      const response: AxiosResponse<ZonalJob[]> = await api.get(
        `/projects/${projectId}/flights/${flightId}/data_products/${dataProduct.id}/jobs`,
        { params: { name: 'zonal' } }
      );
      setJobs(response.data);
    } catch {
      console.log('Unable to check status of zonal statistics jobs');
    }
  }, [projectId, flightId, dataProduct.id]);

  // fetch on reveal and after each form submission completes
  useEffect(() => {
    if (values.zonal && !isSubmitting) {
      fetchJobs();
    }
  }, [values.zonal, isSubmitting, submitCount, fetchJobs]);

  // poll while any zonal job is still running
  const hasActiveJob = jobs.some(isActiveJob);
  useInterval(fetchJobs, values.zonal && hasActiveJob ? 5000 : null);

  const filteredAndSortedMapLayers = useMemo(() => {
    return mapLayers
      .filter(
        ({ geom_type }) =>
          geom_type.toLowerCase() === 'polygon' ||
          geom_type.toLowerCase() === 'multipolygon'
      )
      .sort((a, b) => a.layer_name.localeCompare(b.layer_name));
  }, [mapLayers]);

  return (
    <ul>
      <li>
        <div className="flex flex-col gap-4">
          <div className="flex items-center">
            <Field id="zonal" type="checkbox" name="zonal" />
            <label
              htmlFor="zonal"
              className="ms-2 text-sm font-medium text-gray-900"
            >
              Zonal Statistics
            </label>
          </div>
          {values.zonal && (
            <div>
              <span className="text-sm">Select Layer with Zonal Features:</span>
              {filteredAndSortedMapLayers.map(({ layer_id, layer_name }) => {
                // jobs are returned newest first
                const layerJob =
                  jobs.find((job) => job.extra?.layer_id === layer_id) ?? null;
                return (
                  <div
                    key={layer_id}
                    className="flex items-center text-sm text-gray-600 font-bold pb-1"
                  >
                    <label className="inline-flex items-center">
                      <Field
                        type="radio"
                        name="zonal_layer_id"
                        value={layer_id}
                      />
                      <span className="ml-2">{layer_name}</span>
                    </label>
                    <ZonalLayerStatus
                      dataProduct={dataProduct}
                      layerId={layer_id}
                      job={layerJob}
                    />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </li>
    </ul>
  );
};

export {
  HillshadeTools,
  MultiSpectralTools,
  PointCloudTools,
  RGBTools,
  ZonalStatisticTools,
};
