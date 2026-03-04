export const LoginView = {
    template() {
        return `
            <section id="view-login" class="py-5" data-test="view-login">
                <div class="container px-5">
                    <div class="bg-light rounded-4 py-5 px-4 px-md-5">
                        <header class="text-center mb-5">
                            <h1 class="fw-bolder">Login</h1>
                        </header>
                        <div class="row gx-5 justify-content-center">
                            <div class="col-lg-8 col-xl-6">
                                <form id="loginForm" aria-label="Login form" data-test="login-form">
                                    <div class="form-floating mb-3">
                                        <input class="form-control" id="username" type="text" placeholder="Username" required />
                                        <label for="username">Username</label>
                                    </div>
                                    <div class="form-floating mb-3">
                                        <input class="form-control" id="password" type="password" placeholder="Password" required />
                                        <label for="password">Password</label>
                                    </div>
                                    <div class="d-grid">
                                        <button class="btn btn-primary btn-lg" type="submit" data-test="login-submit">Sign In</button>
                                    </div>
                                    <div class="mt-3 text-center text-muted" data-test="login-message"></div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </section>`;
    },
    mount(context, onLogin) {
        const form = document.getElementById('loginForm');
        if (!form) return;
        form.addEventListener('submit', onLogin, { signal: context.signal });
    },
};
