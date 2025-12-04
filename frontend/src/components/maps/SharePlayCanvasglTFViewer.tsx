import { AxiosResponse } from 'axios';
import { useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router';

import { AlertBar, Status } from '../Alert';
import PlayCanvasglTFViewer from './PlayCanvasglTFViewer';
import { DataProduct } from '../pages/projects/Project';

import api from '../../api';

function useQuery() {
  const { search } = useLocation();

  return useMemo(() => new URLSearchParams(search), [search]);
}

export default function SharePlayCanvasglTFViewer() {
  const [modelUrl, setModelUrl] = useState('');
  const [status, setStatus] = useState<Status | null>(null);

  const query = useQuery();
  const fileID = query.get('file_id');

  useEffect(() => {
    async function fetchUrl(id: string) {
      try {
        const response: AxiosResponse<DataProduct> = await api.get(
          `/public?file_id=${id}`
        );
        if (response.status === 200) {
          setModelUrl(response.data.url);
        } else {
          setStatus({ type: 'error', msg: 'Unable to load file' });
        }
      } catch {
        setStatus({ type: 'error', msg: 'Unable to load file' });
      }
    }

    if (fileID) {
      fetchUrl(fileID);
    }
  }, [fileID]);

  return (
    <>
      {modelUrl && <PlayCanvasglTFViewer src={modelUrl} />}
      {status && <AlertBar alertType={status.type}>{status.msg}</AlertBar>}
    </>
  );
}
