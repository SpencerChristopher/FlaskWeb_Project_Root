// app.js - Modern SPA Core with Design Patterns
import { ProfileView } from './js/views/ProfileView.js';
import { HomeView } from './js/views/HomeView.js';
import { ArticleListView } from './js/views/ArticleListView.js';
import { ArticleDetailView } from './js/views/ArticleDetailView.js';
import { LoginView } from './js/views/LoginView.js';
import { ContentManagerView } from './js/views/ContentManagerView.js';
import { AuthService } from './js/services/AuthService.js';

console.log("App.js Module Loaded - initializing with Patterns...");

// --- Application State (Observable) ---
const auth = new AuthService(fetchAPI);

const consentState = {
    decided: false,
    allowsAuth: false
};

// --- DOM Element Cache ---
const mainNavList = document.getElementById('mainNavList');
const navToggle = document.getElementById('navToggle');
const mainContentElement = document.getElementById('main-content');

// --- Observer Subscription ---
// Automatically update navigation whenever auth state changes.
auth.subscribe((user, loggedIn) => {
    console.info("Auth state changed. Updating UI...", { loggedIn });
    updateNavUI();
    
    // Only re-route if we are already fully initialized AND on the home page.
    // This prevents jitter where startApp() and the observer both trigger router().
    const isHomePage = window.location.pathname === '/' || window.location.pathname === '/home';
    if (isHomePage && consentState.decided && !consentState.initializing) {
        console.debug("Home page auth change detected. Refreshing view...");
        router();
    }
});

// --- Helper Functions ---
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

async function fetchAPI(url, options = {}) {
    options.credentials = 'include';
    const headers = options.headers || {};
    const method = (options.method || 'GET').toUpperCase();

    if (!consentState.allowsAuth && method !== 'GET') {
        const error = new Error('Consent required for authenticated actions.');
        error.status = 403;
        throw error;
    }
    
    if (options.body instanceof FormData) {
        delete headers['Content-Type'];
    } else if (['POST', 'PUT', 'PATCH'].includes(method) && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }

    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
        const csrfToken = getCookie('csrf_access_token');
        if (csrfToken) headers['X-CSRF-TOKEN'] = csrfToken;
    }
    options.headers = headers;

    try {
        const response = await fetch(url, options);

        if (response.status === 401 && !headers['X-Is-Retry'] && !url.includes('/api/auth/refresh')) {
            console.warn('Session expired, attempting silent refresh...');
            try {
                const refreshRes = await fetch('/api/auth/refresh', { 
                    method: 'POST',
                    credentials: 'include',
                    headers: { 'X-CSRF-TOKEN': getCookie('csrf_refresh_token') }
                });
                
                if (refreshRes.ok) {
                    console.info('Refresh successful, retrying original request.');
                    options.headers = { ...headers, 'X-Is-Retry': 'true' };
                    return await fetchAPI(url, options);
                }
            } catch (refreshErr) {
                console.error('Silent refresh failed:', refreshErr);
            }
            auth.logout(); // Use service to notify listeners
            throw new Error('Session expired. Please login again.');
        }

        if (!response.ok) {
            if (response.status === 403) {
                const errorData = await response.json().catch(() => ({ message: 'Forbidden' }));
                const error = new Error(errorData.message || 'Access Denied');
                error.status = 403;
                throw error;
            }
            const errorData = await response.json().catch(() => ({ message: response.statusText }));
            const error = new Error(errorData.message || `Error ${response.status}`);
            error.status = response.status;
            throw error;
        }
        return response.status === 204 ? null : await response.json();
    } catch (err) {
        console.error(`API Error (${url}):`, err);
        throw err;
    }
}

function renderLoading() {
    return `
        <section class="py-5" data-test="view-loading">
            <div class="container px-5 text-center">
                <div class="spinner-border text-primary" role="status" aria-label="Loading"></div>
            </div>
        </section>`;
}

let currentViewCleanup = null;

// --- UI Actions ---
function updateNavUI() {
    if (!mainNavList) return;
    
    const authLinks = document.querySelectorAll('.auth-link');
    authLinks.forEach(el => el.parentElement.remove());
    
    if (auth.loggedIn) {
        if (auth.hasPermission('profile:manage')) {
            mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link auth-link" href="/admin/profile">Edit Profile</a></li>');
        }
        if (auth.hasPermission('content:manage')) {
            mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link auth-link" href="/admin/articles">Manage Articles</a></li>');
        }
        mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link auth-link" id="logout-btn" href="javascript:void(0)">Logout</a></li>');
        document.getElementById('logout-btn')?.addEventListener('click', () => auth.logout().then(() => navigate('/home')));
    } else if (consentState.allowsAuth) {
        mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link auth-link" href="/login">Admin</a></li>');
    }
}

if (navToggle && mainNavList) {
    navToggle.addEventListener('click', () => {
        const isOpen = mainNavList.classList.toggle('is-open');
        navToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
}

document.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    if (link && link.href && link.origin === window.location.origin && !link.hasAttribute('target')) {
        const href = link.getAttribute('href');
        if (href && (href.startsWith('#') || href.includes('#'))) return;

        const path = link.pathname;
        if (!path.startsWith('/api/') && !path.startsWith('/static/')) {
            e.preventDefault();
            if (path !== window.location.pathname) navigate(path);
        }
    }
});

