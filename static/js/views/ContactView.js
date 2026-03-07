// ContactView.js - Extracted View Component
export const ContactView = {
    template: () => `
        <header class="py-5 bg-light border-bottom mb-4">
            <div class="container px-5">
                <div class="text-center my-5">
                    <h1 class="fw-bolder">Contact</h1>
                    <p class="lead mb-0">Get in touch for collaborations and opportunities.</p>
                </div>
            </div>
        </header>
        <section class="py-5">
            <div class="container px-5">
                <div class="row justify-content-center">
                    <div class="col-lg-8">
                        <div class="card mb-4">
                            <div class="card-body p-5">
                                <form id="contactForm">
                                    <div class="mb-3">
                                        <label for="name" class="form-label">Name</label>
                                        <input type="text" class="form-control" id="name" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="email" class="form-label">Email address</label>
                                        <input type="email" class="form-control" id="email" required>
                                    </div>
                                    <div class="mb-3">
                                        <label for="message" class="form-label">Message</label>
                                        <textarea class="form-control" id="message" rows="4" required></textarea>
                                    </div>
                                    <button type="submit" class="btn btn-primary" id="submitButton">Send Message</button>
                                </form>
                                <div id="formStatus" class="mt-3"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>`,
    mount: (ctx) => {
        const form = document.getElementById('contactForm');
        const status = document.getElementById('formStatus');
        
        form?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = document.getElementById('submitButton');
            submitBtn.disabled = true;
            status.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div> Sending...';
            
            const payload = {
                name: document.getElementById('name').value,
                email: document.getElementById('email').value,
                message: document.getElementById('message').value
            };
            
            try {
                await ctx.api('/api/contact', {
                    method: 'POST',
                    body: JSON.stringify(payload)
                });
                status.innerHTML = '<div class="alert alert-success">Message sent successfully!</div>';
                form.reset();
            } catch (err) {
                status.innerHTML = `<div class="alert alert-danger">Error: ${err.message}</div>`;
            } finally {
                submitBtn.disabled = false;
            }
        });
    }
};
