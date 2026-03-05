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
                            <article class="card">
                                <div class="card-body">
                                    <header class="mb-3">
                                        <h1 class="profile-name mb-2" data-test="article-title">${data.title || ""}</h1>
                                        <div class="text-muted mb-2" data-test="article-date">
                                            Published on ${published}
                                        </div>
                                    </header>
                                    <section class="mb-4" data-test="article-content">
                                        <p>${data.content || ""}</p>
                                    </section>
                                </div>
                            </article>
                        </div>
                    </div>
                </div>
            </section>`;
    },
};
