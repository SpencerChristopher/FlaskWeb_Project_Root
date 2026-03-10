import { escapeHTML, validateURL } from '../utils/SecurityUtils.js';

// LicenseView.js - Extracted View Component
export const LicenseView = {
    template: (data) => {
        const title = escapeHTML(data.title || 'License');
        const content = escapeHTML(data.content || 'License content not available.');
        const copyright = escapeHTML(data.copyright || '');
        const distBy = escapeHTML(data.distributed_by || '');
        const distUrl = validateURL(data.distributed_by_link || '#');

        return `
            <header class="py-5 bg-light border-bottom mb-4">
                <div class="container px-5">
                    <div class="text-center my-5">
                        <h1 class="fw-bolder">${title}</h1>
                    </div>
                </div>
            </header>
            <section class="py-5">
                <div class="container px-5">
                    <div class="card mb-4">
                        <div class="card-body p-5">
                            <p class="mb-5">${content}</p>
                            <hr>
                            <div class="d-flex justify-content-between small text-muted">
                                <span>${copyright}</span>
                                <span>Distributed by: 
                                    <a href="${distUrl}" 
                                       target="_blank" 
                                       rel="noopener noreferrer">
                                        ${distBy}
                                    </a>
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </section>`;
    }
};
