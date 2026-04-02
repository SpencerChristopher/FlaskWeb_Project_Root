import { escapeHTML } from '../utils/SecurityUtils.js';

export const AboutView = {
    template(data = {}) {
        const heading = escapeHTML(data.heading || "About Spencer's Cooking");
        const description = escapeHTML(data.description || "");
        const mission = escapeHTML(data.mission || "");
        const promise = escapeHTML(data.promise || "");
        const highlights = Array.isArray(data.highlights) ? data.highlights : [];
        const highlightMarkup = highlights.length
            ? highlights
                  .map(
                      (item) =>
                          `<li class="mb-3 d-flex gap-2 align-items-start">
                              <span class="text-primary fs-5" aria-hidden="true">&bull;</span>
                              <span>${escapeHTML(item)}</span>
                          </li>`
                  )
                  .join('')
            : `<li class="mb-3 d-flex gap-2 align-items-start">
                    <span class="text-primary fs-5" aria-hidden="true">&bull;</span>
                    <span>More curated updates landing here soon.</span>
                </li>`;

        return `
            <section id="view-about" class="py-5" data-test="view-about">
                <div class="container px-3 px-md-5">
                    <div class="text-center mb-5">
                        <h1 class="display-5 fw-bold">${heading}</h1>
                        <p class="lead mx-auto" style="max-width: 700px;">${description}</p>
                    </div>

                    <div class="row g-4">
                        <div class="col-lg-6">
                            <div class="card shadow-sm border-0 rounded-4 p-4 h-100">
                                <h2 class="h5 mb-3">Mission</h2>
                                <p class="text-muted">${mission}</p>
                                <h2 class="h5 mt-4 mb-3">Why it matters</h2>
                                <p class="text-muted">${promise}</p>
                            </div>
                        </div>
                        <div class="col-lg-6">
                            <div class="card shadow-sm border-0 rounded-4 p-4 h-100">
                                <h2 class="h5 mb-3">Project highlights</h2>
                                <ul class="list-unstyled">
                                    ${highlightMarkup}
                                </ul>
                                <p class="text-muted mt-4 mb-0">
                                    This page is just the beginning—check the blog for hands-on explorations and updates.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>`;
    },
};
