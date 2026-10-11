import axios from 'axios';
import { Feature } from 'geojson';
import { useEffect, useState } from 'react';

import { DataProduct } from '../pages/workspace/projects/Project';
import {
  MultibandSymbology,
  SingleBandSymbology,
} from './RasterSymbologyContext';

import { getTitilerQueryParams } from './utils';

type FeaturePreviewImageProps = {
  dataProduct: DataProduct;
  feature: Feature;
  symbology: SingleBandSymbology | MultibandSymbology;
};

export default function FeaturePreviewImage({
  dataProduct,
  feature,
  symbology,
}: FeaturePreviewImageProps) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Build the titiler /cog/feature url
  const cogUrl = dataProduct.filepath;
  const resourcePath = `/cog/feature`;
  const basePath = window.location.origin;
  const queryParams = getTitilerQueryParams(cogUrl, dataProduct, symbology);
  queryParams.append('max_size', '1024');
  const url = `${basePath}${resourcePath}?${queryParams.toString()}`;

  useEffect(() => {
    const controller = new AbortController();
    let blobUrl: string | null = null;

    setLoading(true);
    setError(false);
    setImageUrl(null);

    axios
      .post(url, feature, { responseType: 'blob', signal: controller.signal })
      .then((response) => {
        blobUrl = URL.createObjectURL(response.data);
        setImageUrl(blobUrl);
        setLoading(false);
      })
      .catch((err) => {
        if (axios.isCancel(err)) return;
        console.error(err);
        setError(true);
        setLoading(false);
      });

    return () => {
      controller.abort();
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [url, feature]);

  // Children are absolutely positioned so the image never drives the panel height
  return (
    <div className="relative h-full min-h-40 w-full">
      {loading && (
        <div className="absolute inset-0 rounded-md bg-slate-100 animate-pulse" />
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center text-sm text-slate-500">
          Preview unavailable
        </div>
      )}
      {imageUrl && (
        <img
          id="feature-preview-image"
          className="absolute inset-0 h-full w-full object-contain"
          alt="Feature preview"
          src={imageUrl}
        />
      )}
    </div>
  );
}
