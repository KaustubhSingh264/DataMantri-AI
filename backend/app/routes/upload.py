from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
import pandas as pd
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.database.db import SessionLocal
from app.models.user import User
from app.models.upload_history import UploadHistory
from app.services.forecast_engine import generate_forecast_chart
from app.services.qa_engine import answer_data_question
from app.services.business_logic import localize_answer
from app.services.business_advisor_engine import generate_business_advisor_report
from app.services.data_cleaner import clean_dataset
from app.services.localization_service import language_from_request, localize_analysis_payload, localize_text, normalize_language
from app.services.analytics_pipeline import (
    PipelineContext,
    SUPPORTED_EXTENSIONS,
    build_validation_report,
    log_exception,
    log_stage,
    normalize_dataframe,
    read_dataset,
    run_analysis,
)
from app.services.analysis_cache import cache_metadata, find_cached_analysis, fingerprint_bytes
from app.services.subscription_service import (
    FEATURE_CHAT,
    FEATURE_CLEAN,
    FEATURE_RECOMMENDATION,
    FEATURE_REPORT,
    FEATURE_UPLOAD,
    consume_feature,
    has_full_access,
    refresh_user_plan,
)
from app.services.auth_service import decode_token

router = APIRouter()
security = HTTPBearer()
BACKEND_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_FOLDER = BACKEND_ROOT / "data"
BASIC_INSIGHT_LIMIT = 3
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return email


