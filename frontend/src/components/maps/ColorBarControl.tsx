import axios from 'axios';
import clsx from 'clsx';
import { useEffect, useState } from 'react';
import { ArrowPathIcon } from '@heroicons/react/24/outline';

import { DataProduct } from '../pages/projects/Project';
import {
  SingleBandSymbology,
  useRasterSymbologyContext,
} from './RasterSymbologyContext';

import api from '../../api';

export default function ColorBarControl({
  dataProduct,
  position = 'left',
  projectId,
}: {
  dataProduct: DataProduct;
  position?: 'left' | 'right';
  projectId?: string;
}) {
  const [isRefreshing, toggleIsRefreshing] = useState(false);
  const [url, setURL] = useState('');

  const { state } = useRasterSymbologyContext();

  const symbology = state[dataProduct.id]?.symbology;

  async function fetchColorBar(
    symbology: SingleBandSymbology,
    refresh = false
  ) {
    const stats = dataProduct.stac_properties.raster[0].stats;

    try {
      if (!projectId) {
        projectId = dataProduct.filepath
          .split('/projects/')[1]
          .split('/flights/')[0];
      }
      const response = await api.get(
        `/projects/${projectId}/flights/${dataProduct.flight_id}/data_products/${dataProduct.id}/utils/colorbar`,
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
    if (symbology) {
      fetchColorBar(symbology as SingleBandSymbology);
    }
  }, [symbology]);

  if (!symbology) return null;

  if (url) {
    return (
      <div
        className={clsx(
          'absolute bottom-8 bg-white/75 rounded-md shadow-md px-3 py-6 m-2.5 leading-3 text-slate-600 outline-none',
          { 'start-0': position === 'left', 'end-0': position === 'right' }
        )}
      >
        <img src={url} className="h-80" />
        <button
          type="button"
          className="flex items-center text-sky-600"
          onClick={async () => {
            toggleIsRefreshing(true);
            fetchColorBar(symbology as SingleBandSymbology, true);
          }}
        >
          <ArrowPathIcon
            className={clsx('h-4 w-4 inline mr-2', {
              'animate-spin': isRefreshing,
            })}
          />
          <span>Refresh</span>
        </button>
      </div>
    );
  } else {
    return null;
  }
}
