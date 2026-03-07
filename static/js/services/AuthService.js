/**
 * AuthService.js
 * Abstracts authentication logic away from the main application and views.
 * Ready for future pivot to OAuth/SSO.
 */

export class AuthService {
    constructor(api) {
        this.api = api;
        this.user = null;
        this._loggedIn = false;
    }

    get loggedIn() {
        return !!(this._loggedIn && this.user);
    }

    set loggedIn(value) {
        this._loggedIn = value;
    }

    /**
     * Checks the current authentication status with the server.
     */
    async checkStatus() {
        try {
            // Using suppressAuthRedirect: true to prevent infinite loops in fetchAPI
            const status = await this.api('/api/auth/status', { suppressAuthRedirect: true });
            this.loggedIn = status.logged_in;
            this.user = status.user || null;
            return status;
        } catch (err) {
            this.loggedIn = false;
            this.user = null;
            throw err;
        }
    }

    /**
     * Authenticates a user with username and password.
     */
    async login(username, password) {
        const body = JSON.stringify({ username, password });
        await this.api('/api/auth/login', { method: 'POST', body });
        return await this.checkStatus();
    }

    /**
     * Terminates the current session.
     */
    async logout() {
        await this.api('/api/auth/logout', { method: 'POST' }).catch(() => {});
        this.loggedIn = false;
        this.user = null;
    }

    /**
     * Checks if the user has a specific permission.
     */
    hasPermission(permission) {
        if (!this.loggedIn || !this.user) return false;
        const caps = this.user.capabilities || [];
        return caps.includes(permission);
    }
}
