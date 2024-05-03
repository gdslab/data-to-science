import axios, { AxiosResponse } from 'axios';

import SidePanel from './SidePanel';
import StatCards from './StatCards';

import { SiteStatistics } from './DashboardTypes';
import { useLoaderData } from 'react-router-dom';

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

export default function Dashboard() {
  const stats = useLoaderData() as SiteStatistics;
  return (
    <div className="flex flex-row h-full">
      <SidePanel />
      <StatCards stats={stats} />
    </div>
  );
}
