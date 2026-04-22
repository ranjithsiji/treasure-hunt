import os

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from models import GameConfig, Level, Question, QuestionMedia
from routes.admin import admin_bp
from routes.admin._helpers import (
    admin_required,
    _safe_int,
    _unique_filename,
    log_game_action,
)


@admin_bp.route('/level/<int:level_id>/questions')
@login_required
@admin_required
def manage_questions(level_id):
    level = Level.query.get_or_404(level_id)
    questions = Question.query.filter_by(level_id=level_id).order_by(Question.question_number).all()
    return render_template('admin/manage_questions.html', level=level, questions=questions)


@admin_bp.route('/level/<int:level_id>/questions/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_question(level_id):
    level = Level.query.get_or_404(level_id)

    if request.method == 'POST':
        question_text = (request.form.get('question_text') or '').strip()
        answer = (request.form.get('answer') or '').strip()
        if not question_text or not answer:
            flash('Question text and answer are required.', 'danger')
            return redirect(url_for('admin.add_question', level_id=level_id))

        points = _safe_int(request.form.get('points'), default=10, minimum=0)
        question_type = request.form.get('question_type', 'text')
        num_media = _safe_int(request.form.get('num_media'), default=0, minimum=0)

        max_q = Question.query.filter_by(level_id=level_id).order_by(Question.question_number.desc()).first()
        next_number = (max_q.question_number + 1) if max_q else 1

        media_url = None
        if 'question_image' in request.files:
            file = request.files['question_image']
            if file and file.filename:
                unique_filename = _unique_filename(file.filename)
                upload_folder = os.path.join('static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, unique_filename))
                media_url = f"uploads/{unique_filename}"
                if question_type == 'text':
                    question_type = 'image'

        question = Question(
            level_id=level_id,
            question_number=next_number,
            question_type=question_type,
            question_text=question_text,
            answer=answer,
            points=points,
            media_url=media_url,
        )
        db.session.add(question)
        db.session.commit()

        for i in range(num_media):
            media_type = request.form.get(f'media_type_{i}')
            media_caption = request.form.get(f'media_caption_{i}', '')
            file_key = f'media_file_{i}'
            if file_key in request.files:
                file = request.files[file_key]
                if file and file.filename:
                    unique_filename = _unique_filename(file.filename)
                    upload_folder = os.path.join('static', 'uploads', 'media')
                    os.makedirs(upload_folder, exist_ok=True)
                    file.save(os.path.join(upload_folder, unique_filename))
                    db.session.add(QuestionMedia(
                        question_id=question.id,
                        media_type=media_type,
                        media_url=f"uploads/media/{unique_filename}",
                        media_caption=media_caption,
                        display_order=i,
                    ))
        db.session.commit()

        log_game_action('QUESTION_ADDED', details=f'Question {next_number} added to Level {level.level_number}.')
        flash(f'Question {next_number} added successfully!', 'success')
        return redirect(url_for('admin.manage_questions', level_id=level_id))

    max_q = Question.query.filter_by(level_id=level_id).order_by(Question.question_number.desc()).first()
    next_question_number = (max_q.question_number + 1) if max_q else 1
    return render_template(
        'admin/add_edit_question.html',
        level=level,
        question=None,
        next_question_number=next_question_number,
    )


@admin_bp.route('/question/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    level = question.level

    if request.method == 'POST':
        question_text = (request.form.get('question_text') or '').strip()
        answer = (request.form.get('answer') or '').strip()
        if not question_text or not answer:
            flash('Question text and answer cannot be empty.', 'danger')
            return redirect(url_for('admin.edit_question', question_id=question_id))

        question.question_text = question_text
        question.answer = answer
        question.points = _safe_int(request.form.get('points'), default=10, minimum=0)
        num_media = _safe_int(request.form.get('num_media'), default=0, minimum=0)

        if request.form.get('remove_image') == 'true':
            if question.media_url:
                disk_path = os.path.join('static', question.media_url)
                if os.path.exists(disk_path):
                    os.remove(disk_path)
            question.media_url = None
        elif 'question_image' in request.files:
            file = request.files['question_image']
            if file and file.filename:
                unique_filename = _unique_filename(file.filename)
                upload_folder = os.path.join('static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, unique_filename))
                question.media_url = f"uploads/{unique_filename}"

        for media_id in request.form.getlist('delete_media'):
            media = QuestionMedia.query.get(_safe_int(media_id))
            if media and media.question_id == question.id:
                disk_path = os.path.join('static', media.media_url)
                if os.path.exists(disk_path):
                    os.remove(disk_path)
                db.session.delete(media)

        max_order = db.session.query(db.func.max(QuestionMedia.display_order)).filter_by(question_id=question.id).scalar() or 0
        for i in range(num_media):
            media_type = request.form.get(f'media_type_{i}')
            media_caption = request.form.get(f'media_caption_{i}', '')
            file_key = f'media_file_{i}'
            if file_key in request.files:
                file = request.files[file_key]
                if file and file.filename:
                    unique_filename = _unique_filename(file.filename)
                    upload_folder = os.path.join('static', 'uploads', 'media')
                    os.makedirs(upload_folder, exist_ok=True)
                    file.save(os.path.join(upload_folder, unique_filename))
                    db.session.add(QuestionMedia(
                        question_id=question.id,
                        media_type=media_type,
                        media_url=f"uploads/media/{unique_filename}",
                        media_caption=media_caption,
                        display_order=max_order + i + 1,
                    ))

        db.session.commit()
        log_game_action(
            'QUESTION_UPDATED',
            details=f'Question {question.question_number} in Level {level.level_number} updated.',
        )
        flash(f'Question {question.question_number} updated successfully!', 'success')
        return redirect(url_for('admin.manage_questions', level_id=level.id))

    return render_template('admin/add_edit_question.html', level=level, question=question)


@admin_bp.route('/question/<int:question_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    level = question.level
    level_id = question.level_id
    question_number = question.question_number
    config = GameConfig.query.first()

    if config and config.game_started:
        flash(
            'Cannot delete questions while the game is running. Stop the game first.',
            'danger',
        )
        return redirect(url_for('admin.manage_questions', level_id=level_id))

    if question.media_url:
        disk_path = os.path.join('static', question.media_url)
        if os.path.exists(disk_path):
            os.remove(disk_path)
    for media in question.media_files:
        disk_path = os.path.join('static', media.media_url)
        if os.path.exists(disk_path):
            os.remove(disk_path)

    db.session.delete(question)
    db.session.flush()

    subsequent = (
        Question.query
        .filter(Question.level_id == level_id, Question.question_number > question_number)
        .order_by(Question.question_number)
        .all()
    )
    for q in subsequent:
        q.question_number -= 1

    db.session.commit()
    log_game_action(
        'QUESTION_DELETED',
        details=f'Question {question_number} deleted from Level {level.level_number}. Remaining questions renumbered.',
    )
    flash(f'Question {question_number} deleted and remaining questions renumbered.', 'success')
    return redirect(url_for('admin.manage_questions', level_id=level_id))
