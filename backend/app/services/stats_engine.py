import numpy as np
import pandas as pd
from typing import Dict, List, Any
from app.services.anomalies import detect_column_anomalies, evaluate_dataset_health

def clean_val(val: Any) -> Any:
    """Ensure value can be safely JSON serialized (replace NaN, Inf, NaT with None or string)."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (np.floating, float)):
        if np.isnan(val) or np.isinf(val):
            return None
        return round(float(val), 4)
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (pd.Timestamp, np.datetime64)):
        return str(val)
    return str(val)

def infer_column_type(series: pd.Series) -> str:
    """Infer semantic column type: numeric, datetime, categorical, boolean, or text."""
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
        
    non_null = series.dropna()
    if non_null.empty:
        return "text"
        
    # Check if string values could be mostly dates
    date_successes = 0
    sample = non_null.head(30)
    for val in sample:
        try:
            pd.to_datetime(str(val), format="mixed")
            date_successes += 1
        except Exception:
            pass
    if len(sample) > 0 and (date_successes / len(sample)) > 0.8:
        return "datetime"

    # Check if mostly convertible to numeric
    num_successes = 0
    for val in sample:
        clean_str = str(val).strip().replace("$", "").replace("€", "").replace("£", "").replace(",", "")
        try:
            float(clean_str)
            num_successes += 1
        except Exception:
            pass
    if len(sample) > 0 and (num_successes / len(sample)) > 0.8:
        return "numeric"

    # If low unique count relative to length, it's categorical
    unique_count = series.nunique()
    if unique_count <= 20 or (len(series) > 50 and unique_count / len(series) < 0.1):
        return "categorical"
        
    return "text"

def compute_column_stats(series: pd.Series, col_name: str) -> Dict[str, Any]:
    total_count = len(series)
    non_null_series = series.dropna()
    non_null_count = len(non_null_series)
    null_count = total_count - non_null_count
    null_percentage = round((null_count / total_count * 100), 2) if total_count > 0 else 0.0
    unique_count = int(series.nunique())
    
    inferred_type = infer_column_type(series)
    anomalies = detect_column_anomalies(series, col_name, inferred_type)
    
    sample_values = [clean_val(v) for v in non_null_series.head(6).tolist()]
    
    stats_dict = None
    if inferred_type == "numeric":
        num_s = pd.to_numeric(non_null_series, errors='coerce').dropna()
        if not num_s.empty:
            stats_dict = {
                "mean": clean_val(num_s.mean()),
                "std": clean_val(num_s.std()) if len(num_s) > 1 else 0.0,
                "min": clean_val(num_s.min()),
                "q25": clean_val(num_s.quantile(0.25)),
                "median": clean_val(num_s.median()),
                "q75": clean_val(num_s.quantile(0.75)),
                "max": clean_val(num_s.max()),
                "top_values": None
            }
    elif inferred_type in ["categorical", "text"]:
        top_vc = non_null_series.value_counts().head(5)
        top_list = [
            {"value": str(k), "count": int(v), "percentage": round(int(v) / non_null_count * 100, 1) if non_null_count > 0 else 0}
            for k, v in top_vc.items()
        ]
        stats_dict = {
            "mean": None,
            "std": None,
            "min": None,
            "q25": None,
            "median": None,
            "q75": None,
            "max": None,
            "top_values": top_list
        }
        
    return {
        "name": col_name,
        "dtype": str(series.dtype),
        "inferred_type": inferred_type,
        "non_null_count": non_null_count,
        "null_count": null_count,
        "null_percentage": null_percentage,
        "unique_count": unique_count,
        "sample_values": sample_values,
        "stats": stats_dict,
        "anomalies": anomalies
    }

def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    col_details = []
    col_anomalies_map = {}
    
    for col in df.columns:
        col_name = str(col)
        col_stat = compute_column_stats(df[col], col_name)
        col_details.append(col_stat)
        if col_stat["anomalies"]:
            col_anomalies_map[col_name] = col_stat["anomalies"]
            
    health_summary = evaluate_dataset_health(df, col_anomalies_map)
    
    return {
        "columns": col_details,
        "health": health_summary
    }
