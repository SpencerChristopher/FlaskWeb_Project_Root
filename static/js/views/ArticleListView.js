import { ComponentFactory } from '../components/ComponentFactory.js';

/**
 * ArticleListView.js
 * Renders the public blog article list with polished, consistent styling.
 */

export const ArticleListView = {
    template(data, auth) {
        const articles = data?.posts || [];
        return ComponentFactory.createSection({
            id: "view-articles",
            featureLabel: "Blog",
            title: "Technical Writing",
            tagline: "Insights on software engineering and architecture",
            content: `
                <div class="row justify-content-center" data-test="article-grid">
                    <div class="col-12">
                        ${articles.length ? articles.map((a, idx) => ComponentFactory.createCard({
                            title: a.title,
                            badge: "Article",
                            meta: `📅 ${a.publication_date ? new Date(a.publication_date).toLocaleDateString() : 'Draft'}`,
                            body: `<p class="mb-0">${a.summary}</p>`,
                            link: `/blog/${a.slug}`,
                            dataTest: `article-card-${idx}`
                        })).join("") : `
                            <div class="text-center py-5">
                                <p class="text-muted">No articles published yet. Check back soon!</p>
                            </div>
                        `}
                    </div>
                </div>`
        });
    },
};
