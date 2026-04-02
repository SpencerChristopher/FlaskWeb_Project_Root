import { renderTurnstile, isTurnstileLoginEnabled } from '../utils/Turnstile.js';

export const LoginView = {
    template() {
        return `
            <section id="view-login" class="py-5" data-test="view-login">
                <div class="container px-5">
                    <div class="card">
                        <div class="card-body">
                            <header class="mb-4 text-center">
                                <h1 class="section-title">Login</h1>
                            </header>
                            <div class="row g-4 justify-content-center">
                                <div class="col-12 col-lg-10 col-xl-8">
                                    <form id="loginForm" aria-label="Login form" data-test="login-form">
                                        <div class="mb-3">
                                            <label class="form-label" for="username">Username</label>
                                            <input class="form-control" id="username" type="text" placeholder="Username" required />
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label" for="password">Password</label>
                                            <input class="form-control" id="password" type="password" placeholder="Password" required />
                                        </div>
                                        <div class="mb-3" id="login-turnstile-wrapper">
                                            <div id="login-turnstile-container"></div>
                                        </div>
                                        <div class="d-flex justify-content-between align-items-center">
                                            <button class="btn btn-primary btn-lg" type="submit" data-test="login-submit">Sign In</button>
                                            <div class="small text-muted" data-test="login-message" aria-live="polite"></div>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>`;
    },
    mount(context, onLogin) {
        const form = document.getElementById('loginForm');
        if (!form) return;
        let turnstileToken = null;

        const container = document.getElementById('login-turnstile-container');
        const wrapper = document.getElementById('login-turnstile-wrapper');
        if (!isTurnstileLoginEnabled()) {
            wrapper?.classList.add('d-none');
        } else if (container) {
            renderTurnstile(container, {
                callback: (token) => {
                    turnstileToken = token;
                    form.dataset.turnstileToken = token;
                },
                'expired-callback': () => {
                    turnstileToken = null;
                    delete form.dataset.turnstileToken;
                },
                'error-callback': () => {
                    turnstileToken = null;
                    delete form.dataset.turnstileToken;
                }
            }).catch(() => {
                const msg = form.querySelector('[data-test="login-message"]');
                if (msg) msg.textContent = 'Bot protection failed to load.';
            });
        }
        form.addEventListener('submit', onLogin, { signal: context.signal });

        // Handle security reason messages
        const params = new URLSearchParams(window.location.search);
        const reason = params.get('reason');
        const msgEl = form.querySelector('[data-test="login-message"]');
        
        if (msgEl) {
            if (reason === 'session_expired') {
                msgEl.textContent = 'Session expired. Please login again.';
                msgEl.className = 'small text-warning';
            } else if (reason === 'session_invalidated') {
                msgEl.textContent = 'For your security, you have been logged out after a credential change.';
                msgEl.className = 'small text-danger';
            }
        }
    },
};
