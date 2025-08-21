from flask import Blueprint, render_template

bp = Blueprint('main_routes', __name__)

@bp.route('/')
def index():
    """Serves the single page application's entry point."""
    return render_template('base.html')
