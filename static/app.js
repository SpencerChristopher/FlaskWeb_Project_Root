// app.js - Modern SPA Core with Design Patterns
import { AuthService } from './js/services/AuthService.js';
import { escapeHTML } from './js/utils/SecurityUtils.js';

console.log("App.js Module Loaded - initializing with Patterns...");

// --- Application State (Observable) ---
const auth = new AuthService(fetchAPI);

const consentState = {
    decided: false,
    allowsAuth: false,
    initializing: false
};

// Cache for bootstrap data to prevent double-fetching on first paint
let bootstrapCache = null;
// Cache for article metadata from the list view
const articleCache = new Map();

// --- DOM Element Cache ---
const mainNavList = document.getElementById('mainNavList');
const navToggle = document.getElementById('navToggle');
const mainContentElement = document.getElementById('main-content');

// --- Observer Subscription ---
// Automatically update navigation whenever auth state changes.
auth.subscribe((user, loggedIn) => {
    console.info("Auth state changed. Updating UI...", { loggedIn });
    updateNavUI();
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

        if (response.status === 401 && !headers['X-Is-Retry'] && !url.includes('/api/auth/refresh') && !url.includes('/api/auth/logout')) {
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

        if (response.status === 401 && (url.includes('/api/auth/refresh') || url.includes('/api/auth/logout'))) {
            console.warn('Authentication failed on refresh/logout. Clearing local state.');
            auth.user = null;
            auth.loggedIn = false;
            auth.notify();
            throw new Error('Session invalidated.');
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
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    try {
        await auth.login(username, password); // Observer triggers re-render/nav-update
        navigate('/home');
    } catch (err) { alert(err.message); }
}

async function startApp(allowAuth) {
    consentState.initializing = true;
    consentState.allowsAuth = allowAuth;
    
    if (allowAuth) {
        try {
            const boot = await fetchAPI('/api/bootstrap');
            auth.hydrate(boot.auth);
            bootstrapCache = boot.profile;
        } catch (err) {
            console.warn("Bootstrap failed, continuing as guest.");
        }
    } else {
        auth.user = null;
        auth._loggedIn = false;
        auth.notify();
    }
    
    consentState.decided = true;
    consentState.initializing = false;
    router();
}

// --- Router Registry (Dynamic Path Map) ---
const ROUTES = {
    '/': { module: './js/views/HomeView.js', name: 'HomeView', fetch: () => bootstrapCache || fetchAPI('/api/content/profile') },
    '/home': { module: './js/views/HomeView.js', name: 'HomeView', fetch: () => bootstrapCache || fetchAPI('/api/content/profile') },
    '/blog': { 
        module: './js/views/ArticleListView.js', 
        name: 'ArticleListView',
        fetch: async () => {
            const data = await fetchAPI('/api/blog');
            if (data?.posts) {
                data.posts.forEach(p => articleCache.set(p.slug, p));
            }
            return data;
        } 
    },
    '/login': { module: './js/views/LoginView.js', name: 'LoginView' },
    '/admin/profile': { module: './js/views/ProfileView.js', name: 'ProfileView', auth: true, fetch: () => bootstrapCache || fetchAPI('/api/content/profile') },
    '/admin/articles': { module: './js/views/ContentManagerView.js', name: 'ContentManagerView', auth: true },
    '/about': { module: './js/views/AboutView.js', name: 'AboutView', fetch: () => fetchAPI('/api/about') },
    '/license': { module: './js/views/LicenseView.js', name: 'LicenseView', fetch: () => fetchAPI('/api/license') },
    '/contact': { module: './js/views/ContactView.js', name: 'ContactView' },
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
        let ViewClass = null;

        // Special case for dynamic blog detail
        if (!route && path.startsWith('/blog/')) {
            const slug = path.replace('/blog/', '');
            const cached = articleCache.get(slug);
            
            const module = await import('./js/views/ArticleDetailView.js');
            ViewClass = module.ArticleDetailView;

            route = { 
                fetch: async () => {
                    const full = await fetchAPI(`/api/blog/${slug}`);
                    articleCache.set(slug, full);
                    return full;
                } 
            };
            
            if (cached && cached.content) {
                data = cached;
                route.fetch = null;
            }
        } else if (route) {
            // Lazy load the module using explicit export name
            const module = await import(route.module);
            ViewClass = module[route.name];
        }

        if (!ViewClass) {
            mainContentElement.innerHTML = `<div class="p-5 text-center"><h3>404 - Not Found</h3></div>`;
            return;
        }

        // --- Route Guards ---
        if (route.auth && !consentState.allowsAuth) {
            mainContentElement.innerHTML = `<div class="p-5 text-center"><h3>Consent Required</h3></div>`;
            return;
        }

        if (route.auth && !auth.loggedIn) {
            console.warn(`Unauthorized access to ${path}. Redirecting...`);
            navigate('/login');
            return;
        }

        // Reset Infinite Scroll state if we navigate AWAY from the blog
        if (path !== '/blog') {
            const listModule = await import('./js/views/ArticleListView.js').catch(() => null);
            if (listModule && listModule.ArticleListView) {
                listModule.ArticleListView.resetState?.();
            }
        }

        if (route.fetch) {
            mainContentElement.innerHTML = renderLoading();
            data = await (typeof route.fetch === 'function' ? route.fetch() : route.fetch);
            
            if (bootstrapCache && (path === '/' || path === '/home')) {
                bootstrapCache = null;
            }
        }

        mainContentElement.innerHTML = ViewClass.template(data, auth);
        ViewClass.mount?.(viewContext, route.name === 'LoginView' ? handleLogin : undefined);

    } catch (err) {
        console.error("Router error:", err);
        mainContentElement.innerHTML = `<div class="p-5 text-center"><h3>Page not available</h3><p>${escapeHTML(err.message)}</p></div>`;
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
