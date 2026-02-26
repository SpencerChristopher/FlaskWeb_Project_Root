// app.js - SPA Wireframe Proof-of-Concept
document.addEventListener('DOMContentLoaded', () => {
    console.log("App.js Loaded - initializing...");

    // --- Application State ---
    let userState = {
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
            if (response.status === 204) return null;
            return await response.json();
        } catch (error) {
            console.error('API Fetch Error:', error);
            throw error;
        }
    }

    // --- TEMPLATES ---
    const templates = {
        home: (data) => {
            const socials = data.social_links || {};
            const socialHtml = Object.entries(socials).map(([p, url]) => 
                `<a class="btn btn-outline-light btn-social mx-1" href="${url}" target="_blank">
                    <i class="fa-brands fa-${p.toLowerCase()}"></i>
                </a>`).join('');
            
            const skills = (data.skills || []).map(s => `<span class="badge bg-primary m-1">${s}</span>`).join('');
            
            const profilePic = data.image_url 
                ? `<img class="img-fluid rounded-circle mb-4" src="${data.image_url}" style="width:150px;height:150px;object-fit:cover;border:3px solid white;">`
                : `<div class="rounded-circle bg-secondary d-inline-flex align-items-center justify-content-center mb-4" style="width:150px;height:150px;border:3px solid white;">
                    <i class="fas fa-user fa-4x text-white"></i></div>`;

            return `
            <header class="masthead">
                <div class="container px-4 px-lg-5 text-center">
                    <div class="row justify-content-center">
                        <div class="col-lg-8">
                            ${profilePic}
                            <h1 class="text-white font-weight-bold">${data.name || 'Chris Developer'}</h1>
                            <h3 class="text-white-75 mt-3">${data.location || 'Remote'}</h3>
                            <hr class="divider" />
                            <p class="text-white-75 mb-4">${data.statement || ''}</p>
                            <div class="mb-4">${skills}</div>
                            <div class="mb-5">${socialHtml}</div>
                            <a class="btn btn-primary btn-xl" href="#blog">View Blog</a>
                        </div>
                    </div>
                </div>
            </header>`;
        },
        blogList: (data) => {
            const posts = data.posts || [];
            const cards = posts.map(p => `
                <div class="col-md-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h4 class="card-title">${p.title}</h4>
                            <p class="text-muted small">${p.publication_date || 'Draft'}</p>
                            <p class="card-text">${p.summary}</p>
                            <a href="#blog/${p.slug}" class="btn btn-primary btn-sm">Read More</a>
                        </div>
                    </div>
                </div>`).join('');
            return `<section class="page-section bg-light"><div class="container">
                <h2 class="text-center">Blog</h2><hr class="divider" />
                <div class="row">${posts.length ? cards : '<p class="text-center">No posts.</p>'}</div>
            </div></section>`;
        },
        blogPost: (p) => `
            <section class="page-section"><div class="container">
                <h2 class="text-center">${p.title}</h2><hr class="divider" />
                <div class="row justify-content-center"><div class="col-lg-8">
                    <p class="text-muted text-center">${p.publication_date || 'Draft'}</p>
                    <div class="content mt-4">${p.content}</div>
                </div></div>
            </div></section>`,
        login: () => `
            <section class="page-section"><div class="container">
                <div class="row justify-content-center"><div class="col-lg-6">
                    <h2 class="text-center">Login</h2><hr class="divider" />
                    <form id="loginForm">
                        <div id="login-error" class="alert alert-danger" style="display:none;"></div>
                        <input type="text" id="username" class="form-control mb-3" placeholder="Username" required>
                        <input type="password" id="password" class="form-control mb-3" placeholder="Password" required>
                        <button type="submit" class="btn btn-primary w-100">Login</button>
                    </form>
                </div></div>
            </div></section>`,
        profileEdit: (d) => `
            <section class="page-section"><div class="container"><div class="row justify-content-center"><div class="col-lg-8">
                <h2>Edit Profile</h2><hr />
                <form id="profileForm">
                    <div id="profile-error" class="alert alert-danger" style="display:none;"></div>
                    <div class="mb-3 text-center">
                        <div id="image-preview" class="mb-2">${d.image_url ? `<img src="${d.image_url}" class="rounded-circle" style="width:80px;height:80px;">` : ''}</div>
                        <input type="hidden" id="p-img-url" value="${d.image_url || ''}">
                        <input type="file" id="p-file" class="form-control form-control-sm d-inline-block w-auto">
                        <button type="button" class="btn btn-sm btn-outline-info" id="p-upload">Upload</button>
                    </div>
                    <input type="text" id="p-name" class="form-control mb-2" value="${d.name}" placeholder="Name">
                    <input type="text" id="p-loc" class="form-control mb-2" value="${d.location}" placeholder="Location">
                    <textarea id="p-stmt" class="form-control mb-2" style="height:100px">${d.statement}</textarea>
                    <input type="text" id="p-skills" class="form-control mb-2" value="${(d.skills||[]).join(', ')}" placeholder="Skills (comma separated)">
                    <label class="small text-muted">Socials (JSON)</label>
                    <textarea id="p-soc" class="form-control mb-2 font-monospace">${JSON.stringify(d.social_links, null, 2)}</textarea>
                    <label class="small text-muted">Work History (JSON)</label>
                    <textarea id="p-work" class="form-control mb-2 font-monospace">${JSON.stringify(d.work_history, null, 2)}</textarea>
                    <button type="submit" class="btn btn-success w-100">Save Profile</button>
                </form>
            </div></div></div></section>`
    };

    // --- UI Update ---
    function updateNavUI() {
        const authLinks = document.querySelectorAll('.auth-link');
        authLinks.forEach(el => el.parentElement.remove());
        
        if (userState.loggedIn) {
            const caps = userState.user.capabilities || [];
            if (caps.includes('profile:manage')) {
                mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link auth-link" href="#admin/profile">Edit Profile</a></li>');
            }
            mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link auth-link" id="logout-btn" href="#">Logout</a></li>');
            document.getElementById('logout-btn').addEventListener('click', handleLogout);
        } else {
            mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link auth-link" href="#login">Admin</a></li>');
        }
    }

    // --- Actions ---
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

    async function handleImageUpload() {
        const fileInput = document.getElementById('p-file');
        if (!fileInput.files.length) return;
        const fd = new FormData();
        fd.append('file', fileInput.files[0]);
        try {
            const res = await fetchAPI('/api/content/media', { method: 'POST', body: fd });
            document.getElementById('p-img-url').value = res.url;
            document.getElementById('image-preview').innerHTML = `<img src="${res.url}" class="rounded-circle" style="width:80px;height:80px;">`;
            alert("Uploaded! Don't forget to save.");
        } catch (err) { alert(err.message); }
    }

    async function handleProfileSubmit(e) {
        e.preventDefault();
        try {
            const body = {
                name: document.getElementById('p-name').value,
                location: document.getElementById('p-loc').value,
                statement: document.getElementById('p-stmt').value,
                image_url: document.getElementById('p-img-url').value,
                skills: document.getElementById('p-skills').value.split(',').map(s=>s.trim()).filter(s=>s),
                social_links: JSON.parse(document.getElementById('p-soc').value),
                work_history: JSON.parse(document.getElementById('p-work').value)
            };
            await fetchAPI('/api/content/profile', { method: 'PUT', body: JSON.stringify(body) });
            alert("Profile Saved!");
            window.location.hash = '#home';
        } catch (err) { alert("Save failed: " + err.message); }
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
                mainContentElement.innerHTML = templates.profileEdit(await fetchAPI('/api/content/profile'));
                document.getElementById('profileForm').addEventListener('submit', handleProfileSubmit);
                document.getElementById('p-upload').addEventListener('click', handleImageUpload);
            } else if (hash.startsWith('#blog/')) {
                const slug = hash.replace('#blog/', '');
                mainContentElement.innerHTML = templates.blogPost(await fetchAPI(`/api/blog/${slug}`));
            }
        } catch (err) {
            console.error("Router error:", err);
            mainContentElement.innerHTML = `<div class="p-5 text-center"><h3>Page not available</h3><p>${err.message}</p></div>`;
        }
    }

    // --- Init ---
    async function initializeApp() {
        console.log("Fetching auth status...");
        try {
            const data = await fetchAPI('/api/auth/status', { suppressAuthRedirect: true });
            if (data && data.logged_in) {
                userState.loggedIn = true;
                userState.user = data.user;
                console.log("Logged in as:", data.user.username);
            }
        } catch (e) { console.warn("Init status check bypassed"); }
        finally {
            updateNavUI();
            window.addEventListener('hashchange', router);
            router();
        }
    }

    initializeApp();
});
