"""Home page content, static pages, and menu item management."""
from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from models import MenuItem, Page, SiteContent
from routes.admin import admin_bp
from routes.admin._helpers import admin_required


# ─────────────────────────────────────────────────────────────
# Site Content (Home Page)
# ─────────────────────────────────────────────────────────────

@admin_bp.route('/site-content', methods=['GET', 'POST'])
@login_required
@admin_required
def site_content():
    content = SiteContent.query.first()
    if request.method == 'POST':
        heading = request.form.get('heading', '').strip()
        subheading = request.form.get('subheading', '').strip()
        body_text = request.form.get('body_text', '').strip()

        if content:
            content.heading = heading
            content.subheading = subheading
            content.body_text = body_text
        else:
            content = SiteContent(heading=heading, subheading=subheading, body_text=body_text)
            db.session.add(content)

        db.session.commit()
        flash('Home page content updated successfully!', 'success')
        return redirect(url_for('admin.site_content'))

    return render_template('admin/site_content.html', content=content)


# ─────────────────────────────────────────────────────────────
# Pages Management
# ─────────────────────────────────────────────────────────────

@admin_bp.route('/pages')
@login_required
@admin_required
def manage_pages():
    pages = Page.query.order_by(Page.created_at.desc()).all()
    return render_template('admin/manage_pages.html', pages=pages)


@admin_bp.route('/pages/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_page():
    if request.method == 'POST':
        page_id = request.form.get('page_id', '').strip().lower()
        url = request.form.get('url', '').strip()
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        is_published = request.form.get('is_published') == 'on'

        if not url.startswith('/'):
            url = '/' + url

        if Page.query.filter_by(page_id=page_id).first():
            flash('A page with that Page ID already exists.', 'danger')
            return redirect(url_for('admin.add_page'))

        if Page.query.filter_by(url=url).first():
            flash('A page with that URL already exists.', 'danger')
            return redirect(url_for('admin.add_page'))

        page = Page(page_id=page_id, url=url, title=title, content=content, is_published=is_published)
        db.session.add(page)
        db.session.commit()
        flash(f'Page "{title}" created successfully!', 'success')
        return redirect(url_for('admin.manage_pages'))

    return render_template('admin/add_edit_page.html', page=None)


@admin_bp.route('/pages/<int:page_db_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_page(page_db_id):
    page = Page.query.get_or_404(page_db_id)

    if request.method == 'POST':
        page.page_id = request.form.get('page_id', '').strip().lower()
        page.url = request.form.get('url', '').strip()
        page.title = request.form.get('title', '').strip()
        page.content = request.form.get('content', '').strip()
        page.is_published = request.form.get('is_published') == 'on'

        if not page.url.startswith('/'):
            page.url = '/' + page.url

        db.session.commit()
        flash(f'Page "{page.title}" updated successfully!', 'success')
        return redirect(url_for('admin.manage_pages'))

    return render_template('admin/add_edit_page.html', page=page)


@admin_bp.route('/pages/<int:page_db_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_page(page_db_id):
    page = Page.query.get_or_404(page_db_id)
    title = page.title
    db.session.delete(page)
    db.session.commit()
    flash(f'Page "{title}" deleted.', 'success')
    return redirect(url_for('admin.manage_pages'))


# ─────────────────────────────────────────────────────────────
# Menu Management
# ─────────────────────────────────────────────────────────────

@admin_bp.route('/menu')
@login_required
@admin_required
def manage_menu():
    items = MenuItem.query.order_by(MenuItem.position).all()
    return render_template('admin/manage_menu.html', items=items)


@admin_bp.route('/menu/add', methods=['POST'])
@login_required
@admin_required
def add_menu_item():
    text = request.form.get('text', '').strip()
    link = request.form.get('link', '').strip()
    position = int(request.form.get('position', 0))
    is_active = request.form.get('is_active') == 'on'

    item = MenuItem(text=text, link=link, position=position, is_active=is_active)
    db.session.add(item)
    db.session.commit()
    flash(f'Menu item "{text}" added!', 'success')
    return redirect(url_for('admin.manage_menu'))


@admin_bp.route('/menu/<int:item_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.text = request.form.get('text', '').strip()
    item.link = request.form.get('link', '').strip()
    item.position = int(request.form.get('position', 0))
    item.is_active = request.form.get('is_active') == 'on'
    db.session.commit()
    flash(f'Menu item "{item.text}" updated!', 'success')
    return redirect(url_for('admin.manage_menu'))


@admin_bp.route('/menu/<int:item_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    text = item.text
    db.session.delete(item)
    db.session.commit()
    flash(f'Menu item "{text}" deleted.', 'success')
    return redirect(url_for('admin.manage_menu'))
