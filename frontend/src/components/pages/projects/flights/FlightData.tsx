import axios from 'axios';
import { Params, useLoaderData } from 'react-router-dom';

import FlightDataNav from './FlightDataNav';
import { useProjectContext } from '../ProjectContext';
import { DataProduct } from '../Project';
import FlightDataTabNav from './FlightDataTabNav';

import { RawDataProps } from './RawData/RawData.types';

export async function loader({ params }: { params: Params<string> }) {
  try {
    const dataProducts = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}/flights/${
        params.flightId
      }/data_products`
    );
    const rawData = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}/flights/${
        params.flightId
      }/raw_data`
    );
    if (dataProducts && rawData) {
      return {
        dataProducts: dataProducts.data,
        rawData: rawData.data,
      };
    } else {
      return { dataProducts: [], rawData: [] };
    }
  } catch (err) {
    console.error('Unable to retrieve raw data and data products');
    return { dataProducts: [], rawData: [] };
  }
}

export type FlightData = {
  dataProducts: DataProduct[];
  rawData: RawDataProps[];
};

export default function FlightData() {
  const { dataProducts, rawData } = useLoaderData() as FlightData;
  const { flights } = useProjectContext();

  return (
    <div className="flex flex-row h-full">
      {flights && flights.length > 0 ? <FlightDataNav /> : null}
      <div className="flex flex-col h-full w-full gap-4 p-4">
        <div className="grow min-h-0">
          <FlightDataTabNav dataProducts={dataProducts} rawData={rawData} />
        </div>
      </div>
    </div>
  );
}
