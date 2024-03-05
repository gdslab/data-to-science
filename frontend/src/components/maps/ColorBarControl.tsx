import axios from 'axios';
import { useEffect, useState } from 'react';
import { ArrowPathIcon } from '@heroicons/react/24/outline';

import { DSMSymbologySettings, useMapContext } from './MapContext';
import { DataProduct } from '../pages/projects/Project';
import { classNames } from '../utils';

export default function ColorBarControl({
  projectId,
  dataProduct,
  symbology = undefined,
}: {
  projectId?: string;
  dataProduct: DataProduct;
  symbology?: DSMSymbologySettings | undefined;
}) {
  const [isRefreshing, toggleIsRefreshing] = useState(false);
  const [url, setURL] = useState('');
  const { symbologySettings } = useMapContext();

  const colorBarSymbology = symbology
    ? symbology
    : (symbologySettings as DSMSymbologySettings);

  async function fetchColorBar(symbology: DSMSymbologySettings, refresh = false) {
    const stats = dataProduct.stac_properties.raster[0].stats;

    try {
      if (!projectId) {
        projectId = dataProduct.filepath.split('/projects/')[1].split('/flights/')[0];
      }
      const response = await axios.get(
        `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}/flights/${
          dataProduct.flight_id
        }/data_products/${dataProduct.id}/utils/colorbar`,
        {
          params: {
            cmin:
              symbology.mode === 'minMax'
                ? symbology.min.toFixed(2)
                : symbology.mode === 'userDefined'
                ? symbology.userMin.toFixed(2)
                : symbology.mode === 'meanStdDev'
                ? (stats.mean - stats.stddev * symbology.meanStdDev).toFixed(2)
                : symbology.min.toFixed(2),
            cmax:
              symbology.mode === 'minMax'
                ? symbology.max.toFixed(2)
                : symbology.mode === 'userDefined'
                ? symbology.userMax.toFixed(2)
                : symbology.mode === 'meanStdDev'
                ? (stats.mean + stats.stddev * symbology.meanStdDev).toFixed(2)
                : symbology.max.toFixed(2),
            cmap: symbology.colorRamp,
            refresh: refresh,
          },
        }
      );
      if (response) {
        // only set url if it reseponds with OK status
        axios
          .get(response.data.colorbar_url)
          .then(() => setURL(response.data.colorbar_url))
          .catch(() => setURL(''))
          .finally(() => setTimeout(() => toggleIsRefreshing(false), 2000));
      }
    } catch (err) {
      setTimeout(() => toggleIsRefreshing(false), 2000);
      throw err;
    }
  }

  useEffect(() => {
    fetchColorBar(colorBarSymbology);
  }, [symbologySettings]);

  if (url) {
    return (
      <div className="leaflet-control-container">
        <div className="leaflet-bottom leaflet-left bottom-8">
          <div className="leaflet-control p-1.5 bg-white/60 border-4 border-white/40 rounded-md shadow-md">
            <img src={url} className="h-80" />
            <button
              type="button"
              className="flex items-center text-sky-600"
              onClick={async () => {
                toggleIsRefreshing(true);
                fetchColorBar(colorBarSymbology, true);
              }}
            >
              <ArrowPathIcon
                className={classNames(
                  isRefreshing ? 'animate-spin' : '',
                  'h-4 w-4 inline mr-2'
                )}
              />
              <span>Refresh</span>
            </button>
          </div>
        </div>
      </div>
    );
  } else {
    return null;
  }
}
