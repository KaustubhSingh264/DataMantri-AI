"""
Centralized Language Management Service
Handles all language operations: retrieval, switching, persistence
Single point of control for i18n across the application
"""

from sqlalchemy.orm import Session
from app.models.user import User
from app.i18n.master_translations import get_translation, TRANSLATIONS

VALID_LANGUAGES = ["en", "hi", "hinglish"]
DEFAULT_LANGUAGE = "en"


class LanguageService:
    """Service for managing user language preferences and translations"""
    
    @staticmethod
    def get_user_language(user_id: int, db: Session) -> str:
        """Get user's preferred language from database"""
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.preferred_language in VALID_LANGUAGES:
            return user.preferred_language
        return DEFAULT_LANGUAGE
    
    @staticmethod
    def set_user_language(user_id: int, language: str, db: Session) -> bool:
        """Set user's preferred language in database"""
        if language not in VALID_LANGUAGES:
            return False
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.preferred_language = language
        db.commit()
        return True
    
    @staticmethod
    def get_translation(language: str, section: str, key: str, **kwargs) -> str:
        """Get translated string - wrapper around master_translations"""
        if language not in VALID_LANGUAGES:
            language = DEFAULT_LANGUAGE
        return get_translation(language, section, key, **kwargs)
    
    @staticmethod
    def get_all_translations(language: str) -> dict:
        """Get entire translation dictionary for a language"""
        if language not in VALID_LANGUAGES:
            language = DEFAULT_LANGUAGE
        return TRANSLATIONS.get(language, TRANSLATIONS[DEFAULT_LANGUAGE])
    
    @staticmethod
    def validate_language(language: str) -> bool:
        """Check if language is valid"""
        return language in VALID_LANGUAGES


# Commonly used translation groups (ready-to-use templates)
COMMON_RESPONSES = {
    "upload_success": lambda lang: get_translation(lang, "upload", "upload_success"),
    "upload_failed": lambda lang: get_translation(lang, "upload", "upload_failed"),
    "success": lambda lang: get_translation(lang, "system", "success"),
    "error": lambda lang: get_translation(lang, "system", "error"),
    "loading": lambda lang: get_translation(lang, "system", "loading"),
}