async function handleLogin(e) {
    e.preventDefault();
    const [u, p] = [document.getElementById('username').value, document.getElementById('password').value];
    try {
        await auth.login(u, p); // Observer triggers re-render/nav-update
        navigate('/home');
    } catch (err) { alert(err.message); }
}

async function startApp(allowAuth) {
    consentState.initializing = true;
    consentState.allowsAuth = allowAuth;
    
    if (allowAuth) {
        try {
            await auth.checkStatus();
        } catch (err) {
            console.warn("Initial auth check failed, continuing as guest.");
        }
    } else {
        auth.user = null;
        auth._loggedIn = false;
        auth.notify();
    }
    
    consentState.decided = true;
    consentState.initializing = false;
    router(); // Single entry point for routing on startup
}

// --- Router Registry ---
const ROUTES = {
    '/': { view: HomeView, fetch: () => fetchAPI('/api/content/profile') },
    '/home': { view: HomeView, fetch: () => fetchAPI('/api/content/profile') },
    '/blog': { view: ArticleListView, fetch: () => fetchAPI('/api/blog') },
    '/login': { view: LoginView, auth: true },
    '/admin/profile': { view: ProfileView, auth: true, fetch: () => fetchAPI('/api/content/profile') },
    '/admin/articles': { view: ContentManagerView, auth: true },
    '/about': { view: { template: (d) => `<section class="py-5"><div class="container px-5"><h2 class="fw-bolder">${d.title}</h2><p class="lead">${d.content}</p></div></section>` }, fetch: () => fetchAPI('/api/about') },
    '/license': { view: { template: (d) => `<section class="py-5"><div class="container px-5"><h2 class="fw-bolder">${d.title}</h2><p>${d.content}</p><hr><p class="small text-muted">${d.copyright}</p></div></section>` }, fetch: () => fetchAPI('/api/license') },
    '/contact': { view: { template: () => `<section class="py-5"><div class="container px-5"><h2 class="fw-bolder">Contact</h2><p>Coming soon...</p></div></section>` } },
};

function navigate(path) {
    window.history.pushState({}, '', path);
    router();
}

async function router() {
    const path = window.location.pathname;
    if (currentViewCleanup) {
        currentViewCleanup();
        currentViewCleanup = null;
    }

    const controller = new AbortController();
    const viewContext = { api: fetchAPI, auth: auth, navigate, signal: controller.signal };
    currentViewCleanup = () => controller.abort();

    if (mainNavList) {
        mainNavList.classList.remove('is-open');
        navToggle?.setAttribute('aria-expanded', 'false');
    }

    try {
        let route = ROUTES[path];
        let data = null;

        if (!route && path.startsWith('/blog/')) {
            const slug = path.replace('/blog/', '');
            route = { view: ArticleDetailView, fetch: () => fetchAPI(`/api/blog/${slug}`) };
        }

        if (!route) {
            mainContentElement.innerHTML = `<div class="p-5 text-center"><h3>404 - Not Found</h3></div>`;
            return;
        }

        if (route.auth && !consentState.allowsAuth) {
            mainContentElement.innerHTML = `<div class="p-5 text-center"><h3>Consent Required</h3></div>`;
            return;
        }

        if (route.fetch) {
            mainContentElement.innerHTML = renderLoading();
            data = await route.fetch();
        }

        mainContentElement.innerHTML = route.view.template(data, auth);
        route.view.mount?.(viewContext, route.view === LoginView ? handleLogin : undefined);

    } catch (err) {
        console.error("Router error:", err);
        mainContentElement.innerHTML = `<div class="p-5 text-center"><h3>Page not available</h3><p>${err.message}</p></div>`;
    }
}

window.addEventListener('popstate', router);

// --- Cookie Consent ---
const consentKey = 'cookie_consent';
const dialog = document.getElementById('cookie-dialog');
const storageAvailable = (() => {
    try {
        localStorage.setItem('__test__', '1');
        localStorage.removeItem('__test__');
        return true;
    } catch (e) { return false; }
})();

const existingConsent = storageAvailable ? localStorage.getItem(consentKey) : null;
if (existingConsent === 'accepted') startApp(true);
else if (existingConsent === 'declined') startApp(false);
else if (dialog) {
    document.getElementById('cookie-accept')?.addEventListener('click', () => {
        if (storageAvailable) localStorage.setItem(consentKey, 'accepted');
        dialog.close();
        startApp(true);
    });
    document.getElementById('cookie-decline')?.addEventListener('click', () => {
        if (storageAvailable) localStorage.setItem(consentKey, 'declined');
        dialog.close();
        startApp(false);
    });
    dialog.showModal();
}

document.getElementById('manage-cookies')?.addEventListener('click', (e) => {
    e.preventDefault();
    dialog?.showModal();
});
