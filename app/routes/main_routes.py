"""
This module defines the main route for the Flask application.

It serves the primary HTML shell for the Single Page Application (SPA).
"""

from flask import Blueprint, render_template, Response

bp = Blueprint('main_routes', __name__)

@bp.route('/')
def index() -> Response:
    """
    Serves the single page application's main HTML file.

    This acts as the entry point for the frontend application.

    Returns:
        Response: The rendered base.html template.
    """
    return render_template('base.html')

