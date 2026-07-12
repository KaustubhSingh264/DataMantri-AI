"""
Language Management API Routes
Endpoints for getting/setting language preferences and getting translations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.routes.auth import get_current_user, get_db
from app.models.user import User
from app.i18n.language_service import LanguageService, VALID_LANGUAGES

router = APIRouter(prefix="/api/language", tags=["language"])


@router.get("/valid")
async def get_valid_languages():
    """Get list of valid languages"""
    return {
        "languages": VALID_LANGUAGES,
        "codes": {
            "en": "English",
            "hi": "हिंदी (Hindi)",
            "hinglish": "Hinglish (Hindi + English)"
        }
    }


@router.get("/user")
async def get_user_language(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's language preference"""
    language = LanguageService.get_user_language(current_user.id, db)
    return {
        "language": language,
        "valid_languages": VALID_LANGUAGES
    }


@router.post("/user")
async def set_user_language(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set user's language preference"""
    language = data.get("language")
    
    if not language:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Language parameter required"
        )
    
    if language not in VALID_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid language. Must be one of: {VALID_LANGUAGES}"
        )
    
    if LanguageService.set_user_language(current_user.id, language, db):
        return {
            "success": True,
            "language": language,
            "message": f"Language changed to {language}"
        }
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to update language preference"
    )


@router.get("/translations/{language}")
async def get_translations(language: str):
    """Get all translations for a language"""
    if not LanguageService.validate_language(language):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid language. Must be one of: {VALID_LANGUAGES}"
        )
    
    translations = LanguageService.get_all_translations(language)
    return {
        "language": language,
        "translations": translations
    }


@router.get("/translations/{language}/{section}")
async def get_section_translations(language: str, section: str):
    """Get translations for a specific section"""
    if not LanguageService.validate_language(language):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid language. Must be one of: {VALID_LANGUAGES}"
        )
    
    all_translations = LanguageService.get_all_translations(language)
    section_translations = all_translations.get(section)
    
    if section_translations is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section '{section}' not found"
        )
    
    return {
        "language": language,
        "section": section,
        "translations": section_translations
    }
