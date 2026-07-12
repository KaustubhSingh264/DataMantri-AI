"""
Data Restoration API Routes
Endpoints for restoring dataset, analysis, and dashboard state after refresh
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.routes.auth import get_current_user, get_db
from app.models.user import User
from app.i18n.data_persistence_service import (
    DataPersistenceService,
    DashboardStateService
)
from app.services.localization_service import language_from_request, localize_text

router = APIRouter(prefix="/api/restore", tags=["restore"])


@router.get("/latest-dataset")
async def get_latest_dataset(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's most recent dataset and analysis.
    Called on app load to restore dashboard state.
    """
    language = language_from_request(request, current_user.preferred_language)
    dataset = DataPersistenceService.get_latest_dataset(current_user.id, db, language=language)
    
    if not dataset:
        return {
            "has_dataset": False,
            "language": language,
            "message": localize_text("No previous dataset found. Please upload a CSV.", language)
        }
    
    return {
        "has_dataset": True,
        "language": language,
        "dataset": dataset
    }


@router.get("/dataset/{upload_id}")
async def get_dataset_by_id(
    upload_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific dataset by ID"""
    language = language_from_request(request, current_user.preferred_language)
    dataset = DataPersistenceService.get_dataset_by_id(current_user.id, upload_id, db, language=language)
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )

    current_user.latest_upload_id = upload_id
    db.add(current_user)
    db.commit()
    
    return {
        "success": True,
        "language": language,
        "dataset": dataset
    }


@router.get("/upload-history")
async def get_upload_history(
    request: Request,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's upload history"""
    language = language_from_request(request, current_user.preferred_language)
    uploads = DataPersistenceService.get_all_user_datasets(
        current_user.id, db, limit=limit, language=language
    )
    
    return {
        "uploads": uploads,
        "count": len(uploads),
        "language": language,
    }


@router.get("/dashboard-state")
async def get_dashboard_state(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's dashboard state"""
    state = DashboardStateService.get_dashboard_state(current_user.id, db)
    
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard state not found"
        )
    
    return {
        "success": True,
        "language": language_from_request(request, current_user.preferred_language),
        "state": state
    }


@router.delete("/dataset/{upload_id}")
async def delete_dataset(
    upload_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a dataset (user must own it)"""
    if DataPersistenceService.delete_user_dataset(current_user.id, upload_id, db):
        return {
            "success": True,
            "message": "Dataset deleted successfully"
        }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Dataset not found"
    )
