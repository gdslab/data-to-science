import axios, { AxiosResponse } from 'axios';
import { Field, useFormikContext } from 'formik';
import Papa from 'papaparse';
import { useEffect, useMemo, useState } from 'react';

import HintText from '../../../../../HintText';
import { SelectField } from '../../../../../InputFields';

import { DataProduct, ZonalFeatureCollection } from '../../Project';
import { ToolboxFields } from './ToolboxModal';
import { removeKeysFromFeatureProperties } from '../../mapLayers/utils';

import { useProjectContext } from '../../ProjectContext';
import { useParams } from 'react-router-dom';
import { downloadFile as downloadCSV } from '../../fieldCampaigns/utils';
import { download as downloadGeoJSON } from '../../mapLayers/utils';

const EXGBandSelection = ({ dataProduct }: { dataProduct: DataProduct }) => {
  const bandOptions = dataProduct.stac_properties.eo.map((band, idx) => ({
    label: band.name,
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
    label: band.name,
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

const RGBTools = ({ dataProduct }: { dataProduct: DataProduct }) => {
  const { values } = useFormikContext<ToolboxFields>();

  return (
    <ul>
      <li>
        <div className="flex flex-col gap-4">
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

const LidarTools = () => {
  return (
    <ul>
      <li>
        <div className="flex flex-col gap-4">
          <div className="flex items-center">
            <Field id="chm-checkbox" type="checkbox" name="chm" disabled />
            <label
              htmlFor="chm-checkbox"
              className="ms-2 text-sm font-medium text-gray-900"
            >
              Canopy Height Model (CHM) <span className="italic">Coming soon</span>
            </label>
          </div>
        </div>
      </li>
    </ul>
  );
};

const DownloadZonalStatistics = ({
  dataProductId,
  layerId,
}: {
  dataProductId: string;
  layerId: string;
}) => {
  const [zonalFeatureCollection, setZonalFeatureCollection] =
    useState<ZonalFeatureCollection | null>(null);

  const { projectId, flightId } = useParams();

  const keysToSkip = [
    'id',
    'layer_id',
    'is_active',
    'project_id',
    'flight_id',
    'data_product_id',
  ];

  useEffect(() => {
    async function fetchZonalStats() {
      try {
        const response: AxiosResponse<ZonalFeatureCollection | null> = await axios.get(
          `${
            import.meta.env.VITE_API_V1_STR
          }/projects/${projectId}/flights/${flightId}/data_products/${dataProductId}/zonal_statistics?layer_id=${layerId}`
        );
        if (response.status === 200) {
          setZonalFeatureCollection(response.data);
        } else {
          console.log('Unable to check for previously calculated zonal statistics');
        }
      } catch (_err) {
        console.log('Unable to check for previously calculated zonal statistics');
      }
    }
    if (projectId && flightId && dataProductId) {
      fetchZonalStats();
    }
  }, []);

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
          downloadCSV(csvFile, 'zonal_statistics.csv');
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
            'zonal_statistics.geojson'
          );
        }}
      >
        Download GeoJSON
      </button>
    </div>
  );
};

const ZonalStatisticTools = ({ dataProductId }: { dataProductId: string }) => {
  const { values } = useFormikContext<ToolboxFields>();
  const { mapLayers } = useProjectContext();

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
            <label htmlFor="zonal" className="ms-2 text-sm font-medium text-gray-900">
              Zonal Statistics
            </label>
          </div>
          {values.zonal && (
            <div>
              <span className="text-sm">Select Layer with Zonal Features:</span>
              {filteredAndSortedMapLayers.map(({ layer_id, layer_name, geom_type }) => (
                <label
                  key={layer_id}
                  className="block text-sm text-gray-600 font-bold pb-1"
                >
                  <Field type="radio" name="zonal_layer_id" value={layer_id} />
                  <span className="ml-2">{layer_name}</span>
                  {(geom_type.toLowerCase() === 'polygon' ||
                    geom_type.toLowerCase() === 'multipolygon') && (
                    <DownloadZonalStatistics
                      dataProductId={dataProductId}
                      layerId={layer_id}
                    />
                  )}
                </label>
              ))}
            </div>
          )}
        </div>
      </li>
    </ul>
  );
};

export { RGBTools, MultiSpectralTools, LidarTools, ZonalStatisticTools };
