import { AxiosResponse } from 'axios';
import { useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router';

import { DataProduct } from '../pages/workspace/projects/Project';
import { AlertBar, Status } from '../Alert';

import api from '../../api';
import LCCViewer from './LCCViewer';

function useQuery() {
  const { search } = useLocation();

  return useMemo(() => new URLSearchParams(search), [search]);
}

export default function ShareLCCViewer() {
  const [lccUrl, setLccUrl] = useState('');
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
          setLccUrl(response.data.url);
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
      {lccUrl && <LCCViewer lccUrl={lccUrl} />}
      {status && <AlertBar alertType={status.type}>{status.msg}</AlertBar>}
    </>
  );
}
