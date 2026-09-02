import axios from 'axios';
import { Feature } from 'geojson';
import { useCallback, useEffect, useState } from 'react';

import api from '../../api';
import { DataProduct, ZonalFeature } from '../pages/workspace/projects/Project';

type UseZonalStatisticsArgs = {
  /** Caller decides eligibility; the hook stays idle while false */
  enabled: boolean;
  dataProduct: DataProduct | null;
  projectId: string | null;
  feature: Feature;
};

export type ZonalStatisticsState = {
  data: ZonalFeature | null;
  loading: boolean;
  error: boolean;
  refetch: () => void;
};

/**
 * Fetches zonal statistics for a feature against a data product. Re-fetches
 * when the inputs change and cancels stale in-flight requests.
 */
export function useZonalStatistics({
  enabled,
  dataProduct,
  projectId,
  feature,
}: UseZonalStatisticsArgs): ZonalStatisticsState {
  const dataProductId = dataProduct?.id ?? null;
  const flightId = dataProduct?.flight_id ?? null;

  const [data, setData] = useState<ZonalFeature | null>(null);
  // Start in the loading state so the first paint already shows the skeleton
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState(false);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (!enabled || !dataProductId || !flightId || !projectId) {
      setData(null);
      setLoading(false);
      setError(false);
      return;
    }

    const controller = new AbortController();

    setLoading(true);
    setError(false);
    setData(null);

    api
      .post<ZonalFeature>(
        `/projects/${projectId}/flights/${flightId}/data_products/${dataProductId}/zonal_statistics`,
        feature,
        { signal: controller.signal }
      )
      .then((res) => {
        setData(res.data);
        setLoading(false);
      })
      .catch((err) => {
        if (axios.isCancel(err)) return;
        setError(true);
        setLoading(false);
      });

    return () => {
      controller.abort();
    };
  }, [enabled, dataProductId, flightId, projectId, feature, nonce]);

  const refetch = useCallback(() => setNonce((n) => n + 1), []);

  return { data, loading, error, refetch };
}
