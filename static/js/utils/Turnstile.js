let turnstileLoadPromise = null;

function getConfig() {
    return window.APP_CONFIG || {};
}

export function getTurnstileSiteKey() {
    return getConfig().turnstileSiteKey || '';
}

export function isTurnstileEnabled() {
    return !!getTurnstileSiteKey() && getConfig().turnstileEnabled !== false;
}

export function loadTurnstile() {
    if (window.turnstile) return Promise.resolve(window.turnstile);
    if (turnstileLoadPromise) return turnstileLoadPromise;

    turnstileLoadPromise = new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
        script.async = true;
        script.defer = true;
        script.onload = () => resolve(window.turnstile);
        script.onerror = () => reject(new Error('Failed to load Turnstile'));
        document.head.appendChild(script);
    });

    return turnstileLoadPromise;
}

export async function renderTurnstile(container, callbacks = {}) {
    const siteKey = getTurnstileSiteKey();
    if (!container || !siteKey) return null;

    const turnstile = await loadTurnstile();
    if (!turnstile) return null;

    return turnstile.render(container, {
        sitekey: siteKey,
        ...callbacks
    });
}
