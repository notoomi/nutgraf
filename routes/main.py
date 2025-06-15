from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, FileField
from wtforms.validators import DataRequired, Optional, NumberRange
from models import db, User, Summary, Tag, SummaryTag
from datetime import datetime, timedelta
import json

main_bp = Blueprint('main', __name__)

class SettingsForm(FlaskForm):
    openai_api_key = StringField('OpenAI API Key')
    anthropic_api_key = StringField('Anthropic API Key')
    default_length = SelectField('Default Length', 
                                choices=[('brief', 'Brief'), ('standard', 'Standard'), ('in_depth', 'In-Depth')],
                                default='standard')
    default_tone = SelectField('Default Tone',
                              choices=[('neutral', 'Neutral'), ('conversational', 'Conversational'), ('professional', 'Professional')],
                              default='neutral')
    default_format = SelectField('Default Format',
                                choices=[('prose', 'Prose'), ('bullets', 'Bullet Points')],
                                default='prose')
    default_model = SelectField('Default Model',
                               choices=[('gpt-3.5-turbo', 'GPT-3.5 Turbo'), ('gpt-4', 'GPT-4'), ('gpt-4o', 'GPT-4o'), ('claude-3-sonnet', 'Claude 3.5 Sonnet'), ('claude-3-haiku', 'Claude 3 Haiku')],
                               default='gpt-3.5-turbo')

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get recent summaries
    recent_summaries = Summary.query.filter_by(user_id=current_user.id)\
                                  .order_by(Summary.created_at.desc())\
                                  .limit(5).all()
    
    # Get summary statistics
    total_summaries = Summary.query.filter_by(user_id=current_user.id).count()
    this_week = datetime.utcnow() - timedelta(days=7)
    week_summaries = Summary.query.filter_by(user_id=current_user.id)\
                                 .filter(Summary.created_at >= this_week).count()
    
    return render_template('main/dashboard.html', 
                         recent_summaries=recent_summaries,
                         total_summaries=total_summaries,
                         week_summaries=week_summaries)

@main_bp.route('/analyze')
@login_required
def analyze():
    return render_template('main/analyze.html')

@main_bp.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    tag_filter = request.args.get('tag')
    search_query = request.args.get('search')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Build query
    query = Summary.query.filter_by(user_id=current_user.id)
    
    if search_query:
        query = query.filter(
            (Summary.title.contains(search_query)) |
            (Summary.summary_text.contains(search_query)) |
            (Summary.url.contains(search_query))
        )
    
    if tag_filter:
        query = query.join(SummaryTag).join(Tag).filter(Tag.name == tag_filter)
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Summary.created_at >= date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Summary.created_at <= date_to)
        except ValueError:
            pass
    
    summaries = query.order_by(Summary.created_at.desc())\
                    .paginate(page=page, per_page=10, error_out=False)
    
    # Get all tags for filter dropdown
    all_tags = Tag.query.join(SummaryTag)\
                      .join(Summary)\
                      .filter(Summary.user_id == current_user.id)\
                      .distinct().all()
    
    return render_template('main/history.html', 
                         summaries=summaries,
                         all_tags=all_tags,
                         current_filters={
                             'tag': tag_filter,
                             'search': search_query,
                             'date_from': date_from,
                             'date_to': date_to
                         })

@main_bp.route('/summary/<int:summary_id>')
@login_required
def view_summary(summary_id):
    summary = Summary.query.filter_by(id=summary_id, user_id=current_user.id).first_or_404()
    return render_template('main/summary.html', summary=summary)

@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm()
    
    if request.method == 'GET':
        # Populate form with current settings
        form.default_length.data = current_user.default_length
        form.default_tone.data = current_user.default_tone
        form.default_format.data = current_user.default_format
        form.default_model.data = current_user.default_model
        # Don't populate API keys for security
    
    if form.validate_on_submit():
        # Update user preferences
        current_user.default_length = form.default_length.data
        current_user.default_tone = form.default_tone.data
        current_user.default_format = form.default_format.data
        current_user.default_model = form.default_model.data
        
        # Update AI API keys if provided
        if form.openai_api_key.data:
            current_user.set_openai_key(form.openai_api_key.data)
        
        if form.anthropic_api_key.data:
            current_user.set_anthropic_key(form.anthropic_api_key.data)
        
        try:
            db.session.commit()
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('main.settings'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to update settings. Please try again.', 'error')
    
    return render_template('main/settings.html', form=form)

@main_bp.route('/generate-api-key', methods=['POST'])
@login_required
def generate_api_key():
    """Generate a new Nutgraf API key for the current user"""
    try:
        current_user.generate_api_key()
        db.session.commit()
        flash('New API key generated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to generate API key. Please try again.', 'error')
    
    return redirect(url_for('main.settings'))

@main_bp.route('/revoke-api-key', methods=['POST'])
@login_required
def revoke_api_key():
    """Revoke the current user's API key"""
    try:
        current_user.nutgraf_api_key = None
        db.session.commit()
        flash('API key revoked successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to revoke API key. Please try again.', 'error')
    
    return redirect(url_for('main.settings'))

@main_bp.route('/api-docs')
def api_documentation():
    """Display API documentation"""
    return render_template('main/api_docs.html')