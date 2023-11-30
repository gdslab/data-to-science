import { useState } from 'react';

import { Flight } from '../pages/projects/ProjectDetail';

const POSITION_CLASSES = {
  bottomleft: 'leaflet-bottom leaflet-left',
  bottomright: 'leaflet-bottom leaflet-right',
  topleft: 'leaflet-top leaflet-left',
  topright: 'leaflet-top leaflet-right',
};

interface Props {
  side: string;
  flight: string;
  flights: Flight[];
  dataProduct: string;
  position: string;
  setFlight: React.Dispatch<React.SetStateAction<string>>;
  setDataProduct: React.Dispatch<React.SetStateAction<string>>;
}

import { formatDate } from './LayerPane';

export default function CompareToolSelector({
  side,
  flight,
  flights,
  dataProduct,
  position,
  setFlight,
  setDataProduct,
}: Props) {
  const filterDataProductsByFlight = (dType: string, flightID: string) => {
    const f = flights.filter(({ id }) => id === flightID)[0];
    const dp = f.data_products.filter(({ data_type }) => data_type === dType);
    return dp;
  };

  const findDataProductType = (dataProductID: string, flightID: string): string => {
    const f = flights.filter(({ id }) => id === flightID)[0];
    const dp = f.data_products.filter(({ id }) => id === dataProductID);
    if (dp.length > 0) return dp[0].data_type;
  };

  const [dataTypeSelection, setDataTypeSelection] = useState(
    findDataProductType(dataProduct, flight)
  );

  return (
    <div className={POSITION_CLASSES[position]}>
      <div className="leaflet-control leaflet-bar mb-4">
        <div className="grid grid-rows-3 gap-2 p-4 bg-slate-200 shadow-md">
          <div className="flex flex-row items-center">
            <label className="mr-4">Flight</label>
            <select
              className="bg-slate-50 p-1.5 rounded"
              name={`flightCompare-${side}`}
              value={flight}
              onChange={(e) => {
                setFlight(e.target.value);
                const filteredDataProducts = filterDataProductsByFlight(
                  dataTypeSelection,
                  e.target.value
                );
                if (filteredDataProducts.length > 0) {
                  setDataProduct(filteredDataProducts[0].id);
                } else {
                  setDataProduct('');
                }
              }}
            >
              {flights.map((fOpt) => (
                <option key={`${fOpt.id}-side`} value={fOpt.id}>
                  {formatDate(fOpt.acquisition_date)}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-row items-center">
            <label className="mr-4">Data Type</label>
            <div className="grow grid grid-cols-2 gap-1.5">
              <div>
                <input
                  type="radio"
                  value="ortho"
                  checked={dataTypeSelection === 'ortho'}
                  disabled={filterDataProductsByFlight('ortho', flight).length < 1}
                  onChange={(e) => {
                    setDataTypeSelection(e.target.value);
                    const filteredDataProducts = filterDataProductsByFlight(
                      'ortho',
                      flight
                    );
                    if (filteredDataProducts.length > 0) {
                      setDataProduct(filteredDataProducts[0].id);
                    } else {
                      setDataProduct('');
                    }
                  }}
                />
                <label className="ml-1.5" htmlFor="ortho">
                  Ortho
                </label>
              </div>
              <div>
                <input
                  type="radio"
                  name={`datatype-${side}`}
                  value="dsm"
                  checked={dataTypeSelection === 'dsm'}
                  disabled={filterDataProductsByFlight('dsm', flight).length < 1}
                  onChange={(e) => {
                    setDataTypeSelection(e.target.value);
                    const filteredDataProducts = filterDataProductsByFlight(
                      'dsm',
                      flight
                    );
                    if (filteredDataProducts.length > 0) {
                      setDataProduct(filteredDataProducts[0].id);
                    } else {
                      setDataProduct('');
                    }
                  }}
                />
                <label className="ml-1.5" htmlFor="dsm">
                  DSM
                </label>
              </div>
            </div>
          </div>
          <div className="flex flex-row items-center">
            <label className="mr-4">Data Product</label>
            <select
              className="bg-slate-50 p-1.5 rounded grow"
              name={`dataProduct-${side}`}
              value={dataProduct}
              onChange={(e) => {
                setDataProduct(e.target.value);
              }}
            >
              {filterDataProductsByFlight(dataTypeSelection, flight).length > 0 ? (
                filterDataProductsByFlight(dataTypeSelection, flight).map((dOpt) => (
                  <option key={`${dOpt.id}-side`} value={dOpt.id}>
                    {dOpt.data_type}
                  </option>
                ))
              ) : (
                <option value="">Not available</option>
              )}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
