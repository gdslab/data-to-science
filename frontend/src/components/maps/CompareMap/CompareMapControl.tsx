import clsx from 'clsx';
import { useMemo } from 'react';

import { MapComparisonState } from './CompareMap';
import { Flight } from '../../pages/projects/Project';

import { sorter } from '../../utils';

type CompareMapControlProps = {
  flights: Flight[];
  mapComparisonState: MapComparisonState;
  setMapComparisonState: React.Dispatch<
    React.SetStateAction<MapComparisonState>
  >;
  side: 'left' | 'right';
};

export default function CompareMapControl({
  flights,
  mapComparisonState,
  setMapComparisonState,
  side = 'left',
}: CompareMapControlProps) {
  // filter out flights with no data products or only point cloud data products
  const flightsWithRasters = useMemo(() => {
    return flights
      .filter(
        (flight) =>
          flight.data_products.filter(
            (data_product) =>
              data_product.data_type !== 'point_cloud' &&
              data_product.data_type !== 'panoramic' &&
              data_product.data_type !== '3dgs'
          ).length > 0
      )
      .sort((a, b) => sorter(a.acquisition_date, b.acquisition_date));
  }, [flights]);

  // create flight options for remaining flights that have raster data products
  const flightOptions = useMemo(() => {
    return flightsWithRasters.map((flight) => ({
      label: `${flight.acquisition_date}${
        flight.name ? ` (${flight.name})` : ''
      }`,
      value: flight.id,
    }));
  }, [flightsWithRasters]);

  // raster data product options for currently selected flight
  const dataProductOptions = useMemo(() => {
    const flightId = mapComparisonState[side].flightId;
    if (!flightId) return undefined;

    const selectedFlight = flightsWithRasters.find(({ id }) => id === flightId);
    if (!selectedFlight) return undefined;

    return selectedFlight.data_products
      .filter(
        ({ data_type }) =>
          data_type !== 'point_cloud' &&
          data_type !== 'panoramic' &&
          data_type !== '3dgs'
      )
      .map((dataProduct) => ({
        label: dataProduct.data_type,
        value: dataProduct.id,
      }));
  }, [flightsWithRasters, mapComparisonState, side]);

  return (
    <div
      className={clsx(
        'absolute top-2 bg-gray-200 rounded-md shadow-md px-3 py-3 min-w-80',
        {
          'left-14': side === 'left',
          'right-14': side === 'right',
        }
      )}
      style={{ zIndex: 1001 }}
    >
      <div className="w-full flex flex-col gap-2">
        <select
          className="w-full px-8 font-semibold text-gray-600 text-center truncate border-2 border-gray-300 rounded-md bg-white"
          aria-label="Select flight date"
          name={`${side}FlightSelection`}
          value={mapComparisonState[side].flightId}
          onChange={(event) => {
            const updatedMapComparisonState = {
              ...mapComparisonState,
              [side]: {
                ...mapComparisonState[side],
                flightId: event.target.value,
                dataProductId: '',
              },
            };
            setMapComparisonState(updatedMapComparisonState);
          }}
        >
          <>
            {
              <option
                value=""
                disabled={mapComparisonState[side].flightId !== undefined}
              >
                Select date
              </option>
            }
            {flightOptions.map((flightOption) => (
              <option key={flightOption.value} value={flightOption.value}>
                {flightOption.label}
              </option>
            ))}
          </>
        </select>
        {dataProductOptions && dataProductOptions.length > 0 && (
          <select
            className="w-full px-8 font-semibold text-gray-600 text-center truncate border-2 border-gray-300 rounded-md bg-white"
            aria-label="Select data product"
            name={`${side}DataProductSelection`}
            value={mapComparisonState[side].dataProductId}
            onChange={(event) => {
              const updatedMapComparisonState = {
                ...mapComparisonState,
                [side]: {
                  ...mapComparisonState[side],
                  dataProductId: event.target.value,
                },
              };
              setMapComparisonState(updatedMapComparisonState);
            }}
          >
            <>
              <option
                value=""
                disabled={mapComparisonState[side].dataProductId !== undefined}
              >
                Select data product
              </option>
              {dataProductOptions.map((dataProductOption) => (
                <option
                  key={dataProductOption.value}
                  value={dataProductOption.value}
                >
                  {dataProductOption.label.toUpperCase()}
                </option>
              ))}
            </>
          </select>
        )}
      </div>
    </div>
  );
}
