import { useState, useCallback, useEffect, useRef } from 'react';

import { BreedBaseOAuthMessage, BreedBaseOAuthStatus } from './BreedBase.types';

type OAuthHosts = Record<string, { authorizeUrl: string }>;

const TOKEN_KEY_PREFIX = 'breedbase-oauth-token:';

function getHostname(url: string): string | null {
  try {
    return new URL(url).hostname;
  } catch {
    return null;
  }
}

function parseOAuthHosts(value: string | undefined): OAuthHosts {
  if (!value) return {};
  try {
    return JSON.parse(value) as OAuthHosts;
  } catch {
    return {};
  }
}

export function useBreedBaseOAuth() {
  const [authStatus, setAuthStatus] = useState<BreedBaseOAuthStatus>('none');
  const [popupBlocked, setPopupBlocked] = useState(false);
  const [oauthHosts, setOAuthHosts] = useState<OAuthHosts>({});
  const listenerRef = useRef<((event: MessageEvent) => void) | null>(null);

  // Load OAuth hosts from build-time env or runtime config.json
  useEffect(() => {
    if (import.meta.env.VITE_BREEDBASE_OAUTH_HOSTS) {
      setOAuthHosts(
        parseOAuthHosts(import.meta.env.VITE_BREEDBASE_OAUTH_HOSTS)
      );
    } else {
      fetch('/config.json')
        .then((response) => response.json())
        .then((config) => {
          if (config.breedbaseOAuthHosts) {
            setOAuthHosts(config.breedbaseOAuthHosts);
          }
        })
        .catch((error) => {
          console.error('Failed to load config.json:', error);
        });
    }
  }, []);

  const requiresOAuth = useCallback(
    (url: string): boolean => {
      const hostname = getHostname(url);
      if (!hostname) return false;
      return Object.keys(oauthHosts).some((host) => hostname.includes(host));
    },
    [oauthHosts]
  );

  const getToken = useCallback((hostname: string): string | null => {
    return sessionStorage.getItem(`${TOKEN_KEY_PREFIX}${hostname}`);
  }, []);

  const setToken = useCallback((hostname: string, token: string): void => {
    sessionStorage.setItem(`${TOKEN_KEY_PREFIX}${hostname}`, token);
  }, []);

  const clearToken = useCallback((hostname: string): void => {
    sessionStorage.removeItem(`${TOKEN_KEY_PREFIX}${hostname}`);
  }, []);

  const getAuthorizeUrl = useCallback(
    (breedbaseUrl: string): string => {
      const hostname = getHostname(breedbaseUrl);
      if (!hostname) return '';

      const oauthHost = Object.keys(oauthHosts).find((host) =>
        hostname.includes(host)
      );
      if (!oauthHost) return '';

      const { authorizeUrl } = oauthHosts[oauthHost];
      const callbackUrl = `${window.location.origin}/api/v1/breedbase_connections/oauth/callback`;
      return `${authorizeUrl}?redirect_uri=${encodeURIComponent(callbackUrl)}`;
    },
    [oauthHosts]
  );

  const checkAuth = useCallback(
    (breedbaseUrl: string): void => {
      if (!requiresOAuth(breedbaseUrl)) {
        setAuthStatus('none');
        return;
      }

      const hostname = getHostname(breedbaseUrl);
      if (!hostname) return;

      const token = getToken(hostname);
      if (token) {
        setAuthStatus('authenticated');
      } else {
        setAuthStatus('none');
      }
    },
    [requiresOAuth, getToken]
  );

  const expireAuth = useCallback(
    (breedbaseUrl: string): void => {
      const hostname = getHostname(breedbaseUrl);
      if (hostname) {
        clearToken(hostname);
      }
      setAuthStatus('expired');
    },
    [clearToken]
  );

  const startOAuth = useCallback(
    (breedbaseUrl: string): void => {
      setPopupBlocked(false);
      const url = getAuthorizeUrl(breedbaseUrl);
      if (!url) return;

      // Clean up any previous listener
      if (listenerRef.current) {
        window.removeEventListener('message', listenerRef.current);
      }

      const hostname = getHostname(breedbaseUrl);
      if (!hostname) return;

      const listener = (event: MessageEvent) => {
        if (event.origin !== window.location.origin) return;

        const data = event.data as BreedBaseOAuthMessage;
        if (data?.type !== 'breedbase-oauth-callback') return;

        if (data.status === '200' && data.accessToken) {
          setToken(hostname, data.accessToken);
          setAuthStatus('authenticated');
        } else {
          setAuthStatus('none');
        }

        window.removeEventListener('message', listener);
        listenerRef.current = null;
      };

      listenerRef.current = listener;
      window.addEventListener('message', listener);

      const popup = window.open(url, 'breedbase-oauth', 'width=600,height=700');
      if (!popup) {
        setPopupBlocked(true);
        window.removeEventListener('message', listener);
        listenerRef.current = null;
      }
    },
    [getAuthorizeUrl, setToken]
  );

  // Clean up listener on unmount
  useEffect(() => {
    return () => {
      if (listenerRef.current) {
        window.removeEventListener('message', listenerRef.current);
      }
    };
  }, []);

  return {
    authStatus,
    popupBlocked,
    requiresOAuth,
    startOAuth,
    getToken,
    getAuthorizeUrl,
    checkAuth,
    expireAuth,
  };
}
