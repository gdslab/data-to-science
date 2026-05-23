import { useMemo } from 'react';
import { Layer, Source, useMap } from 'react-map-gl/maplibre';

import { DataProduct } from '../pages/workspace/projects/Project';
import {
  SingleBandSymbology,
  MultibandSymbology,
  useRasterSymbologyContext,
} from './RasterSymbologyContext';

import {
  getMultibandMinMax,
  getSingleBandMinMax,
  getTitilerQueryParams,
  isPublicOnly,
  isSingleBand,
} from './utils';
import { useMapLayerContext } from './MapLayersContext';
import { useMapContext } from './MapContext';

function constructRasterTileUrl(
  dataProduct: DataProduct,
  symbologySettings: SingleBandSymbology | MultibandSymbology | null,
  tileScale: number
): string {
  if (!symbologySettings) return '';

  // path to data product
  const cogUrl = dataProduct.filepath;

  // tile matrix set
  const tms = 'WebMercatorQuad';

  // parts of path for fetching tiles
  const resourcePath = `/cog/tiles/${tms}/{z}/{x}/{y}@${tileScale}x`;
  const basePath = window.location.origin;
  const queryParams = getTitilerQueryParams(
    cogUrl,
    dataProduct,
    symbologySettings
  );
  // add query params to base url
  const url = `${basePath}${resourcePath}?${queryParams.toString()}`;

  return url;
}

function constructPublicRasterTileUrl(
  dataProduct: DataProduct,
  symbologySettings: SingleBandSymbology | MultibandSymbology | null,
  tileScale: number
): string {
  if (!symbologySettings) return '';

  const apiV1Str = import.meta.env.VITE_API_V1_STR;
  const basePath = window.location.origin;
  const queryParams = new URLSearchParams();
  queryParams.append('data_product_id', dataProduct.id);
  queryParams.append('scale', tileScale.toString());

  if (isSingleBand(dataProduct)) {
    const s = symbologySettings as SingleBandSymbology;
    queryParams.append('bidx', '1');
    queryParams.append('colormap_name', s.colorRamp);
    queryParams.append(
      'rescale',
      getSingleBandMinMax(dataProduct.stac_properties, s).flat().join(',')
    );
  } else {
    const s = symbologySettings as MultibandSymbology;
    queryParams.append('bidx', s.red.idx.toString());
    queryParams.append('bidx', s.green.idx.toString());
    queryParams.append('bidx', s.blue.idx.toString());
    getMultibandMinMax(dataProduct.stac_properties, s).forEach((rescale) => {
      queryParams.append('rescale', `${rescale}`);
    });
  }

  return `${basePath}${apiV1Str}/public/maptiles?z={z}&x={x}&y={y}&${queryParams.toString()}`;
}

export default function ProjectRasterTiles({
  beforeLayerId = null,
  boundingBox = undefined,
  dataProduct,
}: {
  beforeLayerId?: string | null;
  boundingBox?: [number, number, number, number];
  dataProduct: DataProduct;
}) {
  const { current: map } = useMap();

  const { activeProject, tileScale } = useMapContext();
  const {
    state: { layers },
  } = useMapLayerContext();

  const { state } = useRasterSymbologyContext();

  const { isLoaded, symbology } = state[dataProduct.id] || {};

  const tiles = useMemo(
    () => [
      isPublicOnly(activeProject)
        ? constructPublicRasterTileUrl(dataProduct, symbology, tileScale)
        : constructRasterTileUrl(dataProduct, symbology, tileScale),
    ],
    [activeProject, dataProduct, symbology, tileScale]
  );

  // Calculate the beforeId for positioning the raster
  const calculatedBeforeId = useMemo(() => {
    if (!map) return undefined;

    // If beforeLayerId is explicitly provided, use it (e.g., for background rasters)
    if (beforeLayerId && map.getLayer(beforeLayerId)) {
      return beforeLayerId;
    }

    // Otherwise, find the first vector layer to position below all vectors
    const checkedLayers = layers.filter((layer) => layer.checked);

    if (checkedLayers.length === 0) return undefined;

    const orderedLayerIds = map.getLayersOrder();

    // Return the first checked layer that appears in the map's layer order
    // Also check for polygon border layers (they have -border suffix)
    for (const layerId of orderedLayerIds) {
      const matchedLayer = checkedLayers.find(
        (layer) =>
          layer.id === layerId ||
          (layer.type.toLowerCase() === 'polygon' &&
            `${layer.id}-border` === layerId)
      );
      if (matchedLayer) {
        return layerId; // Return the actual map layer ID, not the layer.id
      }
    }

    return undefined;
  }, [map, beforeLayerId, layers]);

  if (!symbology || !isLoaded || !map || !tiles) return null;

  return (
    <Source
      key={`${dataProduct.id}-source`}
      id={dataProduct.id}
      type="raster"
      tiles={tiles}
      maxzoom={24}
      minzoom={0}
      tileSize={256}
      {...(boundingBox ? { bounds: boundingBox } : {})}
    >
      <Layer
        key={`${dataProduct.id}-layer`}
        id={dataProduct.id}
        type="raster"
        source={dataProduct.id}
        paint={{
          'raster-opacity':
            symbology.opacity != null ? symbology.opacity / 100 : 1,
        }}
        beforeId={calculatedBeforeId}
      />
    </Source>
  );
}
