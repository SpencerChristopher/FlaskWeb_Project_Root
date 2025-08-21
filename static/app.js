// app.js - SPA logic for the entire site.

document.addEventListener('DOMContentLoaded', () => {
    // --- Application State ---
    let userState = {
        loggedIn: false,
        user: null
    };

    // --- DOM Element Cache ---
    const mainNavList = document.querySelector('#navbarResponsive .navbar-nav');
    const mainContentElement = document.getElementById('main-content'); // Cache the main content element

    // --- Helper Functions ---
    async function fetchAPI(url, options = {}) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                let errorData;
                try {
                    errorData = await response.json();
                } catch (e) {
                    errorData = { message: response.statusText };
                }
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }
            if (response.status === 204 || response.headers.get("content-length") === "0") return null;
            return await response.json();
        } catch (error) {
            console.error('API Fetch Error:', error);
            throw error;
        }
    }

    // --- TEMPLATES (now returning only inner content for #main-content) ---
    const templates = {
        home: (data) => `
            <div class="container px-4 px-lg-5 h-100">
                <div class="row gx-4 gx-lg-5 h-100 align-items-center justify-content-center text-center">
                    <div class="col-lg-8 align-self-end">
                        <h1 class="text-white font-weight-bold">Home Page</h1>
                        <hr class="divider" />
                        <h2 class="text-white-75 mb-5">${data.title}</h2>
                    </div>
                    <div class="col-lg-8 align-self-baseline">
                        <p class="text-white-75 mb-5">${data.tagline}</p>
                        <p class="text-white-75 mb-5">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero. Sed cursus ante dapibus diam.</p>
                        <a class="btn btn-primary btn-xl" href="${data.button_link}">Find Out More</a>
                    </div>
                </div>
            </div>`,
        blogList: (posts) => {
            let postHtml = posts.map(post => `
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h4 class="card-title">${post.title}</h4>
                            <h6 class="card-subtitle mb-2 text-muted">${post.published_date || 'Draft'}</h6>
                            <p class="card-text">${post.summary}</p>
                            <a href="#blog/${post.slug}" class="btn btn-primary btn-sm">Read More</a>
                        </div>
                    </div>
                </div>`).join('');
            return `
                <div class="container px-4 px-lg-5">
                    <h1 class="text-center mt-0">Blog List Page</h1>
                    <hr class="divider" />
                    <p class="text-center mb-4">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero. Sed cursus ante dapibus diam.</p>
                    <div class="row gx-4 gx-lg-5 justify-content-center">
                        ${posts.length > 0 ? postHtml : '<p class="text-center">No posts yet!</p>'}
                    </div>
                </div>`;
        },
        blogPost: (post) => `
            <div class="container px-4 px-lg-5">
                <h1 class="text-center mt-0">Blog Post: ${post.title}</h1>
                <hr class="divider" />
                <div class="text-muted text-center mb-4">${post.published_date || 'Draft'}</div>
                <div class="row gx-4 gx-lg-5 justify-content-center">
                    <div class="col-lg-8">
                        <p><strong>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero. Sed cursus ante dapibus diam.</strong></p>
                        <hr/>
                        ${post.content}
                    </div>
                </div>
            </div>`,
        login: () => `
            <div class="container px-4 px-lg-5">
                <div class="row gx-4 gx-lg-5 justify-content-center">
                    <div class="col-lg-6 col-md-8">
                        <h1 class="text-center mt-0">Login Page</h1>
                        <hr class="divider" />
                        <p class="text-muted text-center mb-5">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero.</p>
                        <form id="loginForm">
                            <div id="login-error" class="text-danger mb-3 text-center" style="display:none;"></div>
                            <div class="form-floating mb-3">
                                <input class="form-control" id="username" type="text" placeholder="Username" required />
                                <label for="username">Username</label>
                            </div>
                            <div class="form-floating mb-3">
                                <input class="form-control" id="password" type="password" placeholder="Password" required />
                                <label for="password">Password</label>
                            </div>
                            <div class="d-grid">
                                <button class="btn btn-primary btn-xl" type="submit">Login</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>`,
        adminDashboard: (posts) => {
            const postRows = posts.map(post => `
                <tr data-post-id="${post._id.$oid}">
                    <td>${post.title}</td>
                    <td>${post.is_published ? '<span class="badge bg-success">Published</span>' : '<span class="badge bg-secondary">Draft</span>'}</td>
                    <td>${new Date(post.created_at.$date).toLocaleDateString()}</td>
                    <td>
                        <a href="#admin/edit/${post._id.$oid}" class="btn btn-sm btn-primary">Edit</a>
                        <button class="btn btn-sm btn-danger delete-btn">Delete</button>
                    </td>
                </tr>
            `).join('');
            return `
                <div class="container px-4 px-lg-5">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <h2 class="mt-0">Admin Dashboard</h2>
                        <a href="#admin/new" class="btn btn-primary">Create New Post</a>
                    </div>
                    <hr class="divider" />
                    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero. Sed cursus ante dapibus diam.</p>
                    <div class="table-responsive">
                        <table class="table table-striped table-hover">
                            <thead><tr><th>Title</th><th>Status</th><th>Created</th><th>Actions</th></tr></thead>
                            <tbody id="dashboard-tbody">
                                ${posts.length > 0 ? postRows : '<tr><td colspan="4" class="text-center">No posts found.</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>`;
        },
        postForm: (post = {}) => {
            const isEditing = post && post._id;
            const title = isEditing ? `Edit Post` : 'Create New Post';
            const buttonText = isEditing ? 'Update Post' : 'Create Post';
            return `
                <div class="container px-4 px-lg-5">
                    <h1 class="text-center mt-0">Post Editor</h1>
                    <h2 class="text-center mt-0">${title}</h2>
                    <hr class="divider" />
                    <p class="text-center mb-5">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero. Sed cursus ante dapibus diam.</p>
                    <div class="row gx-4 gx-lg-5 justify-content-center">
                        <div class="col-lg-8">
                            <form id="postForm" data-post-id="${isEditing ? post._id.$oid : ''}">
                                <div id="form-error" class="text-danger mb-3 text-center" style="display:none;"></div>
                                <div class="form-floating mb-3">
                                    <input class="form-control" id="title" type="text" value="${post.title || ''}" required />
                                    <label for="title">Title</label>
                                </div>
                                <div class="form-floating mb-3">
                                    <textarea class="form-control" id="content" style="height: 15rem" required>${post.content || ''}</textarea>
                                    <label for="content">Content</label>
                                </div>
                                <div class="form-check form-switch mb-3">
                                    <input class="form-check-input" type="checkbox" id="is_published" ${post.is_published ? 'checked' : ''}>
                                    <label class="form-check-label" for="is_published">Publish this post</label>
                                </div>
                                <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                                    <a href="#admin" class="btn btn-secondary">Cancel</a>
                                    <button class="btn btn-primary" type="submit">${buttonText}</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>`;
        },
        about: () => `
            <div class="container px-4 px-lg-5">
                <h1 class="text-center mt-0">About Us</h1>
                <hr class="divider" />
                <p class="text-center mb-5">This is the About page. More content coming soon!</p>
            </div>`,
        license: () => `
            <div class="container px-4 px-lg-5">
                <h1 class="text-center mt-0">License Information</h1>
                <hr class="divider" />
                <p class="text-center mb-5">This is the License page. Details about the project license will be here.</p>
            </div>`,
        contact: () => `
            <div class="container px-4 px-lg-5">
                <h1 class="text-center mt-0">Contact Us</h1>
                <hr class="divider" />
                <p class="text-center mb-5">This is the Contact page. You can reach us at contact@example.com.</p>
            </div>`
    };

    // --- UI Update Functions ---
    function updateNavUI() {
        mainNavList.querySelector('#admin-link')?.parentElement.remove();
        mainNavList.querySelector('#logout-link')?.parentElement.remove();
        if (userState.loggedIn) {
            mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link" id="admin-link" href="#admin">Dashboard</a></li>');
            mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link" id="logout-link" href="#">Logout</a></li>');
            mainNavList.querySelector('#logout-link').addEventListener('click', handleLogout);
        } else {
            mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link" id="admin-link" href="#login">Admin</a></li>');
        }
    }

    // --- Event Handlers ---
    async function handleLoginSubmit(event) {
        event.preventDefault();
        const [username, password] = [document.getElementById('username').value, document.getElementById('password').value];
        const errorDiv = document.getElementById('login-error');
        errorDiv.style.display = 'none';
        try {
            const data = await fetchAPI('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) });
            userState.loggedIn = true; userState.user = data.user;
            updateNavUI(); window.location.hash = '#admin';
        } catch (error) {
            errorDiv.textContent = error.message; errorDiv.style.display = 'block';
        }
    }

    async function handleLogout(event) {
        if(event) event.preventDefault();
        try {
            await fetchAPI('/api/auth/logout', { method: 'POST' });
            userState.loggedIn = false; userState.user = null;
            updateNavUI(); window.location.hash = '#home';
        } catch (error) { alert('Logout failed: ' + error.message); }
    }

    async function handlePostFormSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const postId = form.dataset.postId;
        const errorDiv = document.getElementById('form-error');
        errorDiv.style.display = 'none';

        const postData = {
            title: document.getElementById('title').value,
            content: document.getElementById('content').value,
            is_published: document.getElementById('is_published').checked
        };

        const url = postId ? `/api/admin/posts/${postId}` : '/api/admin/posts';
        const method = postId ? 'PUT' : 'POST';

        try {
            await fetchAPI(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(postData) });
            window.location.hash = '#admin';
        } catch (error) {
            errorDiv.textContent = error.message; errorDiv.style.display = 'block';
        }
    }

    async function handleDeletePost(event) {
        if (!event.target.classList.contains('delete-btn')) return;
        const row = event.target.closest('tr');
        const postId = row.dataset.postId;

        if (confirm('Are you sure you want to delete this post?')) {
            try {
                await fetchAPI(`/api/admin/posts/${postId}`, { method: 'DELETE' });
                row.remove(); // Remove from UI immediately
            } catch (error) {
                alert('Failed to delete post: ' + error.message);
            }
        }
    }

    // --- Router ---
    const routes = {
        '#home': async () => { mainContentElement.innerHTML = templates.home(await fetchAPI('/api/home')); },
        '#blog': async () => { mainContentElement.innerHTML = templates.blogList(await fetchAPI('/api/blog')); },
        '#blog/:slug': async (slug) => { mainContentElement.innerHTML = templates.blogPost(await fetchAPI(`/api/blog/${slug}`)); },
        '#login': () => { mainContentElement.innerHTML = templates.login(); document.getElementById('loginForm').addEventListener('submit', handleLoginSubmit); },
        '#admin': async () => {
            if (!userState.loggedIn) { window.location.hash = '#login'; return; }
            try {
                const posts = await fetchAPI('/api/admin/posts');
                mainContentElement.innerHTML = templates.adminDashboard(posts);
                document.getElementById('dashboard-tbody').addEventListener('click', handleDeletePost);
            } catch (error) { mainContentElement.innerHTML = `<p class="text-danger text-center">${error.message}</p>`; }
        },
        '#admin/new': () => {
            if (!userState.loggedIn) { window.location.hash = '#login'; return; }
            mainContentElement.innerHTML = templates.postForm();
            document.getElementById('postForm').addEventListener('submit', handlePostFormSubmit);
        },
        '#admin/edit/:id': async (id) => {
            if (!userState.loggedIn) { window.location.hash = '#login'; return; }
            try {
                const post = await fetchAPI(`/api/admin/posts/${id}`);
                mainContentElement.innerHTML = templates.postForm(post);
                document.getElementById('postForm').addEventListener('submit', handlePostFormSubmit);
            } catch (error) { mainContentElement.innerHTML = `<p class="text-danger text-center">${error.message}</p>`; }
        },
        '#about': () => { mainContentElement.innerHTML = templates.about(); },
        '#license': () => { mainContentElement.innerHTML = templates.license(); },
        '#contact': () => { mainContentElement.innerHTML = templates.contact(); }
    };

    async function router() {
        const path = window.location.hash || '#home';
        const [route, param, id] = path.split('/'); // e.g., #admin/edit/123

        let matchedRoute;
        if (route === '#admin' && param === 'edit' && id) {
            matchedRoute = routes['#admin/edit/:id'];
            await matchedRoute(id);
        } else if (route === '#admin' && param === 'new') {
            await routes['#admin/new']();
        } else if (routes[route + '/:slug'] && param) {
            await routes[route + '/:slug'](param);
        } else if (routes[route]) {
            await routes[route]();
        } else {
            window.location.hash = '#home';
        }
    }

    // --- App Initialization ---
    async function initializeApp() {
        try {
            const data = await fetchAPI('/api/auth/status');
            if (data.logged_in) { userState.loggedIn = true; userState.user = data.user; }
        } catch (error) {
            console.error("Could not verify auth status. Assuming logged out.", error);
        } finally {
            updateNavUI();
            window.addEventListener('hashchange', router);

            // Add a global click handler for all SPA links
            document.addEventListener('click', (event) => {
                const anchor = event.target.closest('a');
                if (anchor && anchor.getAttribute('href')?.startsWith('#')) {
                    event.preventDefault();
                    if (window.location.hash !== anchor.getAttribute('href')) {
                        window.location.hash = anchor.getAttribute('href');
                    }
                }
            });

            router(); // Initial route load
        }
    }

    initializeApp();
});
