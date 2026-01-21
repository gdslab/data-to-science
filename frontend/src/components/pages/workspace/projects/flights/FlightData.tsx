import { Params, useLoaderData } from 'react-router';

import FlightDataNav from './FlightDataNav';
import { useProjectContext } from '../ProjectContext';
import { DataProduct } from '../Project';
import FlightDataTabNav from './FlightDataTabNav';

import { RawDataProps } from './RawData/RawData.types';

import api from '../../../../../api';

export async function loader({ params }: { params: Params<string> }) {
  try {
    const [dataProducts, rawData] = await Promise.all([
      api.get(
        `/projects/${params.projectId}/flights/${params.flightId}/data_products`
      ),
      api.get(
        `/projects/${params.projectId}/flights/${params.flightId}/raw_data`
      ),
    ]);

    if (dataProducts && rawData) {
      return {
        dataProducts: dataProducts.data,
        rawData: rawData.data,
      };
    } else {
      return {
        dataProducts: [],
        rawData: [],
      };
    }
  } catch {
    console.error('Unable to retrieve raw data and data products');
    return {
      dataProducts: [],
      rawData: [],
    };
  }
}

export type FlightDataLoaderData = {
  dataProducts: DataProduct[];
  rawData: RawDataProps[];
};

export default function FlightData() {
  const { dataProducts, rawData } = useLoaderData() as FlightDataLoaderData;
  const { flights: contextFlights } = useProjectContext();

  return (
    <div className="flex flex-row h-full">
      {contextFlights && contextFlights.length > 0 ? <FlightDataNav /> : null}
      <div className="flex flex-col h-full w-full gap-4 p-4">
        <div className="grow min-h-0">
          <FlightDataTabNav dataProducts={dataProducts} rawData={rawData} />
        </div>
      </div>
    </div>
  );
}
