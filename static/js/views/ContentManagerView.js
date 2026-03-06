/**
 * ContentManagerView.js
 * Manages the article lifecycle: listing, creating, editing, and deleting.
 */

export const ContentManagerView = {
    template() {
        return `
            <section id="view-content-manager" class="py-5" data-test="view-content-manager">
                <div class="container px-5">
                    <header class="mb-5 text-center">
                        <div class="feature bg-primary text-white rounded-3 mb-3">Content</div>
                        <h2 class="section-title fw-bolder">Article Management</h2>
                        <p class="lead fw-normal text-muted mb-0">Compose and publish your blog posts</p>
                    </header>

                    <div class="row g-4 mb-5" data-test="content-manager-grid">
                        <div class="col-md-12">
                            <div class="card border-0 shadow-sm rounded-4 bg-white">
                                <div class="card-body p-4 d-flex justify-content-between align-items-center">
                                    <div>
                                        <h5 class="fw-bolder mb-1">Create New Content</h5>
                                        <p class="text-muted small mb-0">Draft a new article for your professional blog.</p>
                                    </div>
                                    <button class="btn btn-primary px-4 rounded-pill" type="button" data-test="create-article" id="open-create-modal">
                                        + New Article
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
                        <div class="card-header bg-white border-bottom p-4">
                            <h5 class="fw-bolder mb-0">Your Articles</h5>
                        </div>
                        <div class="card-body p-0">
                            <div class="table-responsive">
                                <table class="table table-hover align-middle mb-0" id="articles-table">
                                    <thead class="bg-light">
                                        <tr>
                                            <th class="ps-4 border-0 text-uppercase small fw-bold text-muted">Title</th>
                                            <th class="border-0 text-uppercase small fw-bold text-muted">Status</th>
                                            <th class="border-0 text-uppercase small fw-bold text-muted">Last Updated</th>
                                            <th class="pe-4 border-0 text-uppercase small fw-bold text-muted text-end">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="articles-list-body">
                                        <!-- Loaded via mount -->
                                        <tr><td colspan="4" class="text-center py-5 text-muted">Loading articles...</td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Article Form Modal -->
                <div id="article-form-modal" class="modal-overlay" style="display:none;">
                    <div class="modal-content card shadow-lg border-0 rounded-4">
                        <div class="card-header bg-white border-bottom p-4 d-flex justify-content-between align-items-center">
                            <h5 class="fw-bolder mb-0" id="article-modal-title">New Article</h5>
                            <button type="button" class="btn-close" id="close-article-modal"></button>
                        </div>
                        <div class="card-body p-4">
                            <form id="articleForm">
                                <input type="hidden" id="a-id" value="">
                                <div class="mb-3">
                                    <label class="form-label small fw-bold">Title</label>
                                    <input type="text" id="a-title" class="form-control" placeholder="Article title..." required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label small fw-bold">Summary</label>
                                    <textarea id="a-summary" class="form-control" rows="2" placeholder="Brief summary for list view..." required></textarea>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label small fw-bold">Content (Markdown/HTML)</label>
                                    <textarea id="a-content" class="form-control" rows="10" placeholder="Full article content..." required></textarea>
                                </div>
                                <div class="form-check form-switch mb-4">
                                    <input class="form-check-input" type="checkbox" id="a-published">
                                    <label class="form-check-label fw-bold small" for="a-published">Publish immediately</label>
                                </div>
                                <div class="d-flex gap-2">
                                    <button type="submit" class="btn btn-primary flex-grow-1" id="save-article-btn">Save Article</button>
                                    <button type="button" class="btn btn-light" id="cancel-article-modal">Cancel</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </section>
            <style>
                .modal-overlay {
                    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(30, 30, 30, 0.6); display: flex;
                    align-items: center; justify-content: center; z-index: 1000;
                    backdrop-filter: blur(4px);
                }
                .modal-content { width: 95%; max-width: 800px; max-height: 90vh; overflow-y: auto; }
            </style>`;
    },

    articleRowTemplate(a) {
        const date = a.last_updated ? new Date(a.last_updated).toLocaleDateString() : '—';
        const statusBadge = a.is_published 
            ? '<span class="badge bg-success-subtle text-success border border-success-subtle px-3 py-2 rounded-pill">Published</span>'
            : '<span class="badge bg-secondary-subtle text-secondary border border-secondary-subtle px-3 py-2 rounded-pill">Draft</span>';
        
        return `
            <tr data-id="${a.id}">
                <td class="ps-4 fw-bold">${a.title}</td>
                <td>${statusBadge}</td>
                <td class="text-muted small">${date}</td>
                <td class="pe-4 text-end">
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline-primary edit-article-btn" data-id="${a.id}">Edit</button>
                        <button class="btn btn-sm btn-outline-danger delete-article-btn" data-id="${a.id}">Delete</button>
                    </div>
                </td>
            </tr>`;
    },

    async mount(context) {
        const fetchAPI = context.api;
        const listBody = document.getElementById('articles-list-body');
        const modal = document.getElementById('article-form-modal');
        const form = document.getElementById('articleForm');
        
        const loadArticles = async () => {
            try {
                const articles = await fetchAPI('/api/content/articles');
                if (articles.length === 0) {
                    listBody.innerHTML = '<tr><td colspan="4" class="text-center py-5 text-muted">No articles found. Create your first one above!</td></tr>';
                } else {
                    listBody.innerHTML = articles.map(a => this.articleRowTemplate(a)).join('');
                }
            } catch (err) {
                listBody.innerHTML = `<tr><td colspan="4" class="text-center py-5 text-danger">Failed to load articles: ${err.message}</td></tr>`;
            }
        };

        const openModal = (article = null) => {
            const titleEl = document.getElementById('article-modal-title');
            if (article) {
                titleEl.textContent = 'Edit Article';
                document.getElementById('a-id').value = article.id;
                document.getElementById('a-title').value = article.title;
                document.getElementById('a-summary').value = article.summary;
                document.getElementById('a-content').value = article.content;
                document.getElementById('a-published').checked = article.is_published;
            } else {
                titleEl.textContent = 'New Article';
                form.reset();
                document.getElementById('a-id').value = '';
            }
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        };

        const closeModal = () => {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        };

        // Listeners
        document.getElementById('open-create-modal').onclick = () => openModal();
        document.getElementById('close-article-modal').onclick = closeModal;
        document.getElementById('cancel-article-modal').onclick = closeModal;

        listBody.onclick = async (e) => {
            const id = e.target.getAttribute('data-id');
            if (e.target.classList.contains('edit-article-btn')) {
                const article = await fetchAPI(`/api/content/articles/${id}`);
                openModal(article);
            } else if (e.target.classList.contains('delete-article-btn')) {
                if (confirm('Delete this article permanently?')) {
                    await fetchAPI(`/api/content/articles/${id}`, { method: 'DELETE' });
                    loadArticles();
                }
            }
        };

        form.onsubmit = async (e) => {
            e.preventDefault();
            const id = document.getElementById('a-id').value;
            const data = {
                title: document.getElementById('a-title').value.trim(),
                summary: document.getElementById('a-summary').value.trim(),
                content: document.getElementById('a-content').value.trim(),
                is_published: document.getElementById('a-published').checked
            };

            try {
                const method = id ? 'PUT' : 'POST';
                const url = id ? `/api/content/articles/${id}` : '/api/content/articles';
                await fetchAPI(url, { method, body: JSON.stringify(data) });
                closeModal();
                loadArticles();
            } catch (err) {
                alert('Failed to save article: ' + err.message);
            }
        };

        // Initial Load
        loadArticles();
    }
};
