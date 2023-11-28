import { useEffect, useState } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet-side-by-side';

import CompareToolSelector from './CompareToolSelector';
import { getDataProductTileLayer } from './DataProductTileLayer';
import { Flight } from '../pages/projects/ProjectDetail';

interface SideBySideControl extends L.Control {
  _leftLayer: L.TileLayer;
  _leftLayers: L.TileLayer[];
  _rightLayer: L.TileLayer;
  _rightLayers: L.TileLayer[];
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

const getCOGTileLayers = (map: L.Map) => {
  let layers: L.TileLayer[] = [];
  map.eachLayer((layer: L.Layer) => {
    if (layer instanceof L.TileLayer) {
      if (layer.options.className === 'compare-tl') {
        layers.push(layer);
      }
    }
  });
  return layers;
};

export default function CompareTool({ flights }: { flights: Flight[] }) {
  const map = useMap();
  const [sideBySideControl, setSideBySideControl] = useState<SideBySideControl | null>(
    null
  );

  const getDataProductByFlight = (flightID: string): string => {
    const dataProducts = flights.filter(({ id }) => id === flightID)[0].data_products;
    if (dataProducts.length > 0) {
      const dataProductsGTIFF = dataProducts.filter(
        ({ data_type }) => data_type !== 'point_cloud'
      );
      if (dataProductsGTIFF.length > 0) {
        return dataProductsGTIFF[0].id;
      } else {
        return '';
      }
    } else {
      return '';
    }
  };

  const [flight1, setFlight1] = useState(flights[0].id);
  const [flight2, setFlight2] = useState(flights[0].id);
  const [dataProduct1, setDataProduct1] = useState(getDataProductByFlight(flight1));
  const [dataProduct2, setDataProduct2] = useState(getDataProductByFlight(flight2));

  useEffect(() => {
    // adds side by side comparison control to map
    if (sideBySideControl) {
      map.removeControl(sideBySideControl);
      map.removeLayer(sideBySideControl._leftLayer);
      map.removeLayer(sideBySideControl._rightLayer);
      setSideBySideControl(null);
    }

    if (!dataProduct1 || !dataProduct2) return;

    const layer1 = getLayerFromProps(flights, flight1, dataProduct1);
    const layer2 = getLayerFromProps(flights, flight2, dataProduct2);

    if (!map.hasLayer(layer1)) layer1.addTo(map);
    if (!map.hasLayer(layer2)) layer2.addTo(map);

    // @ts-ignore
    const control: SideBySideControl = L.control.sideBySide(layer1, layer2);
    setSideBySideControl(control);
    control.addTo(map);
  }, [dataProduct1, dataProduct2]);

  useEffect(() => {
    // effect prevents duplicate layers and slider bars
    let lid: string | undefined = undefined;
    let rid: string | undefined = undefined;

    if (sideBySideControl) {
      lid = sideBySideControl._leftLayers[0].options.id;
      rid = sideBySideControl._rightLayers[0].options.id;
    }

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

    if (document.getElementsByClassName('leaflet-sbs').length > 1) {
      document.getElementsByClassName('leaflet-sbs')[0].remove();
    }
  });

  useEffect(
    () => () => {
      // remove any active layers on unmount
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
