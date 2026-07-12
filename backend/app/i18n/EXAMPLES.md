"""
Example integrations showing how to use i18n in different parts of the application.
"""

# Example 1: Using i18n in routes
# In your route files (e.g., app/routes/auth.py):

from flask import jsonify, request, g
from app.i18n import I18nService
from app.middleware.language_middleware import language_middleware

# Example route with language support
def example_login_route():
    """
    @app.route('/api/auth/login', methods=['POST'])
    @language_middleware
    def login():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # Validate input
        if not email or not password:
            return I18nService.format_error_response(
                'invalid_input',
                g.language,
                400
            ), 400
        
        # Try to authenticate
        # ... authentication logic ...
        
        # If successful
        return I18nService.format_success_response(
            {'user_id': user_id, 'token': token},
            'login_success',
            g.language
        ), 200
    """
    pass


# Example 2: Using i18n in services
# In your service files:

from app.i18n import I18nService

def example_service_method():
    """
    def process_upload(file, user_id, language='en'):
        # Validate file
        if not file:
            return {
                'success': False,
                'message': I18nService.get_message('file_required', language)
            }
        
        if file.content_type != 'text/csv':
            return {
                'success': False,
                'message': I18nService.get_message('invalid_file_type', language)
            }
        
        # Process file
        # ... your logic ...
        
        return {
            'success': True,
            'message': I18nService.get_message('upload_success', language),
            'file_id': file_id
        }
    """
    pass


# Example 3: Integrating into Flask app
# In your main.py:

def setup_i18n_in_app(app):
    """
    Setup i18n in Flask app.
    
    Usage in main.py:
    
    from flask import Flask
    from app.middleware.language_middleware import before_request_handler
    
    app = Flask(__name__)
    
    # Add language middleware
    app.before_request(before_request_handler)
    
    # Now all requests will have g.language set
    """
    pass


# Example 4: Using with HTTP responses
# Common pattern for API responses:

def example_api_response():
    """
    # Success response
    response = I18nService.format_success_response(
        data={'results': data, 'count': len(data)},
        message_key='operation_successful',
        language=g.language
    )
    
    # Error response
    response = I18nService.format_error_response(
        message_key='database_error',
        language=g.language,
        status_code=500,
        details={'table': 'users', 'operation': 'query'}
    )
    """
    pass
