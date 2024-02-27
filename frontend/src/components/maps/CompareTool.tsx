import { useEffect, useState } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet-side-by-side';

import CompareToolSelector from './CompareToolSelector';
import { getDataProductTileLayer } from './DataProductTileLayer';
import { Flight } from '../pages/projects/Project';

interface SideBySideControl extends L.Control {
  _leftLayer: L.TileLayer;
  _leftLayers: L.TileLayer[];
  _rightLayer: L.TileLayer;
  _rightLayers: L.TileLayer[];
  _updateClip: () => void;
}

export const getFlightsWithGTIFF = (flights: Flight[]): Flight[] => {
  return flights.filter((flight) => {
    if (flight.data_products.length > 0) {
      const dataProducts = flight.data_products.filter(
        ({ data_type }) => data_type !== 'point_cloud'
      );
      if (dataProducts.length > 0) {
        return flight;
      }
    }
  });
};

const getLayerFromProps = (
  flights: Flight[],
  flightID: string,
  dataProductID: string
) => {
  const dataProduct = flights
    .filter(({ id }) => id === flightID)[0]
    .data_products.filter(({ id }) => id === dataProductID)[0];

  const tileLayer = getDataProductTileLayer(dataProduct);
  return L.tileLayer(tileLayer.props.url, {
    className: 'compare-tl',
    maxZoom: tileLayer.props.maxZoom,
    maxNativeZoom: tileLayer.props.maxNativeZoom,
    zIndex: tileLayer.props.zIndex,
  });
};

/**
 * Returns array of tile layers added by compare tool to current map.
 * @param {L.Map} map Leaflet map.
 * @returns {L.TileLayer[]} Array of tile layers added by compare tool.
 */
const getCOGTileLayers = (map: L.Map): L.TileLayer[] => {
  let layers: L.TileLayer[] = [];
  map.eachLayer((layer: L.Layer) => {
    if (layer instanceof L.TileLayer) {
      // only tile layers added by compare tool will have 'compare-tl' class
      if (layer.options.className === 'compare-tl') {
        layers.push(layer);
      }
    }
  });
  return layers;
};

// find ID of a dsm or ortho data product from a specific flight
const getDataProductByFlight = (flightID: string, flights: Flight[]): string => {
  const dataProducts = flights.filter(({ id }) => id === flightID)[0].data_products;
  if (dataProducts.length > 0) {
    // filter out any point cloud data products
    const dataProductsGTIFF = dataProducts.filter(
      ({ data_type }) => data_type !== 'point_cloud'
    );
    if (dataProductsGTIFF.length > 0) {
      // give preference to ortho over dsm
      const ortho = dataProductsGTIFF.filter(({ data_type }) => data_type === 'ortho');
      return ortho.length > 0 ? ortho[0].id : dataProductsGTIFF[0].id;
    } else {
      return '';
    }
  } else {
    return '';
  }
};

