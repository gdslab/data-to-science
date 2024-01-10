import axios from 'axios';
import { useEffect, useState } from 'react';

import { DSMSymbologySettings, useMapContext } from './MapContext';
import { DataProduct } from '../pages/projects/ProjectDetail';

export default function ColorBarControl({
  projectId,
  dataProduct,
}: {
  projectId: string;
  dataProduct: DataProduct;
}) {
  const [url, setURL] = useState('');
  const { symbologySettings } = useMapContext();

  useEffect(() => {
    async function fetchColorBar(symbology: DSMSymbologySettings) {
      const stats = dataProduct.stac_properties.raster[0].stats;

      try {
        const response = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}/flights/${
            dataProduct.flight_id
          }/data_products/${dataProduct.id}/utils/colorbar`,
          {
            params: {
              cmin:
                symbology.mode === 'minMax'
                  ? symbology.min
                  : symbology.mode === 'userDefined'
                  ? symbology.userMin
                  : symbology.mode === 'meanStdDev'
                  ? stats.mean - stats.stddev * symbology.meanStdDev
                  : symbology.min,
              cmax:
                symbology.mode === 'minMax'
                  ? symbology.max
                  : symbology.mode === 'userDefined'
                  ? symbology.userMax
                  : symbology.mode === 'meanStdDev'
                  ? stats.mean + stats.stddev * symbology.meanStdDev
                  : symbology.max,
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
    const symbology = symbologySettings as DSMSymbologySettings | undefined;
    if (symbology) {
      fetchColorBar(symbology);
    }
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
