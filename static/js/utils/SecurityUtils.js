/**
 * SecurityUtils.js
 * Centralized security helpers for modern Vanilla JS applications.
 */

/**
 * Escapes HTML special characters to prevent Reflected/Stored XSS.
 * Use this for all dynamic text being inserted into template literals.
 */
export function escapeHTML(str) {
    if (!str) return "";
    const htmlEntities = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
        "/": "&#47;",
    };
    return String(str).replace(/[&<>"'/]/g, (s) => htmlEntities[s]);
}

/**
 * Validates a URL against a strict whitelist of safe protocols.
 * Prevents 'javascript:' or 'data:' URI injections.
 */
export function validateURL(url, allowedProtocols = ["https:", "http:", "mailto:", "tel:"]) {
    if (!url) return "#";
    try {
        const parsed = new URL(url, window.location.origin);
        if (allowedProtocols.includes(parsed.protocol)) {
            return url;
        }
    } catch (e) {
        // Fallback for relative paths or invalid URLs
        if (url.startsWith("/") || url.startsWith("./") || url.startsWith("../")) {
            return url;
        }
    }
    console.warn("Security blocked invalid URL protocol:", url);
    return "javascript:void(0)";
}

/**
 * Sanitizes rich text content (HTML) using a whitelist approach.
 * Currently uses native DOMParser for basic cleanup.
 */
export function sanitizeHTML(html) {
    if (!html) return "";
    const doc = new DOMParser().parseFromString(html, 'text/html');
    
    // Remove all <script> tags
    const scripts = doc.querySelectorAll('script');
    scripts.forEach(s => s.remove());
    
    // Remove all event handlers (onmouseover, onclick, etc.)
    const allElements = doc.querySelectorAll('*');
    allElements.forEach(el => {
        for (let i = 0; i < el.attributes.length; i++) {
            const attr = el.attributes[i];
            if (attr.name.startsWith('on')) {
                el.removeAttribute(attr.name);
            }
        }
    });
    
    return doc.body.innerHTML;
}
