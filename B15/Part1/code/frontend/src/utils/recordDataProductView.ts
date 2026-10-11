import api from '../api';
import { getSessionId } from './sessionId';

// Record a view for a data product. A single code path serves every caller:
// the api instance sends the auth cookie (withCredentials) so the backend
// attributes signed-in viewers by user, while the X-Session-Id header covers
// anonymous viewers. The public endpoint never returns 401, so the api
// instance's refresh/redirect interceptor is not triggered.
//
// View recording is best-effort — failures (e.g. 404 for an unauthorized or
// unpublished product) are swallowed and never surfaced to the user.
//
// Returns the authoritative view count from the response (so callers can update
// state without an extra fetch), or null if the request failed.
export async function recordDataProductView(
  dataProductId: string
): Promise<number | null> {
  try {
    const response = await api.post(
      `/public/data_products/${dataProductId}/view`,
      null,
      { headers: { 'X-Session-Id': getSessionId() } }
    );
    return typeof response.data?.view_count === 'number'
      ? response.data.view_count
      : null;
  } catch {
    // Intentionally ignored: view tracking must not disrupt the viewer.
    return null;
  }
}
