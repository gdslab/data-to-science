import axios, { AxiosResponse } from 'axios';
import { useLoaderData } from 'react-router-dom';

import StatCards from './StatCards';

import { SiteStatistics } from './DashboardTypes';

export async function loader() {
  const response: AxiosResponse<SiteStatistics> = await axios.get(
    `${import.meta.env.VITE_API_V1_STR}/admin/site_statistics`
  );
  if (response) {
    return response.data;
  } else {
    return [];
  }
}

export default function DashboardSiteStatistics() {
  const stats = useLoaderData() as SiteStatistics;

  return <StatCards stats={stats} />;
}
