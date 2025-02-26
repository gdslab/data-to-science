import axios from 'axios';
import { Feature } from 'geojson';
import { useEffect, useState } from 'react';

import { DataProduct } from '../pages/projects/Project';
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
  const [imageUrl, setImageUrl] = useState(null);

  // Build the titiler /cog/feature url
  const cogUrl = dataProduct.filepath;
  const resourcePath = `/cog/feature`;
  const basePath = window.location.origin;
  const queryParams = getTitilerQueryParams(cogUrl, dataProduct, symbology);
  queryParams.append('max_size', '1024');
  const url = `${basePath}${resourcePath}?${queryParams.toString()}`;

  // Fetch image from titiler and update the imageUrl state
  useEffect(() => {
    let isMounted = true;
    let blobUrl;

    axios
      .post(url, feature, { responseType: 'blob' })
      .then((response) => {
        blobUrl = URL.createObjectURL(response.data);
        if (isMounted) {
          setImageUrl(blobUrl);
        }
      })
      .catch((err) => console.error(err));

    // Cleanup function to revoke the blob url
    return () => {
      isMounted = false;
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [url, feature]);

  return (
    <div className="flex h-40 w-full justify-center">
      <img
        id="feature-preview-image"
        className="object-contain h-40"
        alt="Feature preview"
        src={imageUrl || undefined}
      />
    </div>
  );
}
