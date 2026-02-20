/**
 * Loads optional third-party scripts based on environment configuration.
 * Add new optional services here to keep main.tsx clean.
 */
export function loadExternalScripts(): void {
  // Cloudflare Turnstile - load script only when site key is configured at runtime
  fetch('/config.json')
    .then((response) => response.json())
    .then((config) => {
      if (config.turnstileSiteKey) {
        const script = document.createElement('script');
        script.src =
          'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);
      }
    })
    .catch((error) => {
      console.error('Failed to load config.json:', error);
    });

  // Future: Add analytics, error tracking, or other optional services here
}