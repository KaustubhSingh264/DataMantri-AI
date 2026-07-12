from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.upload_history import UploadHistory


PIPELINE_VERSION = "ml-bi-v1"


def fingerprint_bytes(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def fingerprint_file(path: Path) -> str:
    return fingerprint_bytes(path.read_bytes())


def cache_metadata(dataset_hash: str) -> Dict[str, Any]:
    return {"dataset_hash": dataset_hash, "pipeline_version": PIPELINE_VERSION}


def find_cached_analysis(db: Session, user_id: int, dataset_hash: str) -> Optional[UploadHistory]:
    records = (
        db.query(UploadHistory)
        .filter(UploadHistory.user_id == user_id)
        .order_by(UploadHistory.created_at.desc())
        .all()
    )
    for record in records:
        metadata = (record.result_json or {}).get("analysis_cache") if record.result_json else None
        if metadata and metadata.get("dataset_hash") == dataset_hash and metadata.get("pipeline_version") == PIPELINE_VERSION:
            return record
    return None
