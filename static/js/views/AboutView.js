// AboutView.js - Extracted View Component
export const AboutView = {
    template: (data) => `
        <header class="py-5 bg-light border-bottom mb-4">
            <div class="container px-5">
                <div class="text-center my-5">
                    <h1 class="fw-bolder">${data.title || 'About Me'}</h1>
                    <p class="lead mb-0">Learn more about the project and mission.</p>
                </div>
            </div>
        </header>
        <section class="py-5">
            <div class="container px-5">
                <div class="row justify-content-center">
                    <div class="col-lg-8">
                        <p class="lead">${data.content || ''}</p>
                    </div>
                </div>
            </div>
        </section>`
};
