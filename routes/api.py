from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Summary, Tag, SummaryTag, SavedUrl
from services.article_extractor import ArticleExtractor
from services.llm_service import LLMService
from services.url_processor import URLProcessor
import json
from datetime import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/process-urls', methods=['POST'])
@login_required
def process_urls():
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        
        if not urls:
            return jsonify({'error': 'No URLs provided'}), 400
        
        url_processor = URLProcessor()
        processed_urls = []
        
        for url in urls:
            result = url_processor.process_url(url.strip())
            if result:
                processed_urls.append(result)
        
        return jsonify({
            'urls': processed_urls,
            'total': len(processed_urls)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/extract-article', methods=['POST'])
@login_required
def extract_article():
    try:
        data = request.get_json()
        url = data.get('url')
        manual_text = data.get('manual_text')
        
        if not url and not manual_text:
            return jsonify({'error': 'URL or manual text required'}), 400
        
        extractor = ArticleExtractor()
        
        if manual_text:
            # Use manually provided text
            result = {
                'url': url or 'Manual Input',
                'title': data.get('title', 'Manual Input'),
                'author': data.get('author', ''),
                'publication_date': None,
                'content': manual_text,
                'word_count': len(manual_text.split()),
                'is_paywalled': False,
                'manual_input': True
            }
        else:
            result = extractor.extract(url)
        
        if not result:
            return jsonify({'error': 'Failed to extract article content'}), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/generate-summary', methods=['POST'])
@login_required
def generate_summary():
    try:
        data = request.get_json()
        
        # Required fields
        content = data.get('content')
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        # Summary settings
        length = data.get('length', current_user.default_length)
        tone = data.get('tone', current_user.default_tone)
        format_type = data.get('format', current_user.default_format)
        model = data.get('model', current_user.default_model)
        custom_word_count = data.get('custom_word_count')
        
        # Article metadata
        url = data.get('url', '')
        title = data.get('title', '')
        author = data.get('author', '')
        publication_date = data.get('publication_date')
        
        # Initialize LLM service
        llm_service = LLMService(current_user)
        
        # Generate summary
        summary_result = llm_service.generate_summary(
            content=content,
            length=length,
            tone=tone,
            format_type=format_type,
            model=model,
            custom_word_count=custom_word_count
        )
        
        if not summary_result:
            return jsonify({'error': 'Failed to generate summary'}), 500
        
        # Parse publication date
        pub_date = None
        if publication_date:
            try:
                pub_date = datetime.fromisoformat(publication_date.replace('Z', '+00:00'))
            except:
                pass
        
        # Save summary to database
        summary = Summary(
            user_id=current_user.id,
            url=url,
            title=title,
            author=author,
            publication_date=pub_date,
            original_text=content[:10000],  # Limit stored original text
            summary_text=summary_result['text'],
            length_setting=length,
            tone_setting=tone,
            format_setting=format_type,
            model_used=model,
            word_count=summary_result['word_count']
        )
        
        db.session.add(summary)
        db.session.commit()
        
        return jsonify({
            'summary': {
                'id': summary.id,
                'text': summary_result['text'],
                'word_count': summary_result['word_count'],
                'metadata': {
                    'title': title,
                    'author': author,
                    'publication_date': publication_date,
                    'url': url,
                    'analysis_date': summary.created_at.isoformat()
                },
                'settings': {
                    'length': length,
                    'tone': tone,
                    'format': format_type,
                    'model': model
                }
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/add-tags', methods=['POST'])
@login_required
def add_tags():
    try:
        data = request.get_json()
        summary_id = data.get('summary_id')
        tag_names = data.get('tags', [])
        
        if not summary_id or not tag_names:
            return jsonify({'error': 'Summary ID and tags required'}), 400
        
        # Verify summary belongs to current user
        summary = Summary.query.filter_by(id=summary_id, user_id=current_user.id).first()
        if not summary:
            return jsonify({'error': 'Summary not found'}), 404
        
        added_tags = []
        for tag_name in tag_names:
            tag_name = tag_name.strip().lower()
            if not tag_name:
                continue
            
            # Get or create tag
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
                db.session.flush()  # Get the ID
            
            # Check if tag already exists for this summary
            existing_summary_tag = SummaryTag.query.filter_by(
                summary_id=summary_id, 
                tag_id=tag.id
            ).first()
            
            if not existing_summary_tag:
                summary_tag = SummaryTag(summary_id=summary_id, tag_id=tag.id)
                db.session.add(summary_tag)
                added_tags.append(tag_name)
        
        db.session.commit()
        
        return jsonify({
            'added_tags': added_tags,
            'total_tags': len(summary.get_tag_names())
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/remove-tag', methods=['POST'])
@login_required
def remove_tag():
    try:
        data = request.get_json()
        summary_id = data.get('summary_id')
        tag_name = data.get('tag_name')
        
        if not summary_id or not tag_name:
            return jsonify({'error': 'Summary ID and tag name required'}), 400
        
        # Verify summary belongs to current user
        summary = Summary.query.filter_by(id=summary_id, user_id=current_user.id).first()
        if not summary:
            return jsonify({'error': 'Summary not found'}), 404
        
        # Find and remove the tag association
        tag = Tag.query.filter_by(name=tag_name.strip().lower()).first()
        if tag:
            summary_tag = SummaryTag.query.filter_by(
                summary_id=summary_id, 
                tag_id=tag.id
            ).first()
            
            if summary_tag:
                db.session.delete(summary_tag)
                db.session.commit()
                return jsonify({'success': True})
        
        return jsonify({'error': 'Tag not found'}), 404
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/get-tag-suggestions', methods=['GET'])
@login_required
def get_tag_suggestions():
    try:
        query = request.args.get('q', '').strip().lower()
        
        # Get user's existing tags that match the query
        tags = Tag.query.join(SummaryTag)\
                       .join(Summary)\
                       .filter(Summary.user_id == current_user.id)\
                       .filter(Tag.name.contains(query))\
                       .distinct()\
                       .limit(10).all()
        
        suggestions = [tag.name for tag in tags]
        
        return jsonify({'suggestions': suggestions})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/delete-summary', methods=['POST'])
@login_required
def delete_summary():
    """Delete a summary and its associated tags"""
    try:
        data = request.get_json()
        summary_id = data.get('summary_id')
        
        if not summary_id:
            return jsonify({'error': 'Summary ID required'}), 400
        
        # Verify summary belongs to current user
        summary = Summary.query.filter_by(id=summary_id, user_id=current_user.id).first()
        if not summary:
            return jsonify({'error': 'Summary not found'}), 404
        
        # Delete the summary (cascade will handle tags)
        db.session.delete(summary)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Summary deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/debug-extract', methods=['POST'])
@login_required
def debug_extract():
    """Debug endpoint to see raw extraction results"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL required'}), 400
        
        extractor = ArticleExtractor()
        result = extractor.extract(url)
        
        # Return detailed debug information
        return jsonify({
            'debug_info': {
                'url': url,
                'extraction_result': result,
                'raw_content_preview': result.get('content', '')[:500] if result.get('content') else 'No content extracted'
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'debug': True}), 500

@api_bp.route('/save-url', methods=['POST'])
@login_required
def save_url():
    """Save a URL for later analysis"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        description = data.get('description', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Check if URL already exists for this user
        existing_url = SavedUrl.query.filter_by(
            user_id=current_user.id,
            url=url
        ).first()
        
        if existing_url:
            return jsonify({'error': 'URL already saved'}), 400
        
        # Try to extract title for better organization
        title = None
        try:
            extractor = ArticleExtractor()
            result = extractor.extract(url)
            if result:
                title = result.get('title')
        except:
            pass  # Continue without title if extraction fails
        
        # Create saved URL
        saved_url = SavedUrl(
            user_id=current_user.id,
            url=url,
            title=title,
            description=description
        )
        
        db.session.add(saved_url)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'saved_url': {
                'id': saved_url.id,
                'url': saved_url.url,
                'title': saved_url.title,
                'description': saved_url.description,
                'created_at': saved_url.created_at.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/saved-urls', methods=['GET'])
@login_required
def get_saved_urls():
    """Get all saved URLs for the current user"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        
        query = SavedUrl.query.filter_by(user_id=current_user.id)
        
        if search:
            query = query.filter(
                db.or_(
                    SavedUrl.url.contains(search),
                    SavedUrl.title.contains(search),
                    SavedUrl.description.contains(search)
                )
            )
        
        saved_urls = query.order_by(SavedUrl.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get summary data for analyzed URLs
        saved_urls_data = []
        for url in saved_urls.items:
            url_data = {
                'id': url.id,
                'url': url.url,
                'title': url.title,
                'description': url.description,
                'is_analyzed': url.is_analyzed,
                'created_at': url.created_at.isoformat(),
                'updated_at': url.updated_at.isoformat()
            }
            
            # If analyzed, get the most recent summary
            if url.is_analyzed:
                summary = Summary.query.filter_by(
                    user_id=current_user.id,
                    url=url.url
                ).order_by(Summary.created_at.desc()).first()
                
                if summary:
                    url_data['summary'] = {
                        'id': summary.id,
                        'text': summary.summary_text,
                        'word_count': summary.word_count,
                        'length_setting': summary.length_setting,
                        'tone_setting': summary.tone_setting,
                        'format_setting': summary.format_setting,
                        'model_used': summary.model_used,
                        'author': summary.author,
                        'publication_date': summary.publication_date.isoformat() if summary.publication_date else None,
                        'created_at': summary.created_at.isoformat()
                    }
            
            saved_urls_data.append(url_data)
        
        return jsonify({
            'saved_urls': saved_urls_data,
            'pagination': {
                'page': saved_urls.page,
                'pages': saved_urls.pages,
                'per_page': saved_urls.per_page,
                'total': saved_urls.total
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/delete-saved-url', methods=['POST'])
@login_required
def delete_saved_url():
    """Delete a saved URL"""
    try:
        data = request.get_json()
        url_id = data.get('url_id')
        
        if not url_id:
            return jsonify({'error': 'URL ID required'}), 400
        
        # Verify saved URL belongs to current user
        saved_url = SavedUrl.query.filter_by(id=url_id, user_id=current_user.id).first()
        if not saved_url:
            return jsonify({'error': 'Saved URL not found'}), 404
        
        db.session.delete(saved_url)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Saved URL deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/analyze-saved-url', methods=['POST'])
@login_required
def analyze_saved_url():
    """Analyze a saved URL and create a summary"""
    try:
        data = request.get_json()
        url_id = data.get('url_id')
        
        if not url_id:
            return jsonify({'error': 'URL ID required'}), 400
        
        # Verify saved URL belongs to current user
        saved_url = SavedUrl.query.filter_by(id=url_id, user_id=current_user.id).first()
        if not saved_url:
            return jsonify({'error': 'Saved URL not found'}), 404
        
        # Extract article content
        extractor = ArticleExtractor()
        result = extractor.extract(saved_url.url)
        
        if not result:
            return jsonify({'error': 'Failed to extract article content'}), 400
        
        # Use user's default settings for analysis
        length = data.get('length', current_user.default_length)
        tone = data.get('tone', current_user.default_tone)
        format_type = data.get('format', current_user.default_format)
        model = data.get('model', current_user.default_model)
        
        # Generate summary
        llm_service = LLMService(current_user)
        summary_result = llm_service.generate_summary(
            content=result['content'],
            length=length,
            tone=tone,
            format_type=format_type,
            model=model
        )
        
        if not summary_result:
            return jsonify({'error': 'Failed to generate summary'}), 500
        
        # Parse publication date
        pub_date = None
        if result.get('publication_date'):
            try:
                pub_date = datetime.fromisoformat(result['publication_date'].replace('Z', '+00:00'))
            except:
                pass
        
        # Save summary to database
        summary = Summary(
            user_id=current_user.id,
            url=saved_url.url,
            title=result.get('title', saved_url.title),
            author=result.get('author'),
            publication_date=pub_date,
            original_text=result['content'][:10000],
            summary_text=summary_result['text'],
            length_setting=length,
            tone_setting=tone,
            format_setting=format_type,
            model_used=model,
            word_count=summary_result['word_count']
        )
        
        db.session.add(summary)
        
        # Mark saved URL as analyzed
        saved_url.is_analyzed = True
        saved_url.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'summary': {
                'id': summary.id,
                'text': summary_result['text'],
                'word_count': summary_result['word_count'],
                'metadata': {
                    'title': summary.title,
                    'author': summary.author,
                    'publication_date': pub_date.isoformat() if pub_date else None,
                    'url': summary.url,
                    'analysis_date': summary.created_at.isoformat()
                }
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500