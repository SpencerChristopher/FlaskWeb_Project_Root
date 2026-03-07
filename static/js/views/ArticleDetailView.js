export const ArticleDetailView = {
    template(article) {
        const data = article || {};
        const published = data.publication_date
            ? new Date(data.publication_date).toLocaleDateString()
            : "";
        return `
            <section id="view-article-detail" class="py-5" data-test="view-article-detail">
                <div class="container px-5">
                    <div class="row g-4 justify-content-center">
                        <div class="col-12 col-lg-10 col-xl-8">
                            <div class="mb-4">
                                <a href="/blog" class="btn btn-outline-primary btn-sm">&larr; Back to Blog</a>
                            </div>
                            <article class="card">
                                <div class="card-body">
                                    <header class="mb-4">
                                        <h1 class="profile-name mb-2" data-test="article-title">${data.title || ""}</h1>
                                        <div class="text-muted" data-test="article-date">
                                            Published on ${published}
                                        </div>
                                    </header>
                                    <section class="article-content" data-test="article-content">
                                        ${data.content || ""}
                                    </section>
                                </div>
                            </article>
                        </div>
                    </div>
                </div>
            </section>`;
    },
};
