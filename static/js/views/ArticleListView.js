import { ComponentFactory } from '../components/ComponentFactory.js';

/**
 * ArticleListView.js
 * Renders the public blog article list with Infinite Scroll.
 */

export const ArticleListView = {
    _state: {
        currentPage: 1,
        hasNext: false,
        isLoading: false,
        articles: []
    },

    template(data) {
        // Initialize state from initial router fetch if present
        if (data && data.posts && this._state.articles.length === 0) {
            this._state.articles = data.posts;
            this._state.currentPage = data.pagination?.current_page || 1;
            this._state.hasNext = data.pagination?.has_next || false;
        }

        const articlesHtml = this._state.articles.map((a, idx) => ComponentFactory.createCard({
            title: a.title,
            badge: "Article",
            meta: `📅 ${a.publication_date ? new Date(a.publication_date).toLocaleDateString() : 'Draft'}`,
            body: `<p class="mb-0">${a.summary}</p>`,
            link: `/blog/${a.slug}`,
            dataTest: `article-card-${idx}`
        })).join("");

        return ComponentFactory.createSection({
            id: "view-articles",
            featureLabel: "Blog",
            title: "Technical Writing",
            tagline: "Insights on software engineering and architecture",
            content: `
                <div class="row justify-content-center">
                    <div class="col-12" id="article-container" data-test="article-grid">
                        ${articlesHtml || `
                            <div class="text-center py-5">
                                <p class="text-muted">No articles published yet. Check back soon!</p>
                            </div>
                        `}
                    </div>
                </div>
                <!-- Sentinel element for Infinite Scroll -->
                <div id="infinite-sentinel" style="height: 20px; margin-bottom: 50px;"></div>
                <div id="infinite-loader" class="text-center d-none py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading more...</span>
                    </div>
                </div>`
        });
    },

    async mount(ctx) {
        const sentinel = document.getElementById('infinite-sentinel');
        const loader = document.getElementById('infinite-loader');
        const container = document.getElementById('article-container');

        if (!sentinel) return;

        // Reset state on fresh mount to avoid stale data from previous navigation
        // unless we want to keep the scroll position (complex for now).
        // For simplicity, we assume the router handles the first fetch.

        const observer = new IntersectionObserver(async (entries) => {
            const entry = entries[0];
            if (entry.isIntersecting && this._state.hasNext && !this._state.isLoading) {
                await this.loadMore(ctx, container, loader);
            }
        }, { rootMargin: '200px' });

        observer.observe(sentinel);
        
        // Add signal listener to stop observer on unmount
        ctx.signal?.addEventListener('abort', () => observer.disconnect());
    },

    async loadMore(ctx, container, loader) {
        this._state.isLoading = true;
        loader.classList.remove('d-none');

        try {
            const nextPage = this._state.currentPage + 1;
            const data = await ctx.api(`/api/blog?page=${nextPage}&per_page=6`);
            
            if (data?.posts?.length) {
                this._state.articles.push(...data.posts);
                this._state.currentPage = data.pagination.current_page;
                this._state.hasNext = data.pagination.has_next;

                // Append new cards to DOM without re-rendering everything
                const newCardsHtml = data.posts.map((a, idx) => {
                    const globalIdx = this._state.articles.length - data.posts.length + idx;
                    return ComponentFactory.createCard({
                        title: a.title,
                        badge: "Article",
                        meta: `📅 ${a.publication_date ? new Date(a.publication_date).toLocaleDateString() : 'Draft'}`,
                        body: `<p class="mb-0">${a.summary}</p>`,
                        link: `/blog/${a.slug}`,
                        dataTest: `article-card-${globalIdx}`
                    });
                }).join("");
                
                container.insertAdjacentHTML('beforeend', newCardsHtml);
            } else {
                this._state.hasNext = false;
            }
        } catch (err) {
            console.error("Failed to load more articles:", err);
        } finally {
            this._state.isLoading = false;
            loader.classList.add('d-none');
        }
    },

    // Helper to reset state when navigating AWAY from blog
    resetState() {
        this._state = {
            currentPage: 1,
            hasNext: false,
            isLoading: false,
            articles: []
        };
    }
};
