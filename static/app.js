// app.js - SPA logic for the entire site.

document.addEventListener('DOMContentLoaded', () => {
    // --- Application State ---
    let userState = {
        loggedIn: false,
        user: null,
        accessToken: null,
        refreshToken: null
    };

    // --- DOM Element Cache ---
    const mainNavList = document.querySelector('#navbarResponsive .navbar-nav');
    const mainContentElement = document.getElementById('main-content');

    // --- Helper Functions ---
    async function fetchAPI(url, options = {}) {
        const headers = options.headers || {};
        if (userState.accessToken) {
            headers['Authorization'] = `Bearer ${userState.accessToken}`;
        }
        options.headers = headers;

        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                // Don't force a logout for specific auth actions that are expected to fail.
                if ((response.status === 401 || response.status === 403) && !options.suppressAuthRedirect) {
                    console.warn('Authentication error:', response.status);
                    handleLogout(null, true);
                    throw new Error('Authentication required or forbidden.');
                }
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

    function renderPagination(pagination) {
        if (!pagination || pagination.total_pages <= 1) return '';
        let pageLinks = '';
        for (let i = 1; i <= pagination.total_pages; i++) {
            pageLinks += `<li class="page-item ${i === pagination.current_page ? 'active' : ''}"><a class="page-link" href="#blog/page/${i}">${i}</a></li>`;
        }
        return `
            <nav aria-label="Blog navigation">
                <ul class="pagination justify-content-center">
                    <li class="page-item ${!pagination.has_prev ? 'disabled' : ''}">
                        <a class="page-link" href="#blog/page/${pagination.current_page - 1}" aria-label="Previous">&laquo;</a>
                    </li>
                    ${pageLinks}
                    <li class="page-item ${!pagination.has_next ? 'disabled' : ''}">
                        <a class="page-link" href="#blog/page/${pagination.current_page + 1}" aria-label="Next">&raquo;</a>
                    </li>
                </ul>
            </nav>
        `;
    }

    // --- TEMPLATES ---
    const templates = {
        home: (data) => `
            <header class="masthead">
                <div class="container px-4 px-lg-5 h-100">
                    <div class="row gx-4 gx-lg-5 h-100 align-items-center justify-content-center text-center">
                        <div class="col-lg-8 align-self-end">
                            <h1 class="text-white font-weight-bold">${data.title}</h1>
                            <hr class="divider" />
                        </div>
                        <div class="col-lg-8 align-self-baseline">
                            <p class="text-white-75 mb-5">${data.tagline}</p>
                            <a class="btn btn-primary btn-xl" href="${data.button_link}">Find Out More</a>
                        </div>
                    </div>
                </div>
            </header>`,
        blogList: (data) => {
            const { posts, pagination } = data;
            let postHtml = posts.map(post => `
                <div class="col-lg-4 col-md-6 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h4 class="card-title">${post.title}</h4>
                            <h6 class="card-subtitle mb-2 text-muted">${post.publication_date ? new Date(post.publication_date).toLocaleDateString() : 'Not Published'}</h6>
                            <p class="card-text">${post.summary}</p>
                            <a href="#blog/${post.slug}" class="btn btn-primary btn-sm">Read More</a>
                        </div>
                    </div>
                </div>`).join('');
            return `
                <section class="page-section bg-light" id="blog">
                    <div class="container px-4 px-lg-5">
                        <h2 class="text-center mt-0">Our Blog</h2>
                        <hr class="divider" />
                        <div class="row gx-4 gx-lg-5 justify-content-center">
                            ${posts.length > 0 ? postHtml : '<p class="text-center">No posts yet!</p>'}
                        </div>
                        <div class="row gx-4 gx-lg-5 justify-content-center mt-4">
                            <div class="col-auto">${renderPagination(pagination)}</div>
                        </div>
                    </div>
                </section>`;
        },
        blogPost: (post) => `
            <section class="page-section">
                <div class="container px-4 px-lg-5">
                    <h2 class="text-center mt-0">${post.title}</h2>
                    <hr class="divider" />
                    <div class="text-muted text-center mb-4">Published on ${post.publication_date ? new Date(post.publication_date).toLocaleDateString() : 'Not Published'}</div>
                    <div class="row gx-4 gx-lg-5 justify-content-center">
                        <div class="col-lg-8">${post.content}</div>
                    </div>
                </div>
            </section>`,
        login: () => `
            <section class="page-section">
                <div class="container px-4 px-lg-5">
                    <div class="row gx-4 gx-lg-5 justify-content-center">
                        <div class="col-lg-6 col-md-8">
                            <h2 class="text-center mt-0">Admin Login</h2>
                            <hr class="divider" />
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
                                <div class="d-grid"><button class="btn btn-primary btn-xl" type="submit">Login</button></div>
                            </form>
                        </div>
                    </div>
                </div>
            </section>`,
        adminDashboard: (posts) => {
            const postRows = posts.map(post => `
                <tr data-post-id="${post.id}">
                    <td>${post.title}</td>
                    <td>${post.is_published ? '<span class="badge bg-success">Published</span>' : '<span class="badge bg-secondary">Draft</span>'}</td>
                    <td>${new Date(post.publication_date).toLocaleDateString()}</td>
                    <td>
                        <button class="btn btn-sm btn-primary edit-btn">Edit</button>
                        <button class="btn btn-sm btn-danger delete-btn">Delete</button>
                    </td>
                </tr>`).join('');
            return `
                <section class="page-section bg-light" id="admin-dashboard">
                    <div class="container px-4 px-lg-5">
                        <div class="d-flex justify-content-between align-items-center mb-4">
                            <h2 class="mt-0 mb-0">Admin Dashboard</h2>
                            <a href="#account" class="btn btn-secondary">Change Password</a>
                        </div>
                        <hr class="divider" />
                        <div class="row gx-4 gx-lg-5 justify-content-center mb-5">
                            <div class="col-lg-8">
                                <h3 id="form-title" class="text-center">Create New Post</h3>
                                <form id="postForm">
                                    <div id="form-error" class="text-danger mb-3 text-center" style="display:none;"></div>
                                    <div class="form-floating mb-3">
                                        <input class="form-control" id="title" type="text" placeholder="Title" required />
                                        <label for="title">Title</label>
                                    </div>
                                    <div class="form-floating mb-3">
                                        <textarea class="form-control" id="summary" placeholder="Post summary" style="height: 5rem" required></textarea>
                                        <label for="summary">Summary</label>
                                    </div>
                                    <div class="form-floating mb-3">
                                        <textarea class="form-control" id="content" placeholder="Post content" style="height: 10rem" required></textarea>
                                        <label for="content">Content</label>
                                    </div>
                                    <div class="form-check form-switch mb-3">
                                        <input class="form-check-input" type="checkbox" id="is_published">
                                        <label class="form-check-label" for="is_published">Publish this post</label>
                                    </div>
                                    <div class="d-grid" id="form-buttons"><button class="btn btn-primary" type="submit">Create Post</button></div>
                                </form>
                            </div>
                        </div>
                        <hr class="divider" />
                        <h3 class="text-center">Existing Posts</h3>
                        <div class="table-responsive">
                            <table class="table table-striped table-hover">
                                <thead><tr><th>Title</th><th>Status</th><th>Published</th><th>Actions</th></tr></thead>
                                <tbody id="dashboard-tbody">
                                    ${posts.length > 0 ? postRows : '<tr><td colspan="4" class="text-center">No posts found.</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </section>`;
        },
        changePassword: () => `
            <section class="page-section">
                <div class="container px-4 px-lg-5">
                    <div class="row gx-4 gx-lg-5 justify-content-center">
                        <div class="col-lg-6 col-md-8">
                            <h2 class="text-center mt-0">Change Password</h2>
                            <hr class="divider" />
                            <form id="changePasswordForm">
                                <div id="form-error" class="text-danger mb-3 text-center" style="display:none;"></div>
                                <div id="form-success" class="text-success mb-3 text-center" style="display:none;"></div>
                                <div class="form-floating mb-3">
                                    <input class="form-control" id="current_password" type="password" placeholder="Current Password" required />
                                    <label for="current_password">Current Password</label>
                                </div>
                                <div class="form-floating mb-3">
                                    <input class="form-control" id="new_password" type="password" placeholder="New Password" required />
                                    <label for="new_password">New Password</label>
                                </div>
                                <div class="form-floating mb-3">
                                    <input class="form-control" id="confirm_password" type="password" placeholder="Confirm New Password" required />
                                    <label for="confirm_password">Confirm New Password</label>
                                </div>
                                <div class="d-grid"><button class="btn btn-primary btn-xl" type="submit">Update Password</button></div>
                            </form>
                        </div>
                    </div>
                </div>
            </section>`,
        about: () => `<section class="page-section"><div class="container px-4 px-lg-5"><h2 class="text-center mt-0">About Us</h2><hr class="divider" /><div class="row gx-4 gx-lg-5 justify-content-center"><div class="col-lg-8 text-center"><p class="text-muted mb-4">This is the About page. More content coming soon!</p></div></div></div></section>`,
        license: () => `<section class="page-section"><div class="container px-4 px-lg-5"><h2 class="text-center mt-0">License Information</h2><hr class="divider" /><div class="row gx-4 gx-lg-5 justify-content-center"><div class="col-lg-8 text-center"><p class="text-muted mb-4">This is the License page. Details about the project license will be here.</p></div></div></div></section>`,
        contact: () => `<section class="page-section" id="contact"><div class="container px-4 px-lg-5"><div class="row gx-4 gx-lg-5 justify-content-center"><div class="col-lg-8 col-xl-6 text-center"><h2 class="mt-0">Let's Get In Touch!</h2><hr class="divider" /><p class="text-muted mb-5">Ready to start your next project with us? Send us a messages and we will get back to you as soon as possible!</p></div></div></div></section>`
    };

    // --- UI Update Functions ---
    function updateNavUI() {
        mainNavList.querySelector('#admin-link')?.parentElement.remove();
        mainNavList.querySelector('#account-link')?.parentElement.remove();
        mainNavList.querySelector('#logout-link')?.parentElement.remove();
        if (userState.loggedIn) {
            if (userState.user && userState.user.role === 'admin') {
                mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link" id="admin-link" href="#admin">Dashboard</a></li>');
            }
            mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link" id="account-link" href="#account">Account</a></li>');
            mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link" id="logout-link" href="#">Logout</a></li>');
            mainNavList.querySelector('#logout-link').addEventListener('click', handleLogout);
        } else {
            mainNavList.insertAdjacentHTML('beforeend', '<li class="nav-item"><a class="nav-link" id="admin-link" href="#login">Admin</a></li>');
        }
    }

    function resetPostForm() {
        const form = document.getElementById('postForm');
        if (!form) return;
        const formTitle = document.getElementById('form-title');
        const formButtons = document.getElementById('form-buttons');
        form.reset();
        delete form.dataset.postId;
        formTitle.textContent = 'Create New Post';
        formButtons.innerHTML = '<button class="btn btn-primary" type="submit">Create Post</button>';
    }

    // --- Event Handlers ---
    async function handleLoginSubmit(event) {
        event.preventDefault();
        const [username, password] = [document.getElementById('username').value, document.getElementById('password').value];
        const errorDiv = document.getElementById('login-error');
        errorDiv.style.display = 'none';
        try {
            const data = await fetchAPI('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) });
            userState.accessToken = data.access_token;
            userState.refreshToken = data.refresh_token;
            userState.loggedIn = true;
            const payload = JSON.parse(atob(data.access_token.split('.')[1]));
            userState.user = { id: payload.sub, username: payload.username, role: payload.roles[0] };
            localStorage.setItem('accessToken', data.access_token);
            localStorage.setItem('refreshToken', data.refresh_token);
            updateNavUI();
            window.location.hash = '#admin';
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        }
    }

    async function handleLogout(event, force = false) {
        if (event) event.preventDefault();
        if (!force) {
            try {
                await fetchAPI('/api/auth/logout', { method: 'POST' });
            } catch (error) {
                alert('Logout failed: ' + error.message);
            }
        }
        userState.loggedIn = false;
        userState.user = null;
        userState.accessToken = null;
        userState.refreshToken = null;
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        updateNavUI();
        window.location.hash = '#home';
    }

    async function handleChangePasswordSubmit(event) {
        event.preventDefault();
        const currentPassword = document.getElementById('current_password').value;
        const newPassword = document.getElementById('new_password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        const errorDiv = document.getElementById('form-error');
        const successDiv = document.getElementById('form-success');
        errorDiv.style.display = 'none';
        successDiv.style.display = 'none';
        if (newPassword !== confirmPassword) {
            errorDiv.textContent = 'New passwords do not match.';
            errorDiv.style.display = 'block';
            return;
        }
        try {
            const data = await fetchAPI('/api/auth/change-password', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' }, 
                body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
                suppressAuthRedirect: true // Prevent auto-logout on 401 error
            });
            alert(data.message);
            setTimeout(() => handleLogout(null, true), 1000);
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        }
    }

    async function handlePostFormSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const postId = form.dataset.postId;
        const errorDiv = document.getElementById('form-error');
        errorDiv.style.display = 'none';
        const postData = { title: document.getElementById('title').value, summary: document.getElementById('summary').value, content: document.getElementById('content').value, is_published: document.getElementById('is_published').checked };
        const url = postId ? `/api/admin/posts/${postId}` : '/api/admin/posts';
        const method = postId ? 'PUT' : 'POST';
        try {
            await fetchAPI(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(postData) });
            resetPostForm();
            alert(postId ? 'Post updated successfully!' : 'Post created successfully!');
            router();
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        }
    }

    async function handleEditClick(event) {
        const row = event.target.closest('tr');
        const postId = row.dataset.postId;
        try {
            const post = await fetchAPI(`/api/admin/posts/${postId}`);
            document.getElementById('title').value = post.title;
            document.getElementById('summary').value = post.summary;
            document.getElementById('content').value = post.content;
            document.getElementById('is_published').checked = post.is_published;
            const form = document.getElementById('postForm');
            form.dataset.postId = post.id;
            document.getElementById('form-title').textContent = 'Edit Post';
            const formButtons = document.getElementById('form-buttons');
            formButtons.innerHTML = `<button class="btn btn-primary" type="submit">Update Post</button><button type="button" class="btn btn-secondary mt-2" id="cancel-edit-btn">Cancel</button>`;
            document.getElementById('cancel-edit-btn').addEventListener('click', resetPostForm);
            document.getElementById('form-title').scrollIntoView({ behavior: 'smooth' });
        } catch (error) {
            alert('Failed to fetch post for editing: ' + error.message);
        }
    }

    async function handleDeletePost(event) {
        const row = event.target.closest('tr');
        const postId = row.dataset.postId;
        if (confirm('Are you sure you want to delete this post?')) {
            try {
                await fetchAPI(`/api/admin/posts/${postId}`, { method: 'DELETE' });
                row.remove();
            } catch (error) {
                alert('Failed to delete post: ' + error.message);
            }
        }
    }

    // --- Router ---
    const routes = {
        '#home': async () => { mainContentElement.innerHTML = templates.home(await fetchAPI('/api/home')); },
        '#blog': () => { window.location.hash = '#blog/page/1'; },
        '#login': () => { mainContentElement.innerHTML = templates.login(); document.getElementById('loginForm').addEventListener('submit', handleLoginSubmit); },
        '#admin': async () => {
            if (!userState.loggedIn) { window.location.hash = '#login'; return; }
            try {
                const posts = await fetchAPI('/api/admin/posts');
                mainContentElement.innerHTML = templates.adminDashboard(posts);
                document.getElementById('postForm').addEventListener('submit', handlePostFormSubmit);
                document.getElementById('dashboard-tbody').addEventListener('click', (event) => {
                    if (event.target.classList.contains('edit-btn')) handleEditClick(event);
                    if (event.target.classList.contains('delete-btn')) handleDeletePost(event);
                });
            } catch (error) { mainContentElement.innerHTML = `<p class="text-danger text-center">${error.message}</p>`; }
        },
        '#account': () => {
            if (!userState.loggedIn) { window.location.hash = '#login'; return; }
            mainContentElement.innerHTML = templates.changePassword();
            document.getElementById('changePasswordForm').addEventListener('submit', handleChangePasswordSubmit);
        },
        '#about': () => { mainContentElement.innerHTML = templates.about(); },
        '#license': () => { mainContentElement.innerHTML = templates.license(); },
        '#contact': () => { mainContentElement.innerHTML = templates.contact(); }
    };

    async function router() {
        const path = window.location.hash || '#home';
        let match;
        match = path.match(/^#blog\/page\/(\d+)$/);
        if (match) {
            const pageNum = match[1];
            const data = await fetchAPI(`/api/blog?page=${pageNum}`);
            mainContentElement.innerHTML = templates.blogList(data);
            return;
        }
        match = path.match(/^#blog\/(.+)$/);
        if (match) {
            const slug = match[1];
            const post = await fetchAPI(`/api/blog/${slug}`);
            mainContentElement.innerHTML = templates.blogPost(post);
            return;
        }
        if (routes[path]) {
            await routes[path]();
        } else {
            window.location.hash = '#home';
        }
    }

    // --- App Initialization ---
    async function initializeApp() {
        const accessToken = localStorage.getItem('accessToken');
        if (accessToken) {
            userState.accessToken = accessToken;
            try {
                const data = await fetchAPI('/api/auth/status');
                if (data.logged_in) {
                    userState.loggedIn = true;
                    userState.user = data.user;
                } else {
                    handleLogout(null, true);
                }
            } catch (error) {
                console.error("Could not verify auth status. Assuming logged out.", error);
                handleLogout(null, true);
            }
        }
        updateNavUI();
        window.addEventListener('hashchange', router);
        router();
    }

    initializeApp();
});