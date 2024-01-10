import axios from 'axios';
import { useEffect, useState } from 'react';

import { DSMSymbologySettings, useMapContext } from './MapContext';
import { DataProduct } from '../pages/projects/ProjectDetail';

export default function ColorBarControl({
  projectId,
  dataProduct,
  symbology = undefined,
}: {
  projectId?: string;
  dataProduct: DataProduct;
  symbology?: DSMSymbologySettings | undefined;
}) {
  const [url, setURL] = useState('');
  const { symbologySettings } = useMapContext();

  useEffect(() => {
    async function fetchColorBar(symbology: DSMSymbologySettings) {
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
            },
          }
        );
        if (response) {
          // only set url if it reseponds with OK status
          axios
            .get(response.data.colorbar_url)
            .then(() => setURL(response.data.colorbar_url))
            .catch(() => setURL(''));
        }
      } catch (err) {
        throw err;
      }
    }
    const colorBarSymbology = symbology
      ? symbology
      : (symbologySettings as DSMSymbologySettings);

    fetchColorBar(colorBarSymbology);
  }, [symbologySettings]);

  if (url) {
    return (
      <div className="leaflet-control-container">
        <div className="leaflet-bottom leaflet-left bottom-4">
          <div className="leaflet-control p-1.5 bg-white/40 border-4 border-white/20 rounded-md shadow-md">
            <img src={url} className="h-80" />
          </div>
        </div>
      </div>
    );
  } else {
    return null;
  }
}
