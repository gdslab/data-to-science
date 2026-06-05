import { useEffect, useRef, useState } from 'react';

import api from '../../api';
import { DataProduct } from '../pages/workspace/projects/Project';

/** Minimal point type — only lng/lat are required for the sampling request. */
export type IdentifyPoint = {
  lng: number;
  lat: number;
};

export type PointValueResult = {
  coordinates: [number, number];
  values: (number | null)[];
};

type UsePointValueReturn = {
  data: PointValueResult | null;
  loading: boolean;
  error: boolean;
};

/**
 * Fetches the raster cell value(s) at a given point for a data product via
 * GET /public/point. Re-fetches whenever the point coordinates or data product
 * id change. Cancels stale in-flight requests on re-fire or cleanup.
 */
export function usePointValue(
  dataProduct: DataProduct | null,
  point: IdentifyPoint | null
): UsePointValueReturn {
  const [data, setData] = useState<PointValueResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    // clear state when tool is toggled off or no data product is selected
    if (!point || !dataProduct) {
      setData(null);
      setLoading(false);
      setError(false);
      return;
    }

    // cancel any in-flight request before starting a new one
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(false);
    setData(null);

    api
      .get<PointValueResult>('/public/point', {
        params: {
          data_product_id: dataProduct.id,
          lon: point.lng,
          lat: point.lat,
        },
        signal: controller.signal,
      })
      .then((res) => {
        setData(res.data);
        setLoading(false);
      })
      .catch((err) => {
        // ignore cancellation errors from rapid re-clicks
        if (err.code === 'ERR_CANCELED') return;
        setError(true);
        setLoading(false);
      });

    return () => {
      controller.abort();
    };
  }, [dataProduct?.id, point?.lng, point?.lat]);

  return { data, loading, error };
}
