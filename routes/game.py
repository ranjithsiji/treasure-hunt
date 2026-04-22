from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import User, Team, GameConfig, Level, Question, Clue, TeamProgress, ClueUsage
from app import db
from datetime import datetime
import sqlalchemy as sa

game_bp = Blueprint('game', __name__)


def log_game_action(action, team_id=None, details=None):
    from models import GameLog
    log = GameLog(
        team_id=team_id,
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        details=details,
    )
    db.session.add(log)
    db.session.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@game_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))

    if not current_user.team:
        flash('You are not assigned to any team. Please contact admin.', 'warning')
        return render_template('game/no_team.html')

    config = GameConfig.query.first()
    team = current_user.team

    if not config or not config.game_started:
        return render_template('game/waiting.html')

    current_level = Level.query.filter_by(level_number=team.current_level).first()

    # Issue #9 fix: level not found → clear error, no redirect loop back to join_team
    if not current_level:
        flash('Your assigned level no longer exists. Please contact admin.', 'danger')
        return render_template('game/waiting.html')

    # Fix #2: check is_active FIRST.
    # A team on a locked level should always see the locked screen,
    # regardless of how far through the questions they are.
    if not current_level.is_active:
        return render_template('game/level_locked.html', team=team, current_level=team.current_level)

    # Get total questions in this level (single query, reused below)
    total_questions = Question.query.filter_by(level_id=current_level.id).count()

    # Check if team has completed all questions in this level
    if team.current_question > total_questions:
        # Fix #7: compute qualified explicitly here — don't leave it to template inference
        qualified = team.current_level > current_level.level_number
        return render_template(
            'game/level_complete.html',
            team=team,
            level=current_level,
            qualified=qualified,
        )

    # Get current question
    current_question = Question.query.filter_by(
        level_id=current_level.id,
        question_number=team.current_question,
    ).first()

    # Fallback for new teams or out-of-sync question pointer
    if not current_question and team.current_question in (0, 1):
        current_question = (
            Question.query
            .filter_by(level_id=current_level.id)
            .order_by(Question.question_number)
            .first()
        )
        if current_question:
            team.current_question = current_question.question_number
            db.session.commit()

    if not current_question:
        flash('Question not found. Contact admin.', 'danger')
        return render_template('game/waiting.html')

    # Get/create progress entry
    progress = TeamProgress.query.filter_by(
        team_id=team.id,
        question_id=current_question.id,
    ).first()

    if not progress:
        progress = TeamProgress(
            team_id=team.id,
            question_id=current_question.id,
            level_number=current_level.level_number,
        )
        db.session.add(progress)
        db.session.commit()

    # Clues already used for this question
    used_clues = ClueUsage.query.filter_by(
        team_id=team.id,
        question_id=current_question.id,
    ).all()
    used_clue_ids = [uc.clue_id for uc in used_clues]

    # Issue #1/#7 fix: compute clues_remaining once (2 queries) and pass it in;
    # the property won't be re-invoked inside the template if we pass the value.
    clues_remaining = team.clues_remaining

    return render_template(
        'game/play.html',
        team=team,
        level=current_level,
        question=current_question,
        progress=progress,
        used_clue_ids=used_clue_ids,
        clues_remaining=clues_remaining,
        config=config,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Submit Answer
# ─────────────────────────────────────────────────────────────────────────────

@game_bp.route('/submit-answer', methods=['POST'])
@login_required
def submit_answer():
    if not current_user.team:
        return jsonify({'success': False, 'message': 'You are not assigned to any team.'})

    team = current_user.team

    # Issue #4 fix: safe int parse — no more 500 on bad/missing question_id
    try:
        question_id = int(request.form.get('question_id', 0))
        if question_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid request.'})

    answer = request.form.get('answer', '').strip()
    if not answer:
        return jsonify({'success': False, 'message': 'Answer cannot be empty.'})

    question = Question.query.get_or_404(question_id)
    config   = GameConfig.query.first()

    # Issue #3 fix: verify this question belongs to the team's current position
    current_level = Level.query.filter_by(level_number=team.current_level).first()
    if (not current_level
            or question.level_id != current_level.id
            or question.question_number != team.current_question):
        return jsonify({'success': False, 'message': 'Invalid question submission.'})

    # Check answer (case-insensitive)
    if answer.lower() != question.answer.lower():
        log_game_action(
            'SUBMIT_INCORRECT_ANSWER',
            team_id=team.id,
            details=f"Incorrect answer for Question {question.question_number} in Level {current_level.level_number}.",
        )
        return jsonify({'success': False, 'message': 'Incorrect answer. Try again!'})

    # ── Correct answer path ──────────────────────────────────────────────────
    progress = TeamProgress.query.filter_by(
        team_id=team.id,
        question_id=question_id,
    ).first()

    if not progress or progress.is_completed:
        return jsonify({'success': False, 'message': 'Question already completed.'})

    progress.is_completed = True
    progress.completed_at = datetime.utcnow()
    time_diff = progress.completed_at - progress.started_at
    progress.time_taken = int(time_diff.total_seconds())

    # Move pointer to next question
    team.current_question += 1

    total_questions_in_level = Question.query.filter_by(level_id=question.level_id).count()

    if team.current_question > total_questions_in_level:
        # Team finished all questions in this level
        if not current_level.is_final:
            # Issue #2 fix: re-count advanced teams after flushing our own team's update
            # to detect the race window as tightly as possible before final commit.
            db.session.flush()

            advanced_teams_count = Team.query.filter(
                Team.current_level > current_level.level_number
            ).count()

            if advanced_teams_count < current_level.teams_passing:
                team.current_level = current_level.level_number + 1
                team.current_question = 1

                # Auto-close level when last qualification slot is filled
                if advanced_teams_count + 1 >= current_level.teams_passing:
                    current_level.is_active = False
                    log_game_action(
                        'LEVEL_AUTO_CLOSED',
                        details=(
                            f"Level {current_level.level_number} auto-closed — "
                            f"all {current_level.teams_passing} qualification slots filled."
                        ),
                    )

                log_game_action(
                    'LEVEL_ADVANCE',
                    team_id=team.id,
                    details=(
                        f"Team qualified for Level {team.current_level} "
                        f"(Slot {advanced_teams_count + 1}/{current_level.teams_passing} filled)."
                    ),
                )
            else:
                log_game_action(
                    'LEVEL_COMPLETE_NOT_QUALIFIED',
                    team_id=team.id,
                    details=(
                        f"Team finished Level {current_level.level_number} "
                        f"but did not qualify — all {current_level.teams_passing} slots filled."
                    ),
                )
        else:
            # Final level
            db.session.flush()
            finished_count = Team.query.filter(
                Team.current_level == current_level.level_number,
                Team.current_question > total_questions_in_level,
            ).count()

            log_game_action(
                'GAME_COMPLETE',
                team_id=team.id,
                details=f"Team completed the final level! (Rank: {finished_count + 1})",
            )

            if current_level.teams_passing > 0 and finished_count + 1 >= current_level.teams_passing:
                current_level.is_active = False
                log_game_action(
                    'LEVEL_AUTO_CLOSED',
                    details=(
                        f"Final Level {current_level.level_number} auto-closed — "
                        f"{current_level.teams_passing} teams have finished."
                    ),
                )

    # Issue #5 fix: single commit at the end — no intermediate partial commits
    db.session.commit()

    log_game_action(
        'SUBMIT_CORRECT_ANSWER',
        team_id=team.id,
        details=f"Question {question.question_number} in Level {current_level.level_number} answered correctly.",
    )

    response_data = {
        'success': True,
        'message': 'Correct answer!',
        'redirect': url_for('game.dashboard'),
        'has_explanation': bool(question.explanation),
    }
    if question.explanation:
        response_data['explanation'] = question.explanation

    return jsonify(response_data)


# ─────────────────────────────────────────────────────────────────────────────
# Get Clue
# ─────────────────────────────────────────────────────────────────────────────

@game_bp.route('/get-clue/<int:question_id>')
@login_required
def get_clue(question_id):
    if not current_user.team:
        return jsonify({'success': False, 'message': 'You are not assigned to any team.'})

    team     = current_user.team
    question = Question.query.get_or_404(question_id)
    level    = question.level

    # Issue #7 fix: compute clues_remaining once at the top
    clues_remaining = team.clues_remaining

    if clues_remaining <= 0:
        return jsonify({'success': False, 'message': 'You have used all available clues for the entire game.'})

    # Issue #6 fix: guard "no clues defined" BEFORE the loop
    clues = Clue.query.filter_by(question_id=question_id).order_by(Clue.clue_order).all()
    if not clues:
        return jsonify({'success': False, 'message': 'There are no clues defined for this question.'})

    used_clue_ids = [
        uc.clue_id for uc in
        ClueUsage.query.filter_by(team_id=team.id, question_id=question_id).all()
    ]

    next_clue = next((c for c in clues if c.id not in used_clue_ids), None)
    if not next_clue:
        return jsonify({'success': False, 'message': 'You have already used all available clues for this question.'})

    # Record usage
    clue_usage = ClueUsage(team_id=team.id, question_id=question_id, clue_id=next_clue.id)
    db.session.add(clue_usage)

    progress = TeamProgress.query.filter_by(team_id=team.id, question_id=question_id).first()
    if progress:
        progress.clues_used += 1

    db.session.commit()

    # Issue #7 fix: derive new remaining from the already-known value; no extra query
    new_remaining = clues_remaining - 1

    log_game_action(
        'USE_CLUE',
        team_id=team.id,
        details=(
            f"Clue {next_clue.clue_order} used for Question {question.question_number} "
            f"in Level {level.level_number}. (Remaining: {new_remaining})"
        ),
    )

    return jsonify({
        'success': True,
        'clue': next_clue.clue_text,
        'explanation': next_clue.explanation,
        'clues_remaining': new_remaining,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Join Team
# ─────────────────────────────────────────────────────────────────────────────

@game_bp.route('/join-team', methods=['GET', 'POST'])
@login_required
def join_team():
    if current_user.team:
        flash('You are already in a team.', 'info')
        return redirect(url_for('game.dashboard'))

    if request.method == 'POST':
        team_id = request.form.get('team_id')
        if team_id:
            team = Team.query.get(int(team_id))
            if team:
                current_user.team_id = team.id
                db.session.commit()
                flash(f'Successfully joined team {team.name}!', 'success')
                return redirect(url_for('game.dashboard'))

    teams = Team.query.all()
    return render_template('game/join_team.html', teams=teams)


# ─────────────────────────────────────────────────────────────────────────────
# Scoreboard — Issue #8 fix: batch aggregation replaces N+1 queries
# ─────────────────────────────────────────────────────────────────────────────

@game_bp.route('/scoreboard')
def scoreboard():
    config = GameConfig.query.first()

    teams = Team.query.all()

    # Aggregate completed questions and total time in two bulk queries
    completed_agg = dict(
        db.session.query(
            TeamProgress.team_id,
            db.func.count(TeamProgress.id),
        )
        .filter(TeamProgress.is_completed == True)   # noqa: E712
        .group_by(TeamProgress.team_id)
        .all()
    )

    time_agg = dict(
        db.session.query(
            TeamProgress.team_id,
            db.func.coalesce(db.func.sum(TeamProgress.time_taken), 0),
        )
        .filter(TeamProgress.is_completed == True)   # noqa: E712
        .group_by(TeamProgress.team_id)
        .all()
    )

    # Clues used per team in a single query
    clues_used_agg = dict(
        db.session.query(
            ClueUsage.team_id,
            db.func.count(ClueUsage.id),
        )
        .group_by(ClueUsage.team_id)
        .all()
    )

    clues_per_team = config.clues_per_team if config else 0

    team_stats = []
    for team in teams:
        clues_used = clues_used_agg.get(team.id, 0)
        team_stats.append({
            'team': team,
            'completed_questions': completed_agg.get(team.id, 0),
            'total_time': time_agg.get(team.id, 0),
            'current_level': team.current_level,
            'current_question': team.current_question,
            'clues_remaining': max(0, clues_per_team - clues_used),
        })

    # Sort: level desc → questions completed desc → time asc
    team_stats.sort(key=lambda x: (-x['current_level'], -x['completed_questions'], x['total_time']))

    return render_template('game/scoreboard.html', team_stats=team_stats)
