import axios from 'axios';
import { Params, useLoaderData } from 'react-router-dom';

import { DataProduct } from '../ProjectDetail';
import DataProducts from './dataProducts/DataProducts';
import RawData from './rawData/RawData';
import { User } from '../../../../AuthContext';

export async function loader({ params }: { params: Params<string> }) {
  const profile = localStorage.getItem('userProfile');
  const user: User | null = profile ? JSON.parse(profile) : null;
  if (!user) return { dataProducts: [], rawData: [], role: 'viewer' };
  try {
    const projectMember = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}/members/${
        user.id
      }`
    );
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
    if (dataProducts && rawData && projectMember) {
      return {
        dataProducts: dataProducts.data,
        rawData: rawData.data,
        role: projectMember.data.role,
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
  original_filename: string;
  url: string;
}

interface FlightData {
  dataProducts: DataProductStatus[];
  rawData: RawData[];
  role: string;
}

export default function FlightData() {
  const { dataProducts, rawData, role } = useLoaderData() as FlightData;
  return (
    <div className="p-4 grid grid-flow-row auto-rows-max gap-4">
      <RawData data={rawData} role={role} />
      <DataProducts data={dataProducts} role={role} />
    </div>
  );
}
