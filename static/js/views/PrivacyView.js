import { renderMarkdown } from '../utils/SecurityUtils.js';

export const PrivacyView = {
    template(data) {
        if (!data) return '';
        
        const sectionsHtml = data.sections.map(section => `
            <div class="mb-5">
                <h2 class="h4 fw-bold mb-3 text-primary">${section.heading}</h2>
                <p class="text-muted leading-relaxed">${section.content}</p>
            </div>
        `).join('');

        return `
            <section id="view-privacy" class="py-5 bg-light min-vh-100" data-test="view-privacy">
                <div class="container px-5">
                    <div class="row justify-content-center">
                        <div class="col-lg-10 col-xl-8">
                            <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
                                <div class="card-header bg-white border-0 p-5 pb-0">
                                    <h1 class="display-5 fw-bolder mb-2">${data.title}</h1>
                                    <p class="text-secondary small mb-0">Effective Date: ${data.last_updated}</p>
                                    <hr class="mt-4">
                                </div>
                                <div class="card-body p-5 pt-4">
                                    ${sectionsHtml}
                                    
                                    <div class="mt-5 p-4 bg-white border rounded-4">
                                        <h3 class="h5 fw-bold mb-3">Contact Information</h3>
                                        <p class="text-muted mb-0">
                                            If you have any questions about this Privacy Policy or our data practices, 
                                            please use our <a href="/contact" class="text-primary text-decoration-none">Contact Form</a>.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>`;
    },
    mount(context) {
        // Static view, no complex mounting needed
    }
};
