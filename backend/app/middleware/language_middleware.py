from flask import request, g
from app.i18n import I18nService


def get_language_from_request():
    """
    Extract language from request (query parameter or Accept-Language header).
    
    Priority:
    1. ?language=en query parameter
    2. X-DataMantri-Language header
    3. Accept-Language header
    4. Default language
    """
    # Check query parameter first
    language = request.args.get('language')
    
    if not language or language not in I18nService.SUPPORTED_LANGUAGES:
        language = request.headers.get('X-DataMantri-Language')

    if not language or language not in I18nService.SUPPORTED_LANGUAGES:
        # Try to get from Accept-Language header
        accept_language = request.headers.get('Accept-Language', '')
        
        # Parse Accept-Language header (e.g., "en-US,en;q=0.9,hi;q=0.8")
        if accept_language:
            for raw_lang in accept_language.split(','):
                lang = raw_lang.split(';')[0].strip().lower()
                if lang == 'hinglish':
                    language = 'hinglish'
                    break
                primary_lang = lang.split('-')[0]
                if primary_lang in I18nService.SUPPORTED_LANGUAGES:
                    language = primary_lang
                    break
    
    # Use default if still not found
    if not language:
        language = I18nService.DEFAULT_LANGUAGE
    
    return language


def language_middleware(f):
    """
    Decorator to extract and store language in Flask's g object.
    
    Usage:
        @app.route('/api/endpoint')
        @language_middleware
        def endpoint():
            # Access language via g.language
            pass
    """
    def wrapper(*args, **kwargs):
        g.language = get_language_from_request()
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


def before_request_handler():
    """
    Register this as before_request handler to set language for all requests.
    
    Usage in main.py:
        app.before_request(before_request_handler)
    """
    g.language = get_language_from_request()
