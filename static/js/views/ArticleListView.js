/**
 * ArticleListView.js
 * Renders the public blog article list with polished, consistent styling.
 */

export const ArticleListView = {
    template(data) {
        const articles = data?.posts || [];
        return `
            <section id="view-articles" class="py-5" data-test="view-articles">
                <div class="wide-container px-3 px-md-5">
                    <header class="text-center mb-5">
                        <div class="feature bg-primary text-white rounded-3 mb-3">Blog</div>
                        <h2 class="section-title fw-bolder">Technical Writing</h2>
                        <p class="lead fw-normal text-muted mb-0">Insights on software engineering and architecture</p>
                    </header>
                    
                    <div class="row justify-content-center" data-test="article-grid">
                        <div class="col-12">
                            ${articles.length ? articles.map((a, idx) => `
                                <article class="article-card card mb-4 border-0 shadow-sm bg-white" data-test="article-card-${idx}" style="max-width: 1100px; margin-left: auto; margin-right: auto; border-radius: 32px; overflow: hidden;">
                                    <div class="card-body p-4 p-md-5">
                                        <div class="row align-items-center">
                                            <div class="col-12">
                                                <header class="mb-3">
                                                    <div class="badge bg-primary-subtle text-primary border border-primary-subtle px-3 py-2 rounded-pill mb-3 small fw-bold text-uppercase">Article</div>
                                                    <h3 class="fw-bolder mb-2" style="color: var(--text);">
                                                        <a href="/blog/${a.slug}" class="text-decoration-none text-inherit stretched-link">${a.title}</a>
                                                    </h3>
                                                    <div class="text-muted small fw-bold text-uppercase">
                                                        📅 ${a.publication_date ? new Date(a.publication_date).toLocaleDateString() : 'Draft'}
                                                    </div>
                                                </header>
                                                
                                                <div class="bio mb-0 text-muted">
                                                    <p class="mb-0">${a.summary}</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </article>
                            `).join("") : `
                                <div class="text-center py-5">
                                    <p class="text-muted">No articles published yet. Check back soon!</p>
                                </div>
                            `}
                        </div>
                    </div>
                </div>
            </section>`;
    },
};
