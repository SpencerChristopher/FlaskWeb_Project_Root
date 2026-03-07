// LicenseView.js - Extracted View Component
export const LicenseView = {
    template: (data) => `
        <header class="py-5 bg-light border-bottom mb-4">
            <div class="container px-5">
                <div class="text-center my-5">
                    <h1 class="fw-bolder">${data.title || 'License'}</h1>
                </div>
            </div>
        </header>
        <section class="py-5">
            <div class="container px-5">
                <div class="card mb-4">
                    <div class="card-body p-5">
                        <p class="mb-5">${data.content || 'License content not available.'}</p>
                        <hr>
                        <div class="d-flex justify-content-between small text-muted">
                            <span>${data.copyright || ''}</span>
                            <span>Distributed by: <a href="${data.distributed_by_link || '#'}" target="_blank">${data.distributed_by || ''}</a></span>
                        </div>
                    </div>
                </div>
            </div>
        </section>`
};
