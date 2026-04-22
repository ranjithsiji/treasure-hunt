from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from models import Clue, Question
from routes.admin import admin_bp
from routes.admin._helpers import admin_required, _safe_int


@admin_bp.route('/question/<int:question_id>/clues', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_clues(question_id):
    question = Question.query.get_or_404(question_id)

    if request.method == 'POST':
        clue_text = (request.form.get('clue_text') or '').strip()
        if not clue_text:
            flash('Clue text cannot be empty.', 'danger')
            return redirect(url_for('admin.manage_clues', question_id=question_id))

        explanation = (request.form.get('explanation') or '').strip() or None
        max_clue = Clue.query.filter_by(question_id=question_id).order_by(Clue.clue_order.desc()).first()
        next_order = (max_clue.clue_order + 1) if max_clue else 1

        clue = Clue(question_id=question_id, clue_text=clue_text, explanation=explanation, clue_order=next_order)
        db.session.add(clue)
        db.session.commit()
        flash('Clue added successfully!', 'success')
        return redirect(url_for('admin.manage_clues', question_id=question_id))

    clues = Clue.query.filter_by(question_id=question_id).order_by(Clue.clue_order).all()
    return render_template('admin/manage_clues.html', question=question, clues=clues)


@admin_bp.route('/clue/<int:clue_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_clue(clue_id):
    clue = Clue.query.get_or_404(clue_id)
    question = clue.question

    if request.method == 'POST':
        clue_text = (request.form.get('clue_text') or '').strip()
        if not clue_text:
            flash('Clue text cannot be empty.', 'danger')
            return redirect(url_for('admin.edit_clue', clue_id=clue_id))

        new_order = _safe_int(request.form.get('clue_order'), default=clue.clue_order, minimum=1)
        duplicate = (
            Clue.query
            .filter(Clue.question_id == question.id, Clue.clue_order == new_order, Clue.id != clue.id)
            .first()
        )
        if duplicate:
            flash(f'Clue order {new_order} is already used by another clue. Choose a different order.', 'danger')
            return redirect(url_for('admin.edit_clue', clue_id=clue_id))

        clue.clue_text = clue_text
        clue.explanation = (request.form.get('explanation') or '').strip() or None
        clue.clue_order = new_order
        db.session.commit()
        flash('Clue updated successfully!', 'success')
        return redirect(url_for('admin.manage_clues', question_id=question.id))

    return render_template('admin/edit_clue.html', clue=clue, question=question)


@admin_bp.route('/clue/<int:clue_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_clue(clue_id):
    clue = Clue.query.get_or_404(clue_id)
    question_id = clue.question_id
    deleted_order = clue.clue_order

    db.session.delete(clue)
    db.session.flush()

    remaining = (
        Clue.query
        .filter(Clue.question_id == question_id, Clue.clue_order > deleted_order)
        .order_by(Clue.clue_order)
        .all()
    )
    for c in remaining:
        c.clue_order -= 1

    db.session.commit()
    flash('Clue deleted and remaining clues reordered.', 'success')
    return redirect(url_for('admin.manage_clues', question_id=question_id))