def get_current_user(email: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    refresh_user_plan(user, db)
    return user


def is_premium(user: User):
    return has_full_access(user)


def require_premium(user: User):
    return True


def clean_dataframe(df: pd.DataFrame):
    cleaned = df.copy()
    original_rows = len(cleaned)
    original_columns = len(cleaned.columns)
    original_missing = int(cleaned.isna().sum().sum())
    original_duplicate_rows = int(cleaned.duplicated().sum())

    rename_map = {}
    seen_columns = set()
    for column in cleaned.columns:
        normalized = re.sub(r"[^0-9a-zA-Z]+", "_", str(column).strip().lower()).strip("_")
        normalized = normalized or "column"
        base_name = normalized
        suffix = 2
        while normalized in seen_columns:
            normalized = f"{base_name}_{suffix}"
            suffix += 1
        rename_map[column] = normalized
        seen_columns.add(normalized)
    cleaned = cleaned.rename(columns=rename_map)

    text_columns_trimmed = 0
    numeric_columns_converted = 0
    date_columns_standardized = 0
    fill_actions = {}
    outliers_removed = 0

    for column in cleaned.columns:
        if cleaned[column].dtype == "object" or pd.api.types.is_string_dtype(cleaned[column]):
            cleaned[column] = cleaned[column].apply(lambda value: value.strip() if isinstance(value, str) else value)
            text_columns_trimmed += 1

            non_null = cleaned[column].dropna()
            numeric_candidate = pd.to_numeric(
                non_null.astype(str).str.replace(",", "", regex=False).str.replace("₹", "", regex=False),
                errors="coerce",
            )
            if len(non_null) and numeric_candidate.notna().mean() >= 0.8:
                cleaned[column] = pd.to_numeric(
                    cleaned[column].astype(str).str.replace(",", "", regex=False).str.replace("₹", "", regex=False),
                    errors="coerce",
                )
                numeric_columns_converted += 1
                continue

            try:
                parsed_dates = pd.to_datetime(cleaned[column], errors="coerce", format="mixed")
            except TypeError:
                parsed_dates = pd.to_datetime(cleaned[column], errors="coerce")
            if len(non_null) and parsed_dates.notna().mean() >= 0.8:
                cleaned[column] = parsed_dates
                date_columns_standardized += 1

    cleaned = cleaned.drop_duplicates()

    numeric_columns = cleaned.select_dtypes(include=["number"]).columns.tolist()
    outlier_masks = []
    for column in numeric_columns:
        if "id" in column.lower():
            continue
        q1 = cleaned[column].quantile(0.25)
        q3 = cleaned[column].quantile(0.75)
        iqr = q3 - q1
        if pd.isna(iqr) or iqr == 0:
            continue
        lower = q1 - 3 * iqr
        upper = q3 + 3 * iqr
        mask = (cleaned[column] < lower) | (cleaned[column] > upper)
        if 0 < mask.mean() <= 0.05:
            outlier_masks.append(mask)
    if outlier_masks:
        combined_mask = outlier_masks[0]
        for mask in outlier_masks[1:]:
            combined_mask = combined_mask | mask
        outliers_removed = int(combined_mask.sum())
        cleaned = cleaned.loc[~combined_mask].copy()

    for column in cleaned.columns:
        if pd.api.types.is_numeric_dtype(cleaned[column]):
            fill_value = cleaned[column].median()
            cleaned[column] = cleaned[column].fillna(0 if pd.isna(fill_value) else fill_value)
            fill_actions[column] = "median"
        elif pd.api.types.is_datetime64_any_dtype(cleaned[column]):
            non_null_dates = cleaned[column].dropna()
            if not non_null_dates.empty:
                fill_value = non_null_dates.mode().iloc[0] if not non_null_dates.mode().empty else non_null_dates.median()
            else:
                fill_value = pd.Timestamp("1970-01-01")
            cleaned[column] = cleaned[column].fillna(fill_value)
            fill_actions[column] = "date_mode"
        else:
            mode = cleaned[column].mode(dropna=True)
            fallback = mode.iloc[0] if not mode.empty else "Unknown"
            cleaned[column] = cleaned[column].fillna(fallback)
            fill_actions[column] = "mode"

    cleaned = cleaned.convert_dtypes()
    missing_after = int(cleaned.isna().sum().sum())

    return cleaned, {
        "rows_before": original_rows,
        "rows_after": len(cleaned),
        "columns_before": original_columns,
        "columns_after": len(cleaned.columns),
        "columns_renamed": sum(1 for old, new in rename_map.items() if old != new),
        "duplicates_removed": original_duplicate_rows,
        "outliers_removed": outliers_removed,
        "missing_values_before": original_missing,
        "missing_values_after": missing_after,
        "missing_values_filled": max(0, original_missing - missing_after),
        "text_columns_trimmed": text_columns_trimmed,
        "numeric_columns_converted": numeric_columns_converted,
        "date_columns_standardized": date_columns_standardized,
        "fill_actions": fill_actions,
    }


def get_latest_upload_for_user(user: User, db: Session):
    latest = (
        db.query(UploadHistory)
        .filter(UploadHistory.user_id == user.id)
        .order_by(UploadHistory.created_at.desc())
        .first()
    )

    if not latest:
        raise HTTPException(status_code=404, detail="No uploads found")

    return latest


def delete_upload_file_if_unused(filename: str, db: Session):
    if not filename:
        return
    remaining = db.query(UploadHistory).filter(UploadHistory.filename == filename).count()
    if remaining == 0:
        file_path = UPLOAD_FOLDER / filename
        if file_path.exists():
            file_path.unlink()


def load_latest_dataframe(user: User, db: Session):
    latest = get_latest_upload_for_user(user, db)
    ctx = PipelineContext("load_latest_dataframe", upload_id=latest.id, dataset_id=latest.id, user_id=user.id)
    file_path = UPLOAD_FOLDER / latest.filename
    if not file_path.exists():
        log_stage("load_latest_dataframe:file_missing", ctx, filename=latest.filename)
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    try:
        original_name = latest.original_filename or latest.filename
        df = read_dataset(file_path, original_name, ctx)
        df, _ = normalize_dataframe(df, ctx)
    except Exception as exc:
        log_exception("load_latest_dataframe:failed", ctx, exc, filename=latest.filename)
        raise HTTPException(status_code=500, detail=f"Could not restore dataset: {exc}") from exc

    return latest, df


def make_server_filename(original_filename: str) -> str:
    suffix = Path(original_filename).suffix.lower()
    safe_stem = re.sub(r"[^0-9a-zA-Z._-]+", "_", Path(original_filename).stem).strip("._-") or "dataset"
    return f"{safe_stem}_{uuid.uuid4().hex[:12]}{suffix}"


def summarize_upload(validation_report: dict, insights: list, recommendations: list, language: str = "en") -> str:
    summary = (
        f"{validation_report.get('row_count', 0)} rows, "
        f"{validation_report.get('column_count', 0)} columns, "
        f"{len(insights)} insights, {len(recommendations)} recommendations"
    )
    return localize_text(summary, language)


def build_dataset_lifecycle(
    *,
    upload_id: int | None,
    filename: str,
    original_filename: str,
    validation_report: dict,
    analysis: dict,
    created_at: datetime | None = None,
) -> dict:
    upload_time = created_at or datetime.now(timezone.utc)
    return {
        "current_dataset": original_filename or filename,
        "filename": filename,
        "upload_id": upload_id,
        "upload_time": upload_time.isoformat(),
        "analysis_time": datetime.now(timezone.utc).isoformat(),
        "rows": validation_report.get("row_count", 0),
        "columns": validation_report.get("column_count", 0),
        "domain": (analysis.get("domain_detection") or {}).get("domain", "custom"),
        "domain_confidence": (analysis.get("domain_detection") or {}).get("confidence", 0),
        "dataset_health": (analysis.get("dataset_health") or {}).get("overall_health_score"),
        "status": analysis.get("analysis_status", "complete"),
        "models_used": analysis.get("models_used", []),
    }


class InsightItem(BaseModel):
    title: str
    detail: str
    icon: str
    confidence: float


class RecommendationItem(BaseModel):
    title: str
    detail: str
    impact: str


class HistoryItem(BaseModel):
    id: int
    filename: str
    summary: str
    created_at: str


class QARequest(BaseModel):
    question: str
    language: str | None = "en"


class QAResponse(BaseModel):
    question: str
    answer: str
    chart: str | None = None
    language: str | None = "en"


def upload_success_response(dataset_id: int, filename: str, analysis: dict, language: str = "en"):
    language = normalize_language(language)
    return JSONResponse(
        status_code=200,
        content=jsonable_encoder({
            "success": True,
            "language": language,
            "message": localize_text("Upload completed", language),
            "dataset_id": str(dataset_id),
            "filename": filename,
            "data": analysis,
            "analysis": analysis,
        }),
    )


def upload_error_response(status_code: int, error: str, details: str = "", language: str = "en"):
    language = normalize_language(language)
    localized_error = localize_text(error, language)
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({
            "success": False,
            "language": language,
            "message": localized_error,
            "error": localized_error,
            "details": localize_text(details, language),
        }),
    )


