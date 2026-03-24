// ContactView.js - Extracted View Component
import { renderTurnstile, isTurnstileEnabled } from '../utils/Turnstile.js';

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
                                    <div aria-hidden="true" style="position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden;">
                                        <label for="website">Website</label>
                                        <input type="text" class="form-control" id="website" autocomplete="off" tabindex="-1">
                                    </div>
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
                                    <div class="mb-3" id="turnstile-wrapper">
                                        <div id="turnstile-container"></div>
                                    </div>
                                    <button type="submit" class="btn btn-primary" id="submitButton">Send Message</button>
                                </form>
                                <div id="formStatus" class="mt-3" aria-live="polite"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>`,
    mount: (ctx) => {
        const form = document.getElementById('contactForm');
        const status = document.getElementById('formStatus');
        const formLoadedAt = Date.now();
        let turnstileToken = null;

        const container = document.getElementById('turnstile-container');
        const wrapper = document.getElementById('turnstile-wrapper');
        if (!isTurnstileEnabled()) {
            wrapper?.classList.add('d-none');
        } else if (container) {
            renderTurnstile(container, {
                callback: (token) => { turnstileToken = token; },
                'expired-callback': () => { turnstileToken = null; },
                'error-callback': () => { turnstileToken = null; }
            }).catch(() => {
                status.innerHTML = '<div class="alert alert-danger">Bot protection failed to load.</div>';
            });
        }
        
        form?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = document.getElementById('submitButton');
            submitBtn.disabled = true;
            status.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div> Sending...';
            
            if (isTurnstileEnabled() && !turnstileToken) {
                status.innerHTML = '<div class="alert alert-warning">Please complete the verification.</div>';
                submitBtn.disabled = false;
                return;
            }

            const payload = {
                name: document.getElementById('name').value,
                email: document.getElementById('email').value,
                message: document.getElementById('message').value,
                website: document.getElementById('website')?.value || '',
                form_loaded_at: formLoadedAt,
                turnstile_token: turnstileToken
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
