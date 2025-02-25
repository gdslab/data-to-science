import { AxiosResponse, isAxiosError } from 'axios';
import { useEffect } from 'react';
import { useParams } from 'react-router-dom';

import IForesterMap from './IForesterMap';
import { IForester } from '../Project';
import { IForesterControlProvider } from './IForesterContext';
import { useProjectContext } from '../ProjectContext';
import IForesterCardView from './IForesterCardView';

import api from '../../../../../api';

export default function IForesterLayout() {
  const { iforesterDispatch } = useProjectContext();

  const params = useParams();

  useEffect(() => {
    async function fetchIForesterData(projectId: string) {
      try {
        const response: AxiosResponse<IForester[]> = await api.get(
          `/projects/${projectId}/iforester`
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
      <div className="mx-4 h-full flex flex-col lg:flex-row pb-4">
        <div className="flex-none h-full lg:flex-1 lg:w-1/2 lg:min-w-[400px] mb-4 lg:mb-0">
          <IForesterCardView />
        </div>
        <div className="flex-none h-full lg:flex-1 lg:w-1/2 lg:min-w-[400px] pb-4 lg:pb-0 overflow-auto">
          <IForesterMap />
        </div>
      </div>
    </IForesterControlProvider>
  );
}
