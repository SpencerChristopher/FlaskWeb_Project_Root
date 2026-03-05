// app.js - Modular SPA Core
import { ProfileView } from './js/views/ProfileView.js';
import { HomeView } from './js/views/HomeView.js';
import { ArticleListView } from './js/views/ArticleListView.js';
import { ArticleDetailView } from './js/views/ArticleDetailView.js';
import { LoginView } from './js/views/LoginView.js';
import { ContentManagerView } from './js/views/ContentManagerView.js';

console.log("App.js Module Loaded - initializing...");

// --- Application State ---
const userState = {
    loggedIn: false,
    user: null
};

const consentState = {
    decided: false,
    allowsAuth: false
};

// --- DOM Element Cache ---
const mainNavList = document.getElementById('mainNavList');
const navToggle = document.getElementById('navToggle');
const mainContentElement = document.getElementById('main-content');

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
        if (!response.ok) {
            if ((response.status === 401 || response.status === 403) && !options.suppressAuthRedirect) {
                console.warn('Authentication error:', response.status);
                handleLogout(null, true);
                throw new Error('Authentication required.');
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
    const authLinks = document.querySelectorAll('.auth-link');
    authLinks.forEach(el => el.parentElement.remove());
    
    if (userState.loggedIn) {
        const caps = userState.user.capabilities || [];
        if (caps.includes('profile:manage')) {
            mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link auth-link" href="#admin/profile">Edit Profile</a></li>');
        }
        if (caps.includes('content:manage')) {
            mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link auth-link" href="#admin/articles">Manage Articles</a></li>');
        }
        mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link auth-link" id="logout-btn" href="#">Logout</a></li>');
        document.getElementById('logout-btn').addEventListener('click', handleLogout);
    } else if (consentState.allowsAuth) {
        mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link auth-link" href="#login">Admin</a></li>');
    }
}

if (navToggle && mainNavList) {
    navToggle.addEventListener('click', () => {
        const isOpen = mainNavList.classList.toggle('is-open');
        navToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
    mainNavList.addEventListener('click', (e) => {
        if (e.target.tagName === 'A') {
            mainNavList.classList.remove('is-open');
            navToggle.setAttribute('aria-expanded', 'false');
        }
    });
}

async function handleLogout(e, force=false) {
    if (e) e.preventDefault();
    if (!force) await fetchAPI('/api/auth/logout', { method: 'POST' }).catch(() => {});
    userState.loggedIn = false;
    userState.user = null;
    updateNavUI();
    window.location.hash = '#home';
}

async function handleLogin(e) {
    e.preventDefault();
    const [u, p] = [document.getElementById('username').value, document.getElementById('password').value];
    try {
        await fetchAPI('/api/auth/login', { method: 'POST', body: JSON.stringify({username:u, password:p}) });
        await initializeApp();
        window.location.hash = '#home';
    } catch (err) { alert(err.message); }
}

async function initializeApp() {
    try {
        const status = await fetchAPI('/api/auth/status', { suppressAuthRedirect: true });
        userState.loggedIn = status.logged_in;
        userState.user = status.user;
        updateNavUI();
    } catch (err) {
        userState.loggedIn = false;
        updateNavUI();
    }
}

function startApp(allowAuth) {
    consentState.decided = true;
    consentState.allowsAuth = allowAuth;
    if (allowAuth) {
        initializeApp().then(router);
    } else {
        userState.loggedIn = false;
        userState.user = null;
        updateNavUI();
        router();
    }
}

// --- Router ---
async function router() {
    const hash = window.location.hash || '#home';
    console.log("Routing to:", hash);
    if (currentViewCleanup) {
        currentViewCleanup();
        currentViewCleanup = null;
    }

    const controller = new AbortController();
    const viewContext = {
        api: fetchAPI,
        userState,
        navigate: (target) => { window.location.hash = target; },
        signal: controller.signal,
    };
    currentViewCleanup = () => controller.abort();

    try {
        if (hash === '#home') {
            mainContentElement.innerHTML = renderLoading();
            const data = await fetchAPI('/api/content/profile');
            mainContentElement.innerHTML = HomeView.template(data);
            HomeView.mount?.(viewContext);
        } else if (hash === '#blog') {
            mainContentElement.innerHTML = renderLoading();
            const data = await fetchAPI('/api/blog');
            mainContentElement.innerHTML = ArticleListView.template(data);
            ArticleListView.mount?.(viewContext);
        } else if (hash === '#login') {
            if (!consentState.allowsAuth) {
                mainContentElement.innerHTML = `<div class="p-5 text-center"><h3>Consent Required</h3><p>Please accept cookies to access admin features.</p></div>`;
                return;
            }
            mainContentElement.innerHTML = LoginView.template();
            LoginView.mount?.(viewContext, handleLogin);
        } else if (hash === '#admin/profile') {
            if (!consentState.allowsAuth) {
                mainContentElement.innerHTML = `<div class="p-5 text-center"><h3>Consent Required</h3><p>Please accept cookies to access admin features.</p></div>`;
                return;
            }
            mainContentElement.innerHTML = renderLoading();
            const data = await fetchAPI('/api/content/profile');
            mainContentElement.innerHTML = ProfileView.template(data);
            ProfileView.mount?.(viewContext);
        } else if (hash === '#admin/articles') {
            if (!consentState.allowsAuth) {
                mainContentElement.innerHTML = `<div class="p-5 text-center"><h3>Consent Required</h3><p>Please accept cookies to access admin features.</p></div>`;
                return;
            }
            mainContentElement.innerHTML = ContentManagerView.template();
            ContentManagerView.mount?.(viewContext);
        } else if (hash.startsWith('#blog/')) {
            const slug = hash.replace('#blog/', '');
            mainContentElement.innerHTML = renderLoading();
            const data = await fetchAPI(`/api/blog/${slug}`);
            mainContentElement.innerHTML = ArticleDetailView.template(data);
            ArticleDetailView.mount?.(viewContext);
        }
    } catch (err) {
        console.error("Router error:", err);
        mainContentElement.innerHTML = `<div class="p-5 text-center"><h3>Page not available</h3><p>${err.message}</p></div>`;
    }
}

// --- Initialization ---
window.addEventListener('hashchange', router);

// --- Cookie Consent (blocking overlay) ---
const consentKey = 'cookie_consent';
const dialog = document.getElementById('cookie-dialog');
const storageAvailable = (() => {
    try {
        const testKey = '__consent_test__';
        localStorage.setItem(testKey, '1');
        localStorage.removeItem(testKey);
        return true;
    } catch (err) {
        return false;
    }
})();
const existingConsent = storageAvailable ? localStorage.getItem(consentKey) : null;
const manageCookiesLink = document.getElementById('manage-cookies');
let consentHandlersBound = false;

function bindConsentHandlers() {
    if (!dialog || consentHandlersBound) return;
    const acceptBtn = document.getElementById('cookie-accept');
    const declineBtn = document.getElementById('cookie-decline');
    const message = document.getElementById('cookie-message');
    if (acceptBtn) {
        acceptBtn.addEventListener('click', () => {
            if (storageAvailable) {
                localStorage.setItem(consentKey, 'accepted');
            }
            dialog.close();
            document.body.style.overflow = '';
            startApp(true);
        });
    }
    if (declineBtn) {
        declineBtn.addEventListener('click', () => {
            if (storageAvailable) {
                localStorage.setItem(consentKey, 'declined');
            }
            if (message) {
                message.textContent = 'Cookies declined. Admin features are disabled. You can still browse public content.';
            }
            dialog.close();
            document.body.style.overflow = '';
            startApp(false);
        });
    }
    consentHandlersBound = true;
}

if (existingConsent === 'accepted') {
    startApp(true);
} else if (existingConsent === 'declined') {
    startApp(false);
} else if (dialog) {
    bindConsentHandlers();
    dialog.showModal();
    document.body.style.overflow = 'hidden';
}

if (manageCookiesLink) {
    manageCookiesLink.addEventListener('click', (e) => {
        e.preventDefault();
        if (!dialog) return;
        bindConsentHandlers();
        const message = document.getElementById('cookie-message');
        if (message) {
            message.textContent = 'This site uses essential cookies for authentication and security. By continuing, you consent to these cookies.';
        }
        dialog.showModal();
        document.body.style.overflow = 'hidden';
    });
}
