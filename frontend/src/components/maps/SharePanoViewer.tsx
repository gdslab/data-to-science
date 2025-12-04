import { AxiosResponse } from 'axios';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation } from 'react-router';

import { DataProduct } from '../pages/projects/Project';
import { AlertBar, Status } from '../Alert';

import api from '../../api';

function useQuery() {
  const { search } = useLocation();

  return useMemo(() => new URLSearchParams(search), [search]);
}

export default function SharePanoViewer() {
  const [imageUrl, setImageUrl] = useState('');
  const [status, setStatus] = useState<Status | null>(null);
  const viewerRef = useRef<HTMLDivElement>(null);

  const query = useQuery();
  const fileID = query.get('file_id');

  useEffect(() => {
    async function fetchImage(fileID) {
      try {
        const response: AxiosResponse<DataProduct> = await api.get(
          `/public?file_id=${fileID}`
        );
        if (response.status === 200) {
          setImageUrl(response.data.url);
        } else {
          setStatus({ type: 'error', msg: 'Unable to load image' });
        }
      } catch {
        setStatus({ type: 'error', msg: 'Unable to load image' });
      }
    }

    if (fileID) {
      fetchImage(fileID);
    }
  }, [fileID]);

  useEffect(() => {
    if (!viewerRef.current || !imageUrl) return;

    // Load script dynamically
    const script = document.createElement('script');
    script.src = '/lib/pannellum/pannellum.js';
    script.async = true;
    script.onload = () => {
      if (window.pannellum) {
        window.pannellum.viewer(viewerRef.current, {
          type: 'equirectangular',
          panorama: imageUrl,
          autoLoad: true,
        });
      }
    };
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, [imageUrl]);

  return (
    <>
      <div ref={viewerRef} style={{ width: '100%', height: '100%' }} />
      {status && <AlertBar alertType={status.type}>{status.msg}</AlertBar>}
    </>
  );
}
