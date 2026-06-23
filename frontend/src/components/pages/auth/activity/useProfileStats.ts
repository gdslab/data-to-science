import { AxiosResponse, isAxiosError } from 'axios';
import { useEffect, useState } from 'react';

import api from '../../../../api';
import { ProfileStats } from './types';

interface UseProfileStatsResult {
  data: ProfileStats | null;
  loading: boolean;
  error: boolean;
}

/**
 * Fetch the bundled profile stats payload once when `enabled` first becomes
 * true (i.e. the Activity tab is opened). Both segments read from the single
 * response, so switching segments never refetches.
 */
export default function useProfileStats(
  enabled: boolean,
): UseProfileStatsResult {
  const [data, setData] = useState<ProfileStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [hasFetched, setHasFetched] = useState(false);

  useEffect(() => {
    if (!enabled || hasFetched) return;

    let cancelled = false;
    setLoading(true);
    setError(false);

    async function fetchStats() {
      try {
        const response: AxiosResponse<ProfileStats> = await api.get(
          '/users/current/stats',
        );
        if (cancelled) return;
        setData(response.data);
        setHasFetched(true);
      } catch (err) {
        if (cancelled) return;
        if (isAxiosError(err) && err.response) {
          console.error(err.response.data);
        } else {
          console.error(err);
        }
        setError(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchStats();

    return () => {
      cancelled = true;
    };
  }, [enabled, hasFetched]);

  return { data, loading, error };
}
