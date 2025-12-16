/**
 * Loads optional third-party scripts based on environment configuration.
 * Add new optional services here to keep main.tsx clean.
 */
export function loadExternalScripts(): void {
  // Cloudflare Turnstile
  const turnstileSiteKey = import.meta.env.VITE_TURNSTILE_SITE_KEY;
  if (turnstileSiteKey) {
    const script = document.createElement('script');
    script.src =
      'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
  }

  // Future: Add analytics, error tracking, or other optional services here
}
