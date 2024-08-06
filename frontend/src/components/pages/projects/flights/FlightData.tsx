import axios from 'axios';
import { useState } from 'react';
import { Params, useLoaderData } from 'react-router-dom';

import DataProducts from './dataProducts/DataProducts';
import FlightDataNav from './FlightDataNav';
import RawData from './rawData/RawData';
import { useProjectContext } from '../ProjectContext';

import { DataProduct } from '../Project';
import FlightDataTabNav from './FlightDataTabNav';

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
      return { dataProducts: [], rawData: [], role: 'viewer' };
    }
  } catch (err) {
    console.error('Unable to retrieve raw data and data products');
    return { dataProducts: [], rawData: [], role: 'viewer' };
  }
}

export interface DataProductStatus extends DataProduct {
  status: string;
}

export interface RawData {
  id: string;
  original_filename: string;
  status: string;
  url: string;
}

interface FlightData {
  dataProducts: DataProductStatus[];
  rawData: RawData[];
}

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
