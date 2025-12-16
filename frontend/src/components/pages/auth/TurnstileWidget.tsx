import { useEffect, useRef, useState } from 'react';

// Extend Window interface for Turnstile API
declare global {
  interface Window {
    turnstile?: {
      render: (
        element: string | HTMLElement,
        options: {
          sitekey: string;
          theme?: string;
          size?: string;
          callback?: (token: string) => void;
          'error-callback'?: () => void;
          'expired-callback'?: () => void;
        }
      ) => string;
      remove: (widgetId: string) => void;
      reset: (widgetId: string) => void;
    };
  }
}

type TurnstileWidgetProps = {
  siteKey: string;
  onSuccess: (token: string) => void;
  onError?: () => void;
  onExpire?: () => void;
};

export default function TurnstileWidget({
  siteKey,
  onSuccess,
  onError,
  onExpire,
}: TurnstileWidgetProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const widgetIdRef = useRef<string | null>(null);
  const [apiReady, setApiReady] = useState(false);
  const successRef = useRef(onSuccess);
  const errorRef = useRef(onError);
  const expireRef = useRef(onExpire);

  useEffect(() => {
    successRef.current = onSuccess;
  }, [onSuccess]);

  useEffect(() => {
    errorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    expireRef.current = onExpire;
  }, [onExpire]);

  // Wait for the Turnstile script to finish loading
  useEffect(() => {
    if (window.turnstile) {
      setApiReady(true);
      return;
    }

    const script = document.querySelector<HTMLScriptElement>(
      'script[src^="https://challenges.cloudflare.com/turnstile/v0/api.js"]'
    );

    if (!script) return;

    const handleLoad = () => setApiReady(true);
    script.addEventListener('load', handleLoad);

    return () => {
      script.removeEventListener('load', handleLoad);
    };
  }, []);

  // Render the widget when the API is ready
  useEffect(() => {
    if (!apiReady || !containerRef.current || !window.turnstile) return;
    if (widgetIdRef.current) return;

    widgetIdRef.current = window.turnstile.render(containerRef.current, {
      sitekey: siteKey,
      theme: 'auto',
      size: 'flexible',
      callback: (token: string) => {
        successRef.current?.(token);
      },
      'error-callback': () => {
        errorRef.current?.();
      },
      'expired-callback': () => {
        expireRef.current?.();
      },
    });

    return () => {
      if (widgetIdRef.current && window.turnstile) {
        window.turnstile.remove(widgetIdRef.current);
        widgetIdRef.current = null;
      }
    };
  }, [apiReady, siteKey]);

  return <div className="cf-turnstile" ref={containerRef} />;
}
