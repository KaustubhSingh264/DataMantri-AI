from .translations import TRANSLATIONS


class I18nService:
    """Service for handling internationalization and translation."""
    
    SUPPORTED_LANGUAGES = ["en", "hi", "hinglish"]
    DEFAULT_LANGUAGE = "en"
    
    @staticmethod
    def get_supported_languages():
        """Get list of supported languages."""
        return I18nService.SUPPORTED_LANGUAGES
    
    @staticmethod
    def get_message(key: str, language: str = "en") -> str:
        """
        Get translated message by key.
        
        Args:
            key: Translation key (e.g., 'upload_success')
            language: Language code ('en', 'hi', 'hinglish')
            
        Returns:
            Translated message or original key if not found
        """
        # Use default language if not supported
        if language not in I18nService.SUPPORTED_LANGUAGES:
            language = I18nService.DEFAULT_LANGUAGE
        
        # Get translation
        translations = TRANSLATIONS.get(language, {})
        return translations.get(key, key)
    
    @staticmethod
    def format_error_response(message_key: str, language: str = "en", 
                            status_code: int = 400, details: dict = None) -> dict:
        """
        Format error response with translation.
        
        Args:
            message_key: Translation key for error message
            language: Language code
            status_code: HTTP status code
            details: Additional error details
            
        Returns:
            Formatted error response dictionary
        """
        return {
            "status": "error",
            "code": status_code,
            "message": I18nService.get_message(message_key, language),
            "details": details or {}
        }
    
    @staticmethod
    def format_success_response(data: any, message_key: str = "success", 
                               language: str = "en") -> dict:
        """
        Format success response with translation.
        
        Args:
            data: Response data
            message_key: Translation key for success message
            language: Language code
            
        Returns:
            Formatted success response dictionary
        """
        return {
            "status": "success",
            "message": I18nService.get_message(message_key, language),
            "data": data
        }
    
    @staticmethod
    def translate_dict(dictionary: dict, language: str = "en", 
                      key_prefix: str = "") -> dict:
        """
        Translate all values in a dictionary that match translation keys.
        
        Args:
            dictionary: Dictionary to translate
            language: Language code
            key_prefix: Prefix to match for translation keys
            
        Returns:
            Dictionary with translated values
        """
        translated = {}
        for key, value in dictionary.items():
            if isinstance(value, str):
                # Try to translate
                translation_key = f"{key_prefix}{key}" if key_prefix else key
                translated[key] = I18nService.get_message(translation_key, language)
            else:
                translated[key] = value
        return translated
