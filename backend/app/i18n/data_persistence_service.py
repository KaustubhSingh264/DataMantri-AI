"""
Data Persistence Service
Handles restoration of datasets, analyses, and dashboard state
Ensures data survives page refreshes and logout/login cycles
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.user import User
from app.models.upload_history import UploadHistory
from app.services.localization_service import localize_analysis_payload, localize_text, normalize_language


class DataPersistenceService:
    """Service for managing data persistence and restoration"""
    
    @staticmethod
    def get_latest_dataset(user_id: int, db: Session, language: str = "en") -> Optional[Dict[str, Any]]:
        """
        Get the user's most recent uploaded dataset
        Returns both the analysis results and metadata
        """
        user = db.query(User).filter(User.id == user_id).first()
        latest = None
        if user and user.latest_upload_id:
            latest = db.query(UploadHistory).filter(
                UploadHistory.id == user.latest_upload_id,
                UploadHistory.user_id == user_id
            ).first()
        if not latest:
            latest = db.query(UploadHistory).filter(
                UploadHistory.user_id == user_id
            ).order_by(
                UploadHistory.created_at.desc()
            ).first()
        
        if not latest:
            return None
        language = normalize_language(language)
        analysis = localize_analysis_payload(latest.result_json or {}, language)
        
        return {
            "upload_id": latest.id,
            "filename": latest.filename,
            "original_filename": latest.original_filename or latest.filename,
            "file_type": latest.file_type,
            "row_count": latest.row_count,
            "column_count": latest.column_count,
            "validation_report": latest.validation_report,
            "summary": localize_text(latest.summary or "", language),
            "created_at": latest.created_at.isoformat() if latest.created_at else None,
            "analysis_time": ((latest.result_json or {}).get("dataset_lifecycle") or {}).get("analysis_time"),
            "dataset_lifecycle": analysis.get("dataset_lifecycle"),
            "analysis": analysis,  # Full analysis data
        }
    
    @staticmethod
    def get_dataset_by_id(user_id: int, upload_id: int, db: Session, language: str = "en") -> Optional[Dict[str, Any]]:
        """Get specific dataset by ID (if user owns it)"""
        upload = db.query(UploadHistory).filter(
            UploadHistory.id == upload_id,
            UploadHistory.user_id == user_id
        ).first()
        
        if not upload:
            return None
        language = normalize_language(language)
        analysis = localize_analysis_payload(upload.result_json or {}, language)
        
        return {
            "upload_id": upload.id,
            "filename": upload.filename,
            "original_filename": upload.original_filename or upload.filename,
            "file_type": upload.file_type,
            "row_count": upload.row_count,
            "column_count": upload.column_count,
            "validation_report": upload.validation_report,
            "summary": localize_text(upload.summary or "", language),
            "created_at": upload.created_at.isoformat() if upload.created_at else None,
            "analysis_time": ((upload.result_json or {}).get("dataset_lifecycle") or {}).get("analysis_time"),
            "dataset_lifecycle": analysis.get("dataset_lifecycle"),
            "analysis": analysis,
        }
    
    @staticmethod
    def get_all_user_datasets(user_id: int, db: Session, limit: int = 10, language: str = "en") -> list:
        """Get user's upload history (limited for dashboard display)"""
        uploads = db.query(UploadHistory).filter(
            UploadHistory.user_id == user_id
        ).order_by(
            UploadHistory.created_at.desc()
        ).limit(limit).all()
        
        language = normalize_language(language)
        return [
            {
                "upload_id": u.id,
                "filename": u.filename,
                "original_filename": u.original_filename or u.filename,
                "file_type": u.file_type,
                "row_count": u.row_count,
                "column_count": u.column_count,
                "summary": localize_text(u.summary or "", language),
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "analysis_time": ((u.result_json or {}).get("dataset_lifecycle") or {}).get("analysis_time"),
                "dataset_lifecycle": (u.result_json or {}).get("dataset_lifecycle"),
            }
            for u in uploads
        ]
    
    @staticmethod
    def save_dataset_analysis(
        user_id: int,
        filename: str,
        summary: str,
        analysis_data: Dict[str, Any],
        db: Session
    ) -> int:
        """
        Save uploaded dataset and analysis results to database
        Returns the upload_id for future reference
        """
        upload = UploadHistory(
            user_id=user_id,
            filename=filename,
            original_filename=analysis_data.get("original_filename") if isinstance(analysis_data, dict) else filename,
            file_type=analysis_data.get("file_type") if isinstance(analysis_data, dict) else None,
            row_count=(analysis_data.get("validation_report") or {}).get("row_count") if isinstance(analysis_data, dict) else None,
            column_count=(analysis_data.get("validation_report") or {}).get("column_count") if isinstance(analysis_data, dict) else None,
            validation_report=analysis_data.get("validation_report") if isinstance(analysis_data, dict) else None,
            summary=summary,
            result_json=analysis_data
        )
        db.add(upload)
        db.flush()  # Get the ID before commit
        upload_id = upload.id
        
        # Update user's latest_upload_id for quick access
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.latest_upload_id = upload_id
        
        db.commit()
        return upload_id
    
    @staticmethod
    def delete_user_dataset(user_id: int, upload_id: int, db: Session) -> bool:
        """Delete a specific dataset (user must own it)"""
        upload = db.query(UploadHistory).filter(
            UploadHistory.id == upload_id,
            UploadHistory.user_id == user_id
        ).first()
        
        if not upload:
            return False
        
        db.delete(upload)
        
        # Reset latest_upload_id if we deleted the latest
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.latest_upload_id == upload_id:
            new_latest = db.query(UploadHistory).filter(
                UploadHistory.user_id == user_id
            ).order_by(UploadHistory.created_at.desc()).first()
            user.latest_upload_id = new_latest.id if new_latest else None
        
        db.commit()
        return True


class DashboardStateService:
    """Service for managing and restoring dashboard UI state"""
    
    # This would store user preferences for:
    # - Active tab/page
    # - Chart filters
    # - Mode selection
    # - Custom dashboard settings
    
    @staticmethod
    def get_dashboard_state(user_id: int, db: Session) -> Dict[str, Any]:
        """
        Get user's last dashboard state (currently basic implementation)
        Can be extended to store in database if needed
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        return {
            "user_id": user_id,
            "language": user.preferred_language,
            "latest_upload_id": user.latest_upload_id,
        }
    
    @staticmethod
    def save_dashboard_state(user_id: int, state: Dict[str, Any], db: Session) -> bool:
        """Save dashboard state preferences"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Currently updates are minimal - mostly handled via User model
        db.commit()
        return True
