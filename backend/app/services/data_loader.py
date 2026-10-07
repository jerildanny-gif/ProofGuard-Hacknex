import os
import uuid
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from app.config import UPLOAD_DIR, SAMPLE_DATA_DIR
from app.services.stats_engine import analyze_dataframe, clean_val
from app.models.schemas import DatasetMeta, SampleDatasetInfo

# In-memory store for loaded datasets and analysis results
# Map of dataset_id -> {"meta": DatasetMeta, "df": pd.DataFrame, "analysis": dict, "sheets": list}
DATASET_STORE: Dict[str, Dict[str, Any]] = {}

SAMPLE_METADATA: List[SampleDatasetInfo] = [
    SampleDatasetInfo(
        id="sample-sales",
        title="Global E-Commerce Sales",
        filename="global_sales_messy.csv",
        description="Features mixed currencies ($ / € / £ / ¥ / CAD / INR), duplicate order IDs, unaligned weight units (kg vs lbs), and missing discounts.",
        challenge_type="Mixed Units & Currencies",
        tags=["Currency", "Duplicates", "Missing Values", "Units"]
    ),
    SampleDatasetInfo(
        id="sample-employees",
        title="HR Employee Directory",
        filename="employee_records_messy.csv",
        description="Features ambiguous date formats (DD/MM vs MM/DD), duplicate employee records, negative salaries, and masked placeholders ('?', 'TBD').",
        challenge_type="Ambiguous Dates & Duplicates",
        tags=["Dates", "Negative Outliers", "Masked Nulls", "Duplicates"]
    ),
    SampleDatasetInfo(
        id="sample-clinical",
        title="Clinical Trial Cohorts",
        filename="healthcare_trials_messy.csv",
        description="Contains impossible values (negative age: -8, systolic blood pressure: 999 and -5), unmeasured baseline biomarkers, and duplicate patient entries.",
        challenge_type="Impossible Numbers & Trick Answers",
        tags=["Medical", "Impossible Numbers", "Missing Baseline", "Cohorts"]
    ),
    SampleDatasetInfo(
        id="sample-inventory",
        title="Multi-Warehouse Inventory Audit",
        filename="inventory_contradictions.csv",
        description="Contains contradictory stock counts for identical SKUs across systems, negative stock, and missing physical audit records.",
        challenge_type="Contradictory Records",
        tags=["Contradictions", "Discrepancies", "ERP Mismatch", "Supply Chain"]
    )
]

def load_file_to_dataframe(filepath: Path, sheet_name: Optional[str] = None) -> Tuple[pd.DataFrame, Optional[List[str]]]:
    suffix = filepath.suffix.lower()
    sheets = None
    
    if suffix == ".csv":
        encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
        df = None
        for enc in encodings:
            try:
                df = pd.read_csv(filepath, encoding=enc)
                break
            except Exception:
                continue
        if df is None:
            raise ValueError("Could not parse CSV with standard encodings.")
    elif suffix in [".xlsx", ".xls"]:
        excel_file = pd.ExcelFile(filepath)
        sheets = excel_file.sheet_names
        selected_sheet = sheet_name if sheet_name and sheet_name in sheets else sheets[0]
        df = pd.read_excel(filepath, sheet_name=selected_sheet)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")
        
    # Clean column names (strip whitespace, ensure string type)
    df.columns = [str(c).strip() for c in df.columns]
    return df, sheets

def register_dataset(df: pd.DataFrame, name: str, filename: str, is_sample: bool = False, description: Optional[str] = None, sheets: Optional[List[str]] = None, custom_id: Optional[str] = None) -> str:
    dataset_id = custom_id or str(uuid.uuid4())[:8]
    file_type = "csv" if filename.endswith(".csv") else "xlsx"
    
    meta = DatasetMeta(
        id=dataset_id,
        name=name,
        filename=filename,
        file_type=file_type,
        size_bytes=int(df.memory_usage(deep=True).sum()),
        row_count=len(df),
        column_count=len(df.columns),
        uploaded_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        is_sample=is_sample,
        description=description
    )
    
    analysis = analyze_dataframe(df)
    
    DATASET_STORE[dataset_id] = {
        "meta": meta,
        "df": df,
        "analysis": analysis,
        "sheets": sheets
    }
    
    return dataset_id

def init_sample_datasets():
    """Pre-load sample datasets into memory so users can start immediately."""
    for sample in SAMPLE_METADATA:
        if sample.id in DATASET_STORE:
            continue
        filepath = SAMPLE_DATA_DIR / sample.filename
        if filepath.exists():
            try:
                df, sheets = load_file_to_dataframe(filepath)
                register_dataset(
                    df=df,
                    name=sample.title,
                    filename=sample.filename,
                    is_sample=True,
                    description=sample.description,
                    sheets=sheets,
                    custom_id=sample.id
                )
            except Exception as e:
                print(f"Error loading sample dataset {sample.filename}: {e}")

def get_dataset(dataset_id: str) -> Optional[Dict[str, Any]]:
    if dataset_id not in DATASET_STORE:
        # Check if it is a sample dataset that wasn't initialized yet
        init_sample_datasets()
    return DATASET_STORE.get(dataset_id)

def list_all_datasets() -> List[DatasetMeta]:
    init_sample_datasets()
    return [entry["meta"] for entry in DATASET_STORE.values()]

def get_preview_data(dataset_id: str, page: int = 1, page_size: int = 25) -> Optional[Dict[str, Any]]:
    entry = get_dataset(dataset_id)
    if not entry:
        return None
        
    df = entry["df"]
    total_rows = len(df)
    total_pages = max(1, (total_rows + page_size - 1) // page_size)
    
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)
    
    subset = df.iloc[start_idx:end_idx]
    
    # Format rows as list of dicts with clean values
    rows = []
    for _, row in subset.iterrows():
        clean_row = {}
        for col in df.columns:
            clean_row[str(col)] = clean_val(row[col])
        rows.append(clean_row)
        
    return {
        "meta": entry["meta"],
        "columns": [str(c) for c in df.columns],
        "rows": rows,
        "total_rows": total_rows,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }
