import { AxiosResponse } from 'axios';
import { useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router';

import { DataProduct } from '../pages/workspace/projects/Project';
import { AlertBar, Status } from '../Alert';

import api from '../../api';
import PlayCanvasViewer from './PlayCanvasViewer';

function useQuery() {
  const { search } = useLocation();

  return useMemo(() => new URLSearchParams(search), [search]);
}

export default function SharePlayCanvasViewer() {
  const [splatUrl, setSplatUrl] = useState('');
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
          setSplatUrl(response.data.url);
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
      {splatUrl && <PlayCanvasViewer splatUrl={splatUrl} />}
      {status && <AlertBar alertType={status.type}>{status.msg}</AlertBar>}
    </>
  );
}