@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    language: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    consume_feature(user, db, FEATURE_UPLOAD)
    ctx = PipelineContext("upload_file", user_id=user.id)
    original_filename = file.filename or "dataset"
    effective_language = normalize_language(language or language_from_request(request, getattr(user, "preferred_language", None)))
    extension = Path(original_filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        return upload_error_response(400, "Unsupported file type", "Upload CSV, XLSX, or JSON.", effective_language)

    server_filename = make_server_filename(original_filename)
    file_path = UPLOAD_FOLDER / server_filename

    try:
        contents = await file.read()
        if not contents:
            return upload_error_response(400, "Uploaded file is empty", "Choose a non-empty CSV, XLSX, or JSON dataset.", effective_language)
        dataset_hash = fingerprint_bytes(contents)
        cached = find_cached_analysis(db, user.id, dataset_hash) if user else None
        if cached and cached.result_json:
            user.latest_upload_id = cached.id
            db.add(user)
            db.commit()
            cached_payload = {
                **localize_analysis_payload(cached.result_json, effective_language),
                "dataset_id": str(cached.id),
                "upload_id": cached.id,
                "cache_hit": True,
            }
            cached_payload["dataset_lifecycle"] = {
                **(cached_payload.get("dataset_lifecycle") or {}),
                "upload_id": cached.id,
                "status": "cached",
            }
            log_stage("upload_file:cache_hit", ctx, upload_id=cached.id, filename=cached.filename)
            return upload_success_response(cached.id, cached.filename, cached_payload, effective_language)

        file_path.write_bytes(contents)
        log_stage("upload_file:saved", ctx, filename=server_filename, original_filename=original_filename, bytes=len(contents))

        raw_df = read_dataset(file_path, original_filename, ctx)
        df, normalize_report = normalize_dataframe(raw_df, ctx)
        validation_report = build_validation_report(df, normalize_report)
        analysis = run_analysis(df, ctx, validation_report=validation_report, language=effective_language)
        lifecycle = build_dataset_lifecycle(
            upload_id=None,
            filename=server_filename,
            original_filename=original_filename,
            validation_report=validation_report,
            analysis=analysis,
        )

        if user:
            history_payload = {
                "filename": server_filename,
                "original_filename": original_filename,
                "analysis_cache": cache_metadata(dataset_hash),
                "dataset_lifecycle": lifecycle,
                **analysis,
            }

            history = UploadHistory(
                user_id=user.id,
                filename=server_filename,
                original_filename=original_filename,
                file_type=extension.lstrip("."),
                row_count=validation_report.get("row_count"),
                column_count=validation_report.get("column_count"),
                validation_report=jsonable_encoder(validation_report),
                summary=summarize_upload(validation_report, analysis["insights"], analysis["recommendations"], effective_language),
                result_json=jsonable_encoder(history_payload),
            )
            db.add(history)
            db.flush()
            ctx.upload_id = history.id
            ctx.dataset_id = history.id
            lifecycle["upload_id"] = history.id
            history_payload["dataset_lifecycle"] = lifecycle
            history.result_json = jsonable_encoder(history_payload)
            user.latest_upload_id = history.id
            db.add(user)
            db.commit()

        analysis_payload = {
            "filename": server_filename,
            "dataset_id": str(ctx.upload_id),
            "original_filename": original_filename,
            "upload_id": ctx.upload_id,
            "analysis_cache": cache_metadata(dataset_hash),
            "dataset_lifecycle": lifecycle,
            **analysis,
        }

        log_stage("upload_file:complete", ctx, filename=server_filename)
        return upload_success_response(ctx.upload_id, server_filename, analysis_payload, effective_language)
    
    except HTTPException as exc:
        return upload_error_response(exc.status_code, "Upload processing failed", str(exc.detail), effective_language)
    except Exception as e:
        log_exception("upload_file:failed", ctx, e, filename=server_filename, original_filename=original_filename)
        return upload_error_response(500, "Upload processing failed", str(e), effective_language)


@router.post("/ask", response_model=QAResponse)
async def ask_data_question(
    req: QARequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ask a question about your data and get an intelligent answer."""
    consume_feature(user, db, FEATURE_CHAT)

    try:
        latest, df = load_latest_dataframe(user, db)
        result_json = latest.result_json or {}
        profile = result_json.get("profile", {})

        effective_language = normalize_language(req.language or language_from_request(request, getattr(user, "preferred_language", None)))
        result = answer_data_question(df, profile, req.question, language=effective_language)
        answer = result.get("answer") if isinstance(result, dict) else result
        style = "hindi" if effective_language == "hi" else "hinglish" if effective_language == "hinglish" else "english"
        answer = localize_answer(answer, style)
        chart = result.get("chart") if isinstance(result, dict) else None

        user.qa_queries_used = (user.qa_queries_used or 0) + 1
        db.add(user)
        db.commit()

        return {"question": req.question, "answer": answer, "chart": chart, "language": effective_language}

    except HTTPException:
        raise
    except Exception as e:
        log_exception("ask_data_question:failed", PipelineContext("ask_data_question", user_id=user.id), e)
        language = normalize_language(req.language or language_from_request(request, getattr(user, "preferred_language", None)))
        return {"question": req.question, "answer": localize_text(f"Error processing question: {str(e)}", language), "language": language}


@router.post("/clean-data")
def clean_data(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    consume_feature(user, db, FEATURE_CLEAN)
    latest, df = load_latest_dataframe(user, db)
    ctx = PipelineContext("clean_data", upload_id=latest.id, dataset_id=latest.id, user_id=user.id)
    cleaned_df, cleaning_summary = clean_dataset(df)
    cleaning_summary.setdefault("missing_values_filled", cleaning_summary.get("missing_filled", 0))
    cleaning_summary.setdefault("date_columns_standardized", cleaning_summary.get("dates_converted", 0))
    cleaning_summary.setdefault("numeric_columns_converted", cleaning_summary.get("numeric_converted", 0))
    cleaning_summary.setdefault("columns_renamed", cleaning_summary.get("columns_renamed", 0))
    cleaning_summary.setdefault("outliers_removed", 0)
    cleaning_summary.setdefault("missing_values_after", int(cleaned_df.isna().sum().sum()))

    cleaned_filename = make_server_filename(f"cleaned_{Path(latest.original_filename or latest.filename).stem}.csv")
    cleaned_path = UPLOAD_FOLDER / cleaned_filename
    cleaned_df.to_csv(cleaned_path, index=False)

    try:
        cleaned_df, normalize_report = normalize_dataframe(cleaned_df, ctx)
        validation_report = build_validation_report(cleaned_df, normalize_report)
        effective_language = language_from_request(request, getattr(user, "preferred_language", "en"))
        analysis = run_analysis(cleaned_df, ctx, validation_report=validation_report, language=effective_language)
        lifecycle = build_dataset_lifecycle(
            upload_id=None,
            filename=cleaned_filename,
            original_filename=f"cleaned_{latest.original_filename or latest.filename}",
            validation_report=validation_report,
            analysis=analysis,
        )
    except Exception as exc:
        log_exception("clean_data:analysis_failed", ctx, exc, filename=cleaned_filename)
        raise HTTPException(status_code=500, detail=f"Could not analyze cleaned dataset: {exc}") from exc

    response_payload = {
        "filename": cleaned_filename,
        "original_filename": f"cleaned_{latest.original_filename or latest.filename}",
        **analysis,
        "dataset_lifecycle": lifecycle,
        "cleaning_summary": cleaning_summary,
    }

    history = UploadHistory(
        user_id=user.id,
        filename=cleaned_filename,
        original_filename=f"cleaned_{latest.original_filename or latest.filename}",
        file_type="csv",
        row_count=analysis["validation_report"].get("row_count"),
        column_count=analysis["validation_report"].get("column_count"),
        validation_report=jsonable_encoder(analysis["validation_report"]),
        summary=(
            localize_text(
                f"Cleaned data: removed {cleaning_summary['duplicates_removed']} duplicates, "
                f"filled {cleaning_summary['missing_values_filled']} missing values",
                effective_language,
            )
        ),
        result_json=jsonable_encoder(response_payload),
    )
    db.add(history)
    db.flush()
    lifecycle["upload_id"] = history.id
    response_payload["dataset_lifecycle"] = lifecycle
    history.result_json = jsonable_encoder(response_payload)
    user.latest_upload_id = history.id
    db.add(user)
    db.commit()

    return jsonable_encoder(response_payload)


@router.get("/clean-data/download")
def download_cleaned_data(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    consume_feature(user, db, FEATURE_REPORT)
    latest, df = load_latest_dataframe(user, db)
    cleaned_df, _ = clean_dataframe(df)
    base_name = os.path.splitext(latest.filename)[0]
    cleaned_filename = f"cleaned_{base_name}.csv"
    cleaned_path = UPLOAD_FOLDER / cleaned_filename
    cleaned_df.to_csv(cleaned_path, index=False)
    return FileResponse(
        cleaned_path,
        media_type="text/csv",
        filename=cleaned_filename,
    )


@router.get("/forecast")
def get_forecast(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    language = language_from_request(request, getattr(user, "preferred_language", "en"))
    latest, df = load_latest_dataframe(user, db)
    forecasts = latest.result_json.get("forecasts") if latest.result_json else None
    if forecasts is None:
        forecasts = generate_forecast_chart(df)
    return {"forecasts": localize_analysis_payload({"forecasts": forecasts or []}, language).get("forecasts", []), "language": language}


@router.post("/generate-report")
def generate_report(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    consume_feature(user, db, FEATURE_REPORT)
    language = language_from_request(request, getattr(user, "preferred_language", "en"))
    latest = get_latest_upload_for_user(user, db)
    result_json = localize_analysis_payload(latest.result_json or {}, language)
    return {
        "filename": latest.filename,
        "language": language,
        "report": {
            "summary": localize_text(latest.summary or "", language),
            "insights": result_json.get("insights", []),
            "recommendations": result_json.get("recommendations", []),
            "forecasts": result_json.get("forecasts", []),
            "data_quality": result_json.get("data_quality", {}),
        },
    }


@router.get("/history")
def get_history(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    language = language_from_request(request, getattr(user, "preferred_language", "en"))
    records = (
        db.query(UploadHistory)
        .filter(UploadHistory.user_id == user.id)
        .order_by(UploadHistory.created_at.desc())
        .all()
    )

    return {"language": language, "history": [
        {
            "id": record.id,
            "filename": record.filename,
            "original_filename": record.original_filename or record.filename,
            "file_type": record.file_type,
            "row_count": record.row_count,
            "column_count": record.column_count,
            "summary": localize_text(record.summary or "", language),
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
        for record in records
    ]}


@router.delete("/history/{history_id}")
def delete_history_item(history_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = (
        db.query(UploadHistory)
        .filter(UploadHistory.id == history_id, UploadHistory.user_id == user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="History record not found")

    filename = record.filename
    was_latest = user.latest_upload_id == history_id
    db.delete(record)
    db.flush()
    if was_latest:
        new_latest = (
            db.query(UploadHistory)
            .filter(UploadHistory.user_id == user.id)
            .order_by(UploadHistory.created_at.desc())
            .first()
        )
        user.latest_upload_id = new_latest.id if new_latest else None
        db.add(user)
    db.commit()
    delete_upload_file_if_unused(filename, db)
    return {"message": "History record deleted.", "id": history_id}


@router.delete("/history")
def delete_all_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.query(UploadHistory).filter(UploadHistory.user_id == user.id).all()
    filenames = [record.filename for record in records]
    deleted_count = len(records)
    for record in records:
        db.delete(record)
    user.latest_upload_id = None
    db.add(user)
    db.commit()

    for filename in filenames:
        delete_upload_file_if_unused(filename, db)

    return {"message": "All history records deleted.", "deleted": deleted_count}


@router.get("/insights")
def get_insights(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    language = language_from_request(request, getattr(user, "preferred_language", "en"))
    latest = get_latest_upload_for_user(user, db)
    result_json = localize_analysis_payload(latest.result_json or {}, language)
    insights = result_json.get("insights", [])
    if not is_premium(user):
        insights = insights[:BASIC_INSIGHT_LIMIT]

    return {"insights": insights, "language": language}


@router.get("/recommendations")
def get_recommendations(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    consume_feature(user, db, FEATURE_RECOMMENDATION)
    language = language_from_request(request, getattr(user, "preferred_language", "en"))
    latest = get_latest_upload_for_user(user, db)
    result_json = localize_analysis_payload(latest.result_json or {}, language)

    return {"recommendations": result_json.get("recommendations", []), "language": language}


@router.post("/business-advisor")
def business_advisor(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Generate a comprehensive business advisor report that combines:
    - KPI analysis
    - Data quality insights
    - Actionable recommendations
    - Forecasts and trends
    
    This is a FREE feature available to all users.
    """
    
    try:
        latest, df = load_latest_dataframe(user, db)
        language = language_from_request(request, getattr(user, "preferred_language", "en"))
        advisor_report = generate_business_advisor_report(
            df,
            analysis=latest.result_json or None,
            language=language,
        )
        
        return {
            "status": "success",
            "language": language,
            "filename": latest.filename,
            "advisory": {
                "summary": advisor_report.get("business_overview") or advisor_report.get("executive_summary", ""),
                "advisory_summary": advisor_report.get("executive_summary") or advisor_report.get("business_overview", ""),
                "kpis": advisor_report.get("kpis", {}),
                "insights": advisor_report.get("insights", []),
                "recommendations": advisor_report.get("recommendations", []),
                "forecasts": advisor_report.get("forecasts", []),
                "top_risks": advisor_report.get("top_risks", []),
                "top_opportunities": advisor_report.get("top_opportunities", []),
                "action_plan": advisor_report.get("action_plan", []),
                "top_actions": advisor_report.get("top_actions", []),
                "dataset_lifecycle": advisor_report.get("dataset_lifecycle", {}),
                "confidence": advisor_report.get("confidence"),
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        log_exception("business_advisor:failed", PipelineContext("business_advisor", user_id=user.id), e)
        return {
            "status": "error",
            "message": localize_text(f"Error generating business advisor report: {str(e)}", language_from_request(request, getattr(user, "preferred_language", "en")))
        }
