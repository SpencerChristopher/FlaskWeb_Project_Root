"""
This module defines the main route for the Flask application.

It serves the primary HTML shell for the Single Page Application (SPA).
"""

from flask import Blueprint, render_template, Response, request, abort

bp = Blueprint("main_routes", __name__)


@bp.route("/", defaults={"path": ""})
@bp.route("/<path:path>")
def index(path: str) -> Response:
    """
    Serves the single page application's main HTML file.

    Captures all paths to support client-side routing (History API).
    Any path not matched by other blueprints (like /api/) will serve base.html.
    EXCEPT if the path starts with /api/, in which case we should let it 404.
    """
    if request.path.startswith("/api/"):
        abort(404)

    return render_template("base.html")
