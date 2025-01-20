import clsx from 'clsx';
import { useMemo } from 'react';

import { MapComparisonState } from './CompareMap';
import { Flight } from '../../pages/projects/Project';

import { sorter } from '../../utils';

type ComparisonMapControlProps = {
  flights: Flight[];
  mapComparisonState: MapComparisonState;
  setMapComparisonState: React.Dispatch<React.SetStateAction<MapComparisonState>>;
  side: 'left' | 'right';
};

export default function CompareMapControl({
  flights,
  mapComparisonState,
  setMapComparisonState,
  side = 'left',
}: ComparisonMapControlProps) {
  // filter out flights with no data products or only point cloud data products
  const flightsWithRasters = useMemo(() => {
    return flights
      .filter(
        (flight) =>
          flight.data_products.filter(
            (data_product) => data_product.data_type !== 'point_cloud'
          ).length > 0
      )
      .sort((a, b) => sorter(a.acquisition_date, b.acquisition_date));
  }, [flights]);

  // create flight options for remaining flights that have raster data products
  const flightOptions = useMemo(() => {
    return flightsWithRasters.map((flight) => ({
      label: `${flight.acquisition_date}${flight.name ? ` (${flight.name})` : ''}`,
      value: flight.id,
    }));
  }, [flightsWithRasters]);

  /**
   * returns selected flight for 'side' or null if no flight is selected.
   * @param flightId Id of flight object to find.
   * @returns Flight object or null.
   */
  const findSelectedFlight = (flightId: string | undefined): Flight | null => {
    if (!flightId) return null;

    const selectedFlight = flightsWithRasters.filter(({ id }) => id === flightId);
    if (selectedFlight.length > 0) {
      return selectedFlight[0];
    } else {
      return null;
    }
  };

  // raster data product options for currently selected flight
  const dataProductOptions = useMemo(() => {
    return findSelectedFlight(mapComparisonState[side].flightId)
      ?.data_products.filter(({ data_type }) => data_type !== 'point_cloud')
      .map((dataProduct) => ({
        label: dataProduct.data_type,
        value: dataProduct.id,
      }));
  }, [flightOptions, mapComparisonState[side]]);

  return (
    <div
      className={clsx(
        'absolute top-2 bg-gray-200 rounded-md shadow-md px-3 py-3 min-w-80',
        {
          'left-14': side === 'left',
          'right-14': side === 'right',
        }
      )}
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
                <option key={dataProductOption.value} value={dataProductOption.value}>
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