export default function CompareTool({
  flights,
  layerPaneHidden,
}: {
  flights: Flight[];
  layerPaneHidden: boolean;
}) {
  const map = useMap();
  const [dividerPosition, setDividerPosition] = useState<{
    divider: number;
    range: number;
  } | null>(null);
  const [sideBySideControl, setSideBySideControl] = useState<SideBySideControl | null>(
    null
  );
  const [flight1, setFlight1] = useState(flights[0].id);
  const [flight2, setFlight2] = useState(flights[0].id);
  const [dataProduct1, setDataProduct1] = useState(
    getDataProductByFlight(flight1, flights)
  );
  const [dataProduct2, setDataProduct2] = useState(
    getDataProductByFlight(flight2, flights)
  );

  // prevents sbs elements from moving out of position when layer pane hides/opens
  useEffect(() => {
    map.invalidateSize();
  }, [layerPaneHidden]);

  // adds side by side comparison control to map
  useEffect(() => {
    // if a sbs control already exists, remove it and its left/right layers
    if (sideBySideControl) {
      map.removeControl(sideBySideControl);
      if (sideBySideControl._leftLayer) map.removeLayer(sideBySideControl._leftLayer);
      if (sideBySideControl._rightLayer) map.removeLayer(sideBySideControl._rightLayer);
      setSideBySideControl(null);
    }

    // must have two data products to compare
    if (!dataProduct1 || !dataProduct2) return;

    // create tile layers for left/right data products
    // TODO: needs improvement
    const layer1 = getLayerFromProps(flights, flight1, dataProduct1);
    const layer2 = getLayerFromProps(flights, flight2, dataProduct2);

    // add layers to map if not already present on it
    if (!map.hasLayer(layer1)) layer1.addTo(map);
    if (!map.hasLayer(layer2)) layer2.addTo(map);

    // @ts-ignore -- add side by side control to map
    const sbsControl: SideBySideControl = L.control.sideBySide(layer1, layer2);
    setSideBySideControl(sbsControl);
    sbsControl.addTo(map);

    if (dividerPosition) {
      const sbsDividerEl = document.querySelector<HTMLElement>('.leaflet-sbs-divider');
      const sbsRangeEl = document.querySelector<HTMLInputElement>('.leaflet-sbs-range');
      if (sbsDividerEl && sbsRangeEl) {
        sbsDividerEl.style.left = `${dividerPosition.divider.toString()}px`;
        sbsRangeEl.value = dividerPosition.range.toString();
        // clips raster to new divider position
        sbsControl._updateClip();
      }
    }

    // @ts-ignore
    L.DomEvent.on(sbsControl, 'dividermove', ({ x }: { x: number }) => {
      const sbsDividerEl = document.querySelector<HTMLElement>('.leaflet-sbs-divider');
      const sbsRangeEl = document.querySelector<HTMLInputElement>('.leaflet-sbs-range');
      if (sbsDividerEl && sbsRangeEl) {
        setDividerPosition({ divider: x, range: parseFloat(sbsRangeEl.value) });
      }
    });
  }, [dataProduct1, dataProduct2]);

  // prevent duplicate layers and sbs bars
  useEffect(() => {
    let lid: string | undefined = undefined;
    let rid: string | undefined = undefined;
    // get tile layer id for active left and right layers
    if (sideBySideControl) {
      lid = sideBySideControl._leftLayers[0].options.id;
      rid = sideBySideControl._rightLayers[0].options.id;
    }

    // remove any COG tile layers with ids that do not match active left/right layers
    if (lid && rid) {
      const currentTileLayers = getCOGTileLayers(map);
      if (currentTileLayers.length > 2) {
        currentTileLayers.forEach((layer) => {
          if (sideBySideControl) {
            if (layer.options.id !== lid && layer.options.id !== rid) {
              layer.remove();
            }
          }
        });
      }
    }
  });

  // remove any active layers and sbs controls on unmount
  useEffect(
    () => () => {
      map.eachLayer((layer) => {
        if (layer instanceof L.TileLayer) {
          if (layer.options.className === 'compare-tl') layer.remove();
        }
      });
      if (document.getElementsByClassName('leaflet-sbs').length > 0) {
        document.getElementsByClassName('leaflet-sbs')[0].remove();
      }
    },
    []
  );

  return (
    <>
      <CompareToolSelector
        side="left"
        position="topleft"
        flights={flights}
        flight={flight1}
        setFlight={setFlight1}
        dataProduct={dataProduct1}
        setDataProduct={setDataProduct1}
      />
      <CompareToolSelector
        side="right"
        position="topright"
        flights={flights}
        flight={flight2}
        setFlight={setFlight2}
        dataProduct={dataProduct2}
        setDataProduct={setDataProduct2}
      />
    </>
  );
}

export function CompareToolAlert() {
  return (
    <div className="leaflet-top leaflet-left">
      <div className="leaflet-control leaflet-bar mb-4">
        <div className="p-4 bg-slate-200 shadow-md">
          <h1>No data products to compare</h1>
          <p>Upload DSM or ortho datasets to flights to use this tool.</p>
        </div>
      </div>
    </div>
  );
}
