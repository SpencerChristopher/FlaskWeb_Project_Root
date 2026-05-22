"""
This module defines the main route for the Flask application.

It serves the primary HTML shell for the Single Page Application (SPA).
"""

import os
from flask import Blueprint, render_template, Response, request, abort

bp = Blueprint("main_routes", __name__)

_NON_SPA_ROOT_FILENAMES = {
    "ads.txt",
    "browserconfig.xml",
    "humans.txt",
    "manifest.json",
    "robots.txt",
    "security.txt",
    "sitemap.xml",
    "sitemap.xml.gz",
    "site.webmanifest",
}
_NON_SPA_ROOT_SUFFIXES = (".json", ".txt", ".xml", ".xml.gz")
_SENSITIVE_SUFFIXES = (".bak", ".env", ".ini")


def _is_non_spa_request(path: str) -> bool:
    """Return True when the path is clearly not a valid SPA route."""
    normalized_path = path.strip("/")
    if not normalized_path:
        return False

    segments = [segment.lower() for segment in normalized_path.split("/") if segment]
    if not segments:
        return False

    if segments[0] == "api":
        return True

    if any(segment.startswith(".") and segment != ".well-known" for segment in segments):
        return True

    leaf = segments[-1]
    if leaf.endswith(_SENSITIVE_SUFFIXES):
        return True

    if len(segments) == 1 and (
        leaf in _NON_SPA_ROOT_FILENAMES or leaf.endswith(_NON_SPA_ROOT_SUFFIXES)
    ):
        return True

    return False


@bp.route("/", defaults={"path": ""})
@bp.route("/<path:path>")
def index(path: str) -> Response:
    """
    Serves the single page application's main HTML file.

    Captures all paths to support client-side routing (History API).
    Any path not matched by other blueprints (like /api/) will serve base.html.
    EXCEPT if the path starts with /api/, in which case we should let it 404.
    """
    if _is_non_spa_request(request.path):
        abort(404)

    turnstile_site_key = os.environ.get("TURNSTILE_SITE_KEY", "")
    turnstile_enabled = (
        os.environ.get("TURNSTILE_ENABLED", "true").strip().lower()
        in {"1", "true", "yes", "on"}
    )
    turnstile_login_enabled = (
        os.environ.get("TURNSTILE_LOGIN_ENABLED", "false").strip().lower()
        in {"1", "true", "yes", "on"}
    )

    return render_template(
        "base.html",
        turnstile_site_key=turnstile_site_key,
        turnstile_enabled=turnstile_enabled,
        turnstile_login_enabled=turnstile_login_enabled,
    )
