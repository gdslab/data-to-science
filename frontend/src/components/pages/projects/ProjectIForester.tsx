import axios, { AxiosResponse, isAxiosError } from 'axios';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import { IForester } from './Project';
import IForesterList from './iForester/IForesterList';

export default function ProjectIForester() {
  const [iforesterData, setIForesterData] = useState<IForester[] | null>(null);

  const params = useParams();

  useEffect(() => {
    async function fetchIForesterData(projectId: string) {
      try {
        const response: AxiosResponse<IForester[]> = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}/iforester`
        );
        if (response.status === 200) {
          setIForesterData(response.data);
        } else {
          return [];
        }
      } catch (err) {
        if (isAxiosError(err) && err.response) {
          console.error(err.response.data);
        } else {
          console.error(err);
        }
        return [];
      }
    }
    if (params.projectId) {
      fetchIForesterData(params.projectId);
    }
  }, []);

  if (!iforesterData) return <span className="text-lg font-semibold">No data</span>;
  if (iforesterData) return <IForesterList data={iforesterData} />;
}
