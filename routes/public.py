from flask import Blueprint, render_template, abort
from models import SiteContent, Page


public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def home():
    content = SiteContent.query.first()
    return render_template('public/home.html', content=content)


@public_bp.route('/p/<string:page_url_slug>')
def view_page(page_url_slug):
    """Serve a custom admin-created page by its slug (page_id)."""
    page = Page.query.filter_by(page_id=page_url_slug, is_published=True).first_or_404()
    return render_template('public/page.html', page=page)
