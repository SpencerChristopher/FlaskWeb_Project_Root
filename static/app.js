// app.js - Modular SPA Core
import { ProfileView } from './js/views/ProfileView.js';

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

// --- Templates ---
const templates = {
    login: () => `
        <section class="py-5"><div class="container px-5"><div class="bg-light rounded-4 py-5 px-4 px-md-5">
            <div class="text-center mb-5"><h1 class="fw-bolder">Login</h1></div>
            <div class="row gx-5 justify-content-center"><div class="col-lg-8 col-xl-6">
                <form id="loginForm">
                    <div class="form-floating mb-3"><input class="form-control" id="username" type="text" placeholder="Username" required /><label for="username">Username</label></div>
                    <div class="form-floating mb-3"><input class="form-control" id="password" type="password" placeholder="Password" required /><label for="password">Password</label></div>
                    <button class="btn btn-primary btn-lg w-100" type="submit">Sign In</button>
                </form>
            </div></div></div></div></section>`,
    home: (d) => `
        <header class="py-5">
            <div class="container px-5 pb-5">
                <div class="row gx-5 align-items-center">
                    <div class="col-xxl-5">
                        <div class="text-center text-xxl-start">
                            <div class="badge bg-gradient-primary-to-secondary text-white mb-4"><div class="text-uppercase">${d.location}</div></div>
                            <h1 class="display-3 fw-bolder mb-5"><span class="text-gradient d-inline">${d.name}</span></h1>
                            <div class="fs-3 fw-light text-muted mb-5">${d.statement}</div>
                            <div class="d-flex justify-content-center justify-content-xxl-start gap-3 fs-2 mb-5">
                                ${d.social_links.github ? `<a class="text-gradient" href="${d.social_links.github}" target="_blank"><i class="bi-github"></i></a>` : ''}
                                ${d.social_links.linkedin ? `<a class="text-gradient" href="${d.social_links.linkedin}" target="_blank"><i class="bi-linkedin"></i></a>` : ''}
                                ${d.social_links.twitter ? `<a class="text-gradient" href="${d.social_links.twitter}" target="_blank"><i class="bi-twitter"></i></a>` : ''}
                                ${d.social_links.leetcode ? `<a class="text-gradient" href="${d.social_links.leetcode}" target="_blank"><i class="bi-code-slash"></i></a>` : ''}
                                ${d.social_links.kaggle ? `<a class="text-gradient" href="${d.social_links.kaggle}" target="_blank"><i class="bi-graph-up"></i></a>` : ''}
                                ${d.social_links.hackthebox ? `<a class="text-gradient" href="${d.social_links.hackthebox}" target="_blank"><i class="bi-box-seam"></i></a>` : ''}
                            </div>
                        </div>
                    </div>
                    <div class="col-xxl-7">
                        <div class="d-flex justify-content-center mt-5 mt-xxl-0">
                            <div class="profile bg-gradient-primary-to-secondary">
                                ${d.image_url ? `<img class="profile-img" src="${d.image_url}" alt="..." />` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </header>
        
        <section class="py-5 bg-light">
            <div class="container px-5">
                <div class="row gx-5 justify-content-center">
                    <div class="col-xxl-8">
                        <div class="text-center mb-5">
                            <h2 class="display-5 fw-bolder"><span class="text-gradient d-inline">Experience</span></h2>
                        </div>
                        ${d.work_history.map(w => `
                            <div class="card shadow border-0 rounded-4 mb-5">
                                <div class="card-body p-5">
                                    <div class="row align-items-center gx-5">
                                        <div class="col text-center text-lg-start mb-4 mb-lg-0">
                                            <div class="bg-light p-4 rounded-4">
                                                <div class="text-primary fw-bolder mb-2">${w.start_date} - ${w.end_date}</div>
                                                <div class="small fw-bolder">${w.role}</div>
                                                <div class="small text-muted">${w.company}</div>
                                                <div class="small text-muted">${w.location}</div>
                                            </div>
                                        </div>
                                        <div class="col-lg-8">
                                            <div>${w.description}</div>
                                            <div class="mt-3">
                                                ${w.skills.map(s => `<span class="badge bg-secondary me-1">${s}</span>`).join('')}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </section>`,
    blogList: (d) => `
        <section class="py-5"><div class="container px-5">
            <h2 class="display-4 fw-bolder mb-4">Latest Articles</h2>
            <div class="row gx-5">${d.posts.map(p => `
                <div class="col-lg-4 mb-5"><div class="card h-100 shadow border-0">
                    <div class="card-body p-4">
                        <div class="badge bg-primary bg-gradient rounded-pill mb-2">Article</div>
                        <a class="text-decoration-none link-dark stretched-link" href="#blog/${p.slug}"><h5 class="card-title mb-3">${p.title}</h5></a>
                        <p class="card-text mb-0">${p.summary}</p>
                    </div>
                </div></div>`).join('')}</div></div></section>`,
    blogPost: (p) => `
        <section class="py-5"><div class="container px-5">
            <div class="row gx-5 justify-content-center"><div class="col-lg-10 col-xl-8">
                <article>
                    <header class="mb-4"><h1 class="fw-bolder mb-1">${p.title}</h1><div class="text-muted fst-italic mb-2">Published on ${new Date(p.publication_date).toLocaleDateString()}</div></header>
                    <section class="mb-5"><p class="fs-5 mb-4">${p.content}</p></section>
                </article>
            </div></div></div></section>`
};

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
            mainContentElement.innerHTML = templates.home(await fetchAPI('/api/content/profile'));
        } else if (hash === '#blog') {
            mainContentElement.innerHTML = templates.blogList(await fetchAPI('/api/blog'));
        } else if (hash === '#login') {
            mainContentElement.innerHTML = templates.login();
            document.getElementById('loginForm').addEventListener('submit', handleLogin);
        } else if (hash === '#admin/profile') {
            const data = await fetchAPI('/api/content/profile');
            mainContentElement.innerHTML = ProfileView.template(data);
            ProfileView.bindEvents(fetchAPI, router);
        } else if (hash === '#admin/articles') {
            // Placeholder for article management view
            mainContentElement.innerHTML = '<div class="p-5 text-center"><h2>Article Management</h2><p>Coming soon...</p></div>';
        } else if (hash.startsWith('#blog/')) {
            const slug = hash.replace('#blog/', '');
            mainContentElement.innerHTML = templates.blogPost(await fetchAPI(`/api/blog/${slug}`));
        }
    } catch (err) {
        console.error("Router error:", err);
        mainContentElement.innerHTML = `<div class="p-5 text-center"><h3>Page not available</h3><p>${err.message}</p></div>`;
    }
}

// --- Initialization ---
window.addEventListener('hashchange', router);
initializeApp().then(router);
