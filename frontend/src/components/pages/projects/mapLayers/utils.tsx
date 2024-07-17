import axios, { AxiosResponse, isAxiosError } from 'axios';
import { FeatureCollection } from 'geojson';
import shpwrite, { DownloadOptions, ZipOptions } from '@mapbox/shp-write';
import { MapLayerFeatureCollection } from '../Project';

interface MapboxZipOptions extends ZipOptions, DownloadOptions {}

export type MapLayerTableRow = {
  featureCollection: MapLayerFeatureCollection;
  geomType: string;
  id: string;
  name: string;
};

/**
 * Sends zipped shapefile to server for conversion to GeoJSON format.
 * @param file Zipped shapefile.
 * @returns GeoJSON extracted from zipped shapefile or null.
 */
export async function shpToGeoJSON(file: File): Promise<FeatureCollection | null> {
  try {
    const formData = new FormData();
    formData.append('files', file);

    const headers = { 'Content-Type': 'multipart/form-data' };

    const response: AxiosResponse<FeatureCollection> = await axios.post(
      `${import.meta.env.VITE_API_V1_STR}/locations/upload_vector_layer`,
      formData,
      { headers }
    );
    if (response.status === 200) {
      const featureCollection = response.data;
      if (featureCollection.features.length > 0) {
        return featureCollection;
      } else {
        return null;
      }
    } else {
      throw new Error('Unable to process zipped shapefile');
    }
  } catch (err) {
    if (isAxiosError(err)) {
      if (err.response && err.response.data.detail) {
        throw new Error(err.response.data.detail);
      } else {
        throw new Error('Unable to process zipped shapefile');
      }
    } else {
      throw new Error('Unable to process zipped shapefile');
    }
  }
}

/**
 * Creates row data for map layers table. Feature collections with
 * multiple features will be represented by a single row using a common
 * layer name and layer id.
 * @param {FeatureCollection[]} mapLayers Array of feature collections.
 * @returns  Row data for vector table.
 */
export function prepMapLayers(
  mapLayers: MapLayerFeatureCollection[]
): MapLayerTableRow[] {
  // each layer is returned as a geojson feature collection from the api

  // a single feature collection may have multiple features, but the
  // layer name and layer id will be the same for each feature in the collection
  const features: MapLayerTableRow[] = [];
  mapLayers.forEach((featureCollection) => {
    if (
      featureCollection &&
      'features' in featureCollection &&
      featureCollection.features.length > 0
    ) {
      const geomTypes = [
        ...new Set(featureCollection.features.map((feature) => feature.geometry.type)),
      ];
      const id = featureCollection.features[0].properties?.layer_id;
      const name = featureCollection.features[0].properties?.layer_name;
      features.push({
        featureCollection: featureCollection,
        geomType: geomTypes.join(', '),
        id,
        name,
      });
    }
  });
  return features;
}

/**
 * Removes extra properties added by D2S from feature collection
 * that will be downloaded. Only properties included in original upload are kept.
 * @param {FeatureCollection} featureCollection Feature collection with original props.
 * @returns Feature Collection representative of initially uploaded dataset.
 */
function prepFeatureCollectionForDownload(
  featureCollection: FeatureCollection
): FeatureCollection {
  featureCollection.features.forEach((feature) => {
    if ('properties' in feature && feature.properties) {
      if ('properties' in feature.properties) {
        const originalProperties = feature.properties.properties;
        feature.properties = originalProperties;
      }
    }
  });
  return featureCollection;
}

/**
 * Creates blobs for json or zip download of a feature collection and starts download.
 * @param {string} downloadType Default download option is JSON. Zip also supported.
 * @param {MapLayerFeatureCollection} featureCollection Feature collection to be downloaded.
 */
export function download(
  downloadType: string = 'json',
  featureCollection: MapLayerFeatureCollection
) {
  const filename = featureCollection.features[0].properties?.layer_name;
  const updatedFeatureCollection = prepFeatureCollectionForDownload(
    JSON.parse(JSON.stringify(featureCollection))
  );
  // create blob based on download request 'json' or 'zip'
  if (downloadType === 'zip') {
    const options: MapboxZipOptions = {
      filename:
        filename && typeof filename === 'string' ? filename : 'feature_collection',
      outputType: 'blob',
      compression: 'DEFLATE',
    };
    shpwrite
      .zip(updatedFeatureCollection, options)
      .then((zipData) => {
        if (zipData instanceof ArrayBuffer || zipData instanceof Blob) {
          const blob = new Blob([zipData], { type: 'application/zip' });
          const downloadName = filename ? filename + '.zip' : 'feature_collection.zip';
          createAndClickDownloadLink(blob, downloadName);
        } else {
          throw new Error('Unrecognized zip data type');
        }
      })
      .catch((err) => {
        console.error(err);
      });
  } else {
    const json = JSON.stringify(updatedFeatureCollection, null, 2);
    const blob = new Blob([json], { type: 'application/geo+json' });
    const downloadName = `${filename ? filename : 'feature_collection'}.geojson`;
    createAndClickDownloadLink(blob, downloadName);
  }
}

/**
 * Creates temporary href and link for Blob that will be downloaded and clicks link.
 * Afterwards, the href and link are removed.
 * @param {Blob} blob Data to be downloaded.
 * @param {string} filename Filename for download.
 */
function createAndClickDownloadLink(blob: Blob, filename: string) {
  // create link to download geojson blob
  const href = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = href;
  link.download = filename;
  document.body.appendChild(link);
  // initiate download
  link.click();
  // clean up
  document.body.removeChild(link);
  URL.revokeObjectURL(href);
}
