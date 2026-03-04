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

// --- DOM Element Cache ---
const mainNavList = document.querySelector('#navbarResponsive .navbar-nav');
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
    } else {
        mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link auth-link" href="#login">Admin</a></li>');
    }
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

// --- Router ---
async function router() {
    const hash = window.location.hash || '#home';
    console.log("Routing to:", hash);
    try {
        if (hash === '#home') {
            mainContentElement.innerHTML = HomeView.template(await fetchAPI('/api/content/profile'));
        } else if (hash === '#blog') {
            mainContentElement.innerHTML = ArticleListView.template(await fetchAPI('/api/blog'));
        } else if (hash === '#login') {
            mainContentElement.innerHTML = LoginView.template();
            document.getElementById('loginForm').addEventListener('submit', handleLogin);
        } else if (hash === '#admin/profile') {
            const data = await fetchAPI('/api/content/profile');
            mainContentElement.innerHTML = ProfileView.template(data);
            ProfileView.bindEvents(fetchAPI, router);
        } else if (hash === '#admin/articles') {
            mainContentElement.innerHTML = ContentManagerView.template();
        } else if (hash.startsWith('#blog/')) {
            const slug = hash.replace('#blog/', '');
            mainContentElement.innerHTML = ArticleDetailView.template(await fetchAPI(`/api/blog/${slug}`));
        }
    } catch (err) {
        console.error("Router error:", err);
        mainContentElement.innerHTML = `<div class="p-5 text-center"><h3>Page not available</h3><p>${err.message}</p></div>`;
    }
}

// --- Initialization ---
window.addEventListener('hashchange', router);
initializeApp().then(router);
