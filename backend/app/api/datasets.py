import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from app.config import UPLOAD_DIR, ALLOWED_EXTENSIONS
from app.services.data_loader import (
    register_dataset,
    get_dataset,
    list_all_datasets,
    get_preview_data,
    load_file_to_dataframe,
    SAMPLE_METADATA,
    init_sample_datasets,
    DATASET_STORE
)
from app.models.schemas import (
    DatasetMeta,
    DatasetDetailResponse,
    DatasetPreviewResponse,
    SampleDatasetInfo,
    ForensicReport
)
from app.services.data_forensics import run_data_forensics


router = APIRouter(prefix="/datasets", tags=["datasets"])

@router.get("/samples", response_model=List[SampleDatasetInfo])
async def get_sample_datasets():
    """Return catalog of built-in messy datasets showcasing specific data issues."""
    return SAMPLE_METADATA

@router.get("", response_model=List[DatasetMeta])
async def get_datasets():
    """List all registered datasets in the session."""
    return list_all_datasets()

@router.post("/upload", response_model=DatasetDetailResponse)
async def upload_dataset(file: UploadFile = File(...)):
    """Upload a CSV or Excel dataset, analyze quality, and calculate statistics."""
    filename = file.filename or "unknown.csv"
    suffix = Path(filename).suffix.lower()
    
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{suffix}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
        
    save_path = UPLOAD_DIR / filename
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
    try:
        df, sheets = load_file_to_dataframe(save_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
        
    dataset_name = Path(filename).stem.replace("_", " ").title()
    dataset_id = register_dataset(
        df=df,
        name=dataset_name,
        filename=filename,
        is_sample=False,
        sheets=sheets
    )
    
    entry = get_dataset(dataset_id)
    return DatasetDetailResponse(
        meta=entry["meta"],
        columns=entry["analysis"]["columns"],
        health=entry["analysis"]["health"],
        sheets=entry["sheets"]
    )

@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
async def get_dataset_details(dataset_id: str):
    """Retrieve full column statistics and data health assessment for a dataset."""
    entry = get_dataset(dataset_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    return DatasetDetailResponse(
        meta=entry["meta"],
        columns=entry["analysis"]["columns"],
        health=entry["analysis"]["health"],
        sheets=entry["sheets"]
    )

@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
async def get_preview(
    dataset_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=5, le=100)
):
    """Paginated preview rows for table visualization."""
    preview = get_preview_data(dataset_id, page=page, page_size=page_size)
    if not preview:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    return DatasetPreviewResponse(**preview)

@router.get("/{dataset_id}/forensics", response_model=ForensicReport)
async def get_dataset_forensics(dataset_id: str):
    """
    Stage 3 Data Forensics Engine:
    Examines messy data, detects missing placeholders, duplicates, conflicting records,
    currency/unit mismatches, ambiguous dates, impossible values, and referential integrity.
    """
    entry = get_dataset(dataset_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    report = run_data_forensics(entry, all_datasets=DATASET_STORE)
    return report

