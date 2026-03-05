export const ArticleListView = {
    template(data) {
        const articles = data?.posts || [];
        return `
            <section id="view-articles" class="py-5" data-test="view-articles">
                <div class="container px-5">
                    <header class="mb-4">
                        <h2 class="section-title">Latest Articles</h2>
                    </header>
                    <div class="row g-4" data-test="article-grid">
                        ${articles
                            .map(
                                (a, idx) => `
                                    <div class="col-md-4">
                                        <article class="card" data-test="article-card-${idx}">
                                            <div class="card-body">
                                                <div class="badge bg-primary rounded-pill mb-2">Article</div>
                                                <a class="text-decoration-none link-dark stretched-link" href="#blog/${a.slug}">
                                                    <h5 class="card-title mb-3" data-test="article-title">${a.title}</h5>
                                                </a>
                                                <p class="card-text mb-0" data-test="article-summary">${a.summary}</p>
                                            </div>
                                        </article>
                                    </div>`
                            )
                            .join("")}
                    </div>
                </div>
            </section>`;
    },
};
