import axios from 'axios';
import { Params, useLoaderData } from 'react-router-dom';

import { DataProduct } from '../ProjectDetail';
import DataProducts from './dataProducts/DataProducts';
import RawData from './rawData/RawData';

export async function loader({ params }: { params: Params<string> }) {
  try {
    const dataProducts = await axios.get(
      `/api/v1/projects/${params.projectId}/flights/${params.flightId}/data_products`
    );
    const rawData = await axios.get(
      `/api/v1/projects/${params.projectId}/flights/${params.flightId}/raw_data`
    );
    if (dataProducts && rawData) {
      return { dataProducts: dataProducts.data, rawData: rawData.data };
    } else {
      return { dataProducts: [], rawData: [] };
    }
  } catch (err) {
    console.error('Unable to retrieve raw data and data products');
    return { dataProducts: [], rawData: [] };
  }
}

export interface DataProductStatus extends DataProduct {
  status: string;
}

export interface RawData {
  original_filename: string;
  url: string;
}

interface FlightData {
  dataProducts: DataProductStatus[];
  rawData: RawData[];
}

export default function FlightData() {
  const { dataProducts, rawData } = useLoaderData() as FlightData;
  return (
    <div className="p-4 grid grid-flow-row auto-rows-max gap-4">
      <RawData data={rawData} />
      <DataProducts data={dataProducts} />
    </div>
  );
}
