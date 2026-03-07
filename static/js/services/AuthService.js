/**
 * AuthService.js
 * Abstracts authentication logic and acts as an OBSERVABLE for UI state.
 */

export class AuthService {
    constructor(api) {
        this.api = api;
        this.user = null;
        this._loggedIn = false;
        this.listeners = []; // Observer pattern listeners
    }

    get loggedIn() {
        return !!(this._loggedIn && this.user);
    }

    set loggedIn(value) {
        this._loggedIn = value;
    }

    /**
     * Observer Pattern: Subscribe to auth state changes.
     */
    subscribe(callback) {
        this.listeners.push(callback);
        // Immediate call with current state
        callback(this.user, this.loggedIn);
        return () => {
            this.listeners = this.listeners.filter(l => l !== callback);
        };
    }

    /**
     * Notify all observers of a state change.
     */
    notify() {
        this.listeners.forEach(callback => callback(this.user, this.loggedIn));
    }

    async checkStatus() {
        try {
            const status = await this.api('/api/auth/status', { suppressAuthRedirect: true });
            this._loggedIn = status.logged_in;
            this.user = status.user || null;
            this.notify(); // State changed
            return status;
        } catch (err) {
            this._loggedIn = false;
            this.user = null;
            this.notify();
            throw err;
        }
    }

    async login(username, password) {
        const body = JSON.stringify({ username, password });
        await this.api('/api/auth/login', { method: 'POST', body });
        return await this.checkStatus(); // checkStatus triggers notify()
    }

    async logout() {
        await this.api('/api/auth/logout', { method: 'POST' }).catch(() => {});
        this._loggedIn = false;
        this.user = null;
        this.notify(); // State changed
    }

    hasPermission(permission) {
        if (!this.loggedIn || !this.user) return false;
        const caps = this.user.capabilities || [];
        return caps.includes(permission);
    }
}
