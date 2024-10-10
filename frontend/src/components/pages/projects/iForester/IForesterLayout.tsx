import axios, { AxiosResponse, isAxiosError } from 'axios';
import { useEffect } from 'react';
import { useParams } from 'react-router-dom';

import IForesterMap from './IForesterMap';
import { IForester } from '../Project';
import { IForesterControlProvider } from './IForesterContext';
import { useProjectContext } from '../ProjectContext';
import IForesterCardView from './IForesterCardView';

export default function IForesterLayout() {
  const { iforesterDispatch } = useProjectContext();

  const params = useParams();

  useEffect(() => {
    async function fetchIForesterData(projectId: string) {
      try {
        const response: AxiosResponse<IForester[]> = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}/iforester`
        );
        if (response.status === 200) {
          iforesterDispatch({ type: 'set', payload: response.data });
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

  return (
    <IForesterControlProvider>
      <div className="mx-4 min-h-full flex flex-col lg:flex-row">
        <div className="flex-1">
          <IForesterCardView />
        </div>
        <div className="flex-1 lg:w-1/2 lg:min-w-[400px]">
          <IForesterMap />
        </div>
      </div>
    </IForesterControlProvider>
  );
}
