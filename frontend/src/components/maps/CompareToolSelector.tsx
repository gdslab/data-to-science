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
  const findDataProductsByFlight = (flightID: string) => {
    const f = flights.filter(({ id }) => id === flightID)[0];
    return f.data_products;
  };

  return (
    <div className={POSITION_CLASSES[position]}>
      <div className="leaflet-control leaflet-bar mb-4 w-64">
        <div className="grid grid-rows-2 gap-2 p-4 bg-zinc-200 shadow-md">
          <select
            className="h-10 p-1.5 font-semibold text-zinc-600 text-center border-2 border-zinc-300 rounded-md bg-white"
            aria-label="Select flight date"
            name={`flightCompare-${side}`}
            value={flight}
            onChange={(e) => {
              setFlight(e.target.value);
              const dataProducts = findDataProductsByFlight(e.target.value);
              if (dataProducts.length > 0) {
                setDataProduct(dataProducts[0].id);
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

          <select
            className="h-10 p-1.5 font-semibold text-zinc-600 text-center border-2 border-zinc-300 rounded-md bg-white"
            aria-label="Select data product"
            name={`dataProduct-${side}`}
            value={dataProduct}
            onChange={(e) => {
              setDataProduct(e.target.value);
            }}
          >
            {findDataProductsByFlight(flight).length > 0 ? (
              findDataProductsByFlight(flight).map((dOpt) => (
                <option key={`${dOpt.id}-side`} value={dOpt.id}>
                  {dOpt.data_type.toUpperCase()}
                </option>
              ))
            ) : (
              <option value="">Not available</option>
            )}
          </select>
        </div>
      </div>
    </div>
  );
}
