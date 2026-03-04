export const ArticleDetailView = {
    template(article) {
        const data = article || {};
        const published = data.publication_date
            ? new Date(data.publication_date).toLocaleDateString()
            : "";
        return `
            <section id="view-article-detail" class="py-5" data-test="view-article-detail">
                <div class="container px-5">
                    <div class="row gx-5 justify-content-center">
                        <div class="col-lg-10 col-xl-8">
                            <article>
                                <header class="mb-4">
                                    <h1 class="fw-bolder mb-1" data-test="article-title">${data.title || ""}</h1>
                                    <div class="text-muted fst-italic mb-2" data-test="article-date">
                                        Published on ${published}
                                    </div>
                                </header>
                                <section class="mb-5" data-test="article-content">
                                    <p class="fs-5 mb-4">${data.content || ""}</p>
                                </section>
                            </article>
                        </div>
                    </div>
                </div>
            </section>`;
    },
};
