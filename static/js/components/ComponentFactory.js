import { escapeHTML, validateURL } from '../utils/SecurityUtils.js';

/**
 * ComponentFactory.js
 * Centralizes UI generation to ensure consistent styling and atomic structure.
 * This implements the FACTORY PATTERN for Vanilla JS.
 */

export const ComponentFactory = {
    /**
     * Creates a standard content card (used for Experience and Blog).
     */
    createCard: ({ id, title, subtitle, meta, body, tags = [], link = null, dataTest = "", badge = "" }) => {
        const safeTitle = escapeHTML(title);
        const safeSubtitle = escapeHTML(subtitle);
        const safeMeta = escapeHTML(meta);
        const safeLink = validateURL(link);
        const safeBadge = escapeHTML(badge);
        const safeDataTest = escapeHTML(dataTest);

        return `
            <article class="card mb-4 border-0 shadow-sm bg-white" 
                     data-test="${safeDataTest}" 
                     style="max-width: 1100px; margin-left: auto; margin-right: auto; border-radius: 32px; overflow: hidden;">
                <div class="card-body p-4 p-md-5">
                    <header class="mb-3">
                        ${safeBadge ? `<div class="badge bg-primary-subtle text-primary border border-primary-subtle px-3 py-2 rounded-pill mb-3 small fw-bold text-uppercase">${safeBadge}</div>` : ""}
                        <h3 class="fw-bolder mb-2" style="color: var(--text);">
                            ${safeLink && safeLink !== "#" ? `<a href="${safeLink}" class="text-decoration-none text-inherit stretched-link">${safeTitle}</a>` : safeTitle}
                        </h3>
                        ${safeSubtitle ? `<div class="text-primary fw-bold mb-2 fs-5">${safeSubtitle}</div>` : ""}
                        ${safeMeta ? `<div class="text-muted small fw-bold text-uppercase">${safeMeta}</div>` : ""}
                    </header>
                    
                    <div class="bio mb-4 text-muted">
                        ${body}
                    </div>

                    ${tags.length ? `
                        <footer class="mt-auto">
                            <div class="tags">
                                ${tags.map((tag, i) => ComponentFactory.createTag(tag, i % 2 !== 0)).join("")}
                            </div>
                        </footer>
                    ` : ""}
                </div>
            </article>`;
    },

    /**
     * Creates a tag pill.
     */
    createTag: (text, isSecondary = false) => {
        return `<span class="tag ${isSecondary ? 'secondary' : ''}">${escapeHTML(text)}</span>`;
    },

    /**
     * Creates a standard page section with header.
     */
    createSection: ({ id, title, tagline, content, featureLabel = "" }) => {
        return `
            <section id="${escapeHTML(id)}" class="py-5" data-test="${escapeHTML(id)}">
                <div class="container px-5">
                    <header class="mb-5 text-center">
                        ${featureLabel ? `<div class="feature bg-primary text-white rounded-3 mb-3">${escapeHTML(featureLabel)}</div>` : ""}
                        <h2 class="section-title fw-bolder">${escapeHTML(title)}</h2>
                        ${tagline ? `<p class="lead fw-normal text-muted mb-0">${escapeHTML(tagline)}</p>` : ""}
                    </header>
                    ${content}
                </div>
            </section>`;
    }
};
