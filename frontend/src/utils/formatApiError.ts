import { isAxiosError } from 'axios';

import { ErrorResponseBody, ValidationError } from '../types/uppy';

const DEFAULT_FALLBACK = 'Unexpected error occurred. Please try again.';

// Convert an axios error into a safe, user-displayable string.
// Handles FastAPI's two response shapes: { detail: string } and the 422
// validation-error case where detail is an array of {loc, msg, type}.
// The array case must be flattened — passing it as a React child throws
// "Objects are not valid as a React child" and bubbles to error boundaries.
export function formatApiError(
  err: unknown,
  fallback: string = DEFAULT_FALLBACK
): string {
  if (!isAxiosError(err) || !err.response) return fallback;

  const body = err.response.data as ErrorResponseBody | undefined;
  const detail = body?.detail;
  if (!detail) return fallback;

  if (typeof detail === 'string') return detail;

  if (Array.isArray(detail)) {
    const errors = detail as ValidationError[];
    if (errors.length === 0) return fallback;

    return errors
      .map((e) => {
        const path = e.loc
          .filter((p, i) => !(i === 0 && p === 'body'))
          .join('.');
        return path ? `${path}: ${e.msg}` : e.msg;
      })
      .join('; ');
  }

  return fallback;
}
