import { useState } from 'react';

import api from '../../api';
import { DataProduct } from '../pages/workspace/projects/Project';
import { Engagement } from './EngagementInline';

interface UseDataProductLikeResult {
  engagement: Engagement;
  toggleLike: () => void;
  pending: boolean;
}

// Manages the optimistic like state for a single data product. The view count
// is read live from props (it is never changed by the user here); the like
// state is held locally so it can flip immediately on click and roll back on
// error. Seed once per data product — render the consuming component keyed by
// dataProduct.id. Mirrors the optimistic pattern in ProjectCard.tsx.
export function useDataProductLike(
  dataProduct: DataProduct,
  projectId?: string,
  flightId?: string
): UseDataProductLikeResult {
  const [liked, setLiked] = useState<boolean>(!!dataProduct.liked);
  const [likeCount, setLikeCount] = useState<number>(
    dataProduct.like_count ?? 0
  );
  const [pending, setPending] = useState(false);

  const toggleLike = async () => {
    if (pending || !projectId || !flightId) return;

    const prevLiked = liked;
    const prevCount = likeCount;

    // Optimistic flip
    setLiked(!prevLiked);
    setLikeCount(prevLiked ? prevCount - 1 : prevCount + 1);
    setPending(true);

    const url = `/projects/${projectId}/flights/${flightId}/data_products/${dataProduct.id}/like`;
    try {
      const response = prevLiked ? await api.delete(url) : await api.post(url);
      // Reconcile with the authoritative server response
      setLiked(response.data.liked);
      setLikeCount(response.data.like_count);
    } catch {
      // Roll back on error
      setLiked(prevLiked);
      setLikeCount(prevCount);
    } finally {
      setPending(false);
    }
  };

  const engagement: Engagement = {
    likeCount,
    viewCount: dataProduct.view_count ?? 0,
    likedByMe: liked,
  };

  return { engagement, toggleLike, pending };
}
