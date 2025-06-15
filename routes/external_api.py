from flask import Blueprint, request, jsonify
from functools import wraps
from models import db, User, Summary
from services.article_extractor import ArticleExtractor
from services.llm_service import LLMService
from datetime import datetime
import json

external_api_bp = Blueprint('external_api', __name__, url_prefix='/v1')

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = None
        
        # Check for API key in Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            api_key = auth_header.split(' ', 1)[1]
        
        # Check for API key in X-API-Key header (alternative)
        if not api_key:
            api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': 'Please provide your API key in the Authorization header as "Bearer YOUR_KEY" or in the X-API-Key header'
            }), 401
        
        # Find user by API key
        user = User.query.filter_by(nutgraf_api_key=api_key).first()
        if not user:
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid'
            }), 401
        
        # Check if user is active
        if not user.is_active:
            return jsonify({
                'error': 'Account disabled',
                'message': 'Your account has been disabled'
            }), 403
        
        # Check rate limits
        if not user.can_make_api_call():
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': f'You have exceeded your monthly limit of {user.api_calls_limit} API calls',
                'usage': {
                    'calls_made': user.api_calls_made,
                    'calls_limit': user.api_calls_limit
                }
            }), 429
        
        # Add user to request context
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

@external_api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Nutgraf API',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

@external_api_bp.route('/summarize', methods=['POST'])
@require_api_key
def summarize():
    """
    Summarize content from URL or text
    
    Expected JSON payload:
    {
        "url": "https://example.com/article",  // Optional if text is provided
        "text": "Article content...",          // Optional if url is provided
        "title": "Article Title",             // Optional
        "length": "standard",                 // Optional: brief, standard, in_depth, custom
        "tone": "neutral",                    // Optional: neutral, conversational, professional
        "format": "prose",                    // Optional: prose, bullets
        "model": "gpt-3.5-turbo",            // Optional: model to use
        "custom_word_count": 300,            // Optional: if length is "custom"
        "save_summary": true                  // Optional: whether to save to user's history
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body must be valid JSON'
            }), 400
        
        url = data.get('url')
        text = data.get('text')
        
        if not url and not text:
            return jsonify({
                'error': 'Missing content',
                'message': 'Either "url" or "text" must be provided'
            }), 400
        
        # Extract content if URL is provided
        if url and not text:
            extractor = ArticleExtractor()
            extraction_result = extractor.extract(url)
            
            if not extraction_result:
                return jsonify({
                    'error': 'Extraction failed',
                    'message': 'Failed to extract content from the provided URL'
                }), 400
            
            text = extraction_result.get('content')
            title = data.get('title') or extraction_result.get('title', '')
            author = extraction_result.get('author', '')
            publication_date = extraction_result.get('publication_date')
        else:
            title = data.get('title', '')
            author = data.get('author', '')
            publication_date = None
        
        if not text:
            return jsonify({
                'error': 'No content',
                'message': 'No content could be extracted or provided'
            }), 400
        
        # Get summarization parameters
        user = request.current_user
        length = data.get('length', user.default_length)
        tone = data.get('tone', user.default_tone)
        format_type = data.get('format', user.default_format)
        model = data.get('model', user.default_model)
        custom_word_count = data.get('custom_word_count')
        save_summary = data.get('save_summary', False)
        
        # Get optional API keys from request and validate format
        provided_openai_key = data.get('openai_api_key')
        provided_anthropic_key = data.get('anthropic_api_key')
        
        # Basic validation for provided API keys
        if provided_openai_key and not provided_openai_key.startswith('sk-'):
            return jsonify({
                'error': 'Invalid OpenAI API key format',
                'message': 'OpenAI API keys should start with "sk-"'
            }), 400
            
        if provided_anthropic_key and not provided_anthropic_key.startswith('sk-ant-'):
            return jsonify({
                'error': 'Invalid Anthropic API key format', 
                'message': 'Anthropic API keys should start with "sk-ant-"'
            }), 400
        
        # Initialize LLM service with provided keys (if any)
        llm_service = LLMService(user, provided_openai_key, provided_anthropic_key)
        
        # Check if we have the necessary API keys for the requested model
        if model.startswith('gpt') and not llm_service.openai_client:
            if not provided_openai_key and not user.get_openai_key():
                return jsonify({
                    'error': 'OpenAI API key required',
                    'message': 'This model requires an OpenAI API key. Please provide one in your account settings or in the "openai_api_key" field of this request.'
                }), 400
        elif model.startswith('claude') and not llm_service.anthropic_client:
            if not provided_anthropic_key and not user.get_anthropic_key():
                return jsonify({
                    'error': 'Anthropic API key required',
                    'message': 'This model requires an Anthropic API key. Please provide one in your account settings or in the "anthropic_api_key" field of this request.'
                }), 400
        
        # Generate summary
        summary_result = llm_service.generate_summary(
            content=text,
            length=length,
            tone=tone,
            format_type=format_type,
            model=model,
            custom_word_count=custom_word_count
        )
        
        if not summary_result:
            return jsonify({
                'error': 'Summarization failed',
                'message': 'Failed to generate summary'
            }), 500
        
        # Increment API usage
        user.increment_api_usage()
        
        # Save summary if requested
        summary_id = None
        if save_summary:
            # Parse publication date
            pub_date = None
            if publication_date:
                try:
                    if isinstance(publication_date, str):
                        pub_date = datetime.fromisoformat(publication_date.replace('Z', '+00:00'))
                    elif isinstance(publication_date, datetime):
                        pub_date = publication_date
                except:
                    pass
            
            summary = Summary(
                user_id=user.id,
                url=url or 'API Request',
                title=title,
                author=author,
                publication_date=pub_date,
                original_text=text[:10000],  # Limit stored original text
                summary_text=summary_result['text'],
                length_setting=length,
                tone_setting=tone,
                format_setting=format_type,
                model_used=model,
                word_count=summary_result['word_count']
            )
            
            db.session.add(summary)
            summary_id = summary.id
        
        db.session.commit()
        
        # Prepare response
        response_data = {
            'summary': {
                'text': summary_result['text'],
                'word_count': summary_result['word_count'],
                'id': summary_id
            },
            'metadata': {
                'title': title,
                'author': author,
                'url': url,
                'length': length,
                'tone': tone,
                'format': format_type,
                'model': model,
                'timestamp': datetime.utcnow().isoformat()
            },
            'usage': {
                'calls_made': user.api_calls_made,
                'calls_remaining': user.api_calls_limit - user.api_calls_made
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@external_api_bp.route('/usage', methods=['GET'])
@require_api_key
def get_usage():
    """Get current API usage statistics"""
    user = request.current_user
    
    return jsonify({
        'usage': {
            'calls_made': user.api_calls_made,
            'calls_limit': user.api_calls_limit,
            'calls_remaining': user.api_calls_limit - user.api_calls_made,
            'percentage_used': (user.api_calls_made / user.api_calls_limit * 100) if user.api_calls_limit > 0 else 0
        },
        'account': {
            'email': user.email,
            'member_since': user.created_at.isoformat()
        }
    })

@external_api_bp.route('/models', methods=['GET'])
@require_api_key
def get_available_models():
    """Get list of available AI models"""
    user = request.current_user
    llm_service = LLMService(user)
    models = llm_service.get_available_models()
    
    return jsonify({
        'models': models,
        'default_model': user.default_model
    })

@external_api_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested API endpoint does not exist'
    }), 404

@external_api_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Method not allowed',
        'message': 'The HTTP method is not allowed for this endpoint'
    }), 405