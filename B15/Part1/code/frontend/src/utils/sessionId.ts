import { v4 as uuidv4 } from 'uuid';

const SESSION_ID_KEY = 'd2sSessionId';

// Return a stable, anonymous client session id, generating and persisting one in
// localStorage on first use. Used to attribute and de-duplicate views from users
// who are not signed in. A UUID (36 chars) fits the backend's 64-char limit.
export function getSessionId(): string {
  const existing = localStorage.getItem(SESSION_ID_KEY);
  if (existing) return existing;

  const sessionId = uuidv4();
  localStorage.setItem(SESSION_ID_KEY, sessionId);
  return sessionId;
}
