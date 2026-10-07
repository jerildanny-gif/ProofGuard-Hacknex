import re
import pandas as pd
from typing import Dict, List, Any

CURRENCY_SYMBOLS_PATTERN = re.compile(r'[\$€£¥₹元₽₿]|USD|EUR|GBP|INR|JPY|CAD|AUD', re.IGNORECASE)
UNIT_SYMBOLS_PATTERN = re.compile(r'\b(kg|lbs?|g|oz|m|cm|mm|ft|in|km|miles?|liters?|ml|gal)\b', re.IGNORECASE)

def detect_column_anomalies(series: pd.Series, col_name: str, inferred_type: str) -> List[str]:
    anomalies = []
    non_null_series = series.dropna()
    total_count = len(series)
    non_null_count = len(non_null_series)
    
    if total_count == 0:
        return ["Column is completely empty"]
    
    null_ratio = (total_count - non_null_count) / total_count
    if null_ratio > 0.5:
        anomalies.append(f"High missing rate ({null_ratio * 100:.1f}% missing)")
    elif null_ratio > 0.2:
        anomalies.append(f"Moderate missing rate ({null_ratio * 100:.1f}% missing)")
        
    # Check for string variations that look like currencies or mixed units
    if inferred_type in ["text", "categorical", "mixed"]:
        str_samples = [str(x).strip() for x in non_null_series.head(100)]
        currencies_found = set()
        for s in str_samples:
            matches = CURRENCY_SYMBOLS_PATTERN.findall(s)
            for m in matches:
                currencies_found.add(m.upper())
        if len(currencies_found) > 1:
            anomalies.append(f"Mixed currencies detected: {', '.join(sorted(currencies_found))}")
        elif len(currencies_found) == 1 and inferred_type != "numeric":
            anomalies.append(f"Contains currency symbol ({list(currencies_found)[0]}); unparsed numeric values")
            
        units_found = set()
        for s in str_samples:
            matches = UNIT_SYMBOLS_PATTERN.findall(s)
            for m in matches:
                units_found.add(m.lower())
        if len(units_found) > 1:
            anomalies.append(f"Mixed measurement units detected: {', '.join(sorted(units_found))}")

    # Check for ambiguous date formats
    if "date" in col_name.lower() or "time" in col_name.lower() or inferred_type == "datetime":
        str_samples = [str(x).strip() for x in non_null_series.head(50)]
        slash_dates = [s for s in str_samples if "/" in s]
        dash_dates = [s for s in str_samples if "-" in s]
        if slash_dates and dash_dates:
            anomalies.append("Mixed date separators detected (/ and -) indicating ambiguous date representations")
            
        # Check DD/MM vs MM/DD ambiguity
        ambiguous_parts = 0
        for s in slash_dates:
            parts = s.split("/")
            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                p1, p2 = int(parts[0]), int(parts[1])
                if 1 <= p1 <= 12 and 1 <= p2 <= 12 and p1 != p2:
                    ambiguous_parts += 1
        if ambiguous_parts > 3:
            anomalies.append("Ambiguous day/month format detected (e.g., values both <= 12)")

    # Check for numeric anomalies (negative values where suspicious)
    if inferred_type == "numeric":
        numeric_series = pd.to_numeric(non_null_series, errors='coerce').dropna()
        if not numeric_series.empty:
            if "age" in col_name.lower() and (numeric_series < 0).any():
                anomalies.append("Invalid negative age values detected")
            if ("price" in col_name.lower() or "cost" in col_name.lower() or "revenue" in col_name.lower()) and (numeric_series < 0).any():
                anomalies.append("Negative financial values detected where positive expected")
                
    # Detect placeholder strings in text
    if inferred_type in ["text", "categorical", "mixed"]:
        placeholder_tokens = {"na", "n/a", "null", "none", "unknown", "?", "-", "tbd", "undefined"}
        found_placeholders = set()
        for s in non_null_series.head(100):
            token = str(s).strip().lower()
            if token in placeholder_tokens:
                found_placeholders.add(str(s).strip())
        if found_placeholders:
            anomalies.append(f"Masked missing placeholders: {', '.join(list(found_placeholders)[:4])}")

    return anomalies

def evaluate_dataset_health(df: pd.DataFrame, col_anomalies: Dict[str, List[str]]) -> Dict[str, Any]:
    total_cells = df.shape[0] * df.shape[1] if df.shape[1] > 0 else 0
    missing_cells = int(df.isna().sum().sum())
    missing_percentage = (missing_cells / total_cells * 100) if total_cells > 0 else 0.0
    
    # Calculate duplicate rows
    duplicate_rows = int(df.duplicated().sum())
    duplicate_percentage = (duplicate_rows / len(df) * 100) if len(df) > 0 else 0.0
    
    # Aggregate issues
    issues = []
    if duplicate_rows > 0:
        issues.append({
            "category": "Duplicates",
            "severity": "critical" if duplicate_percentage > 5 else "warning",
            "message": f"{duplicate_rows} duplicate rows ({duplicate_percentage:.1f}% of dataset)"
        })
        
    if missing_percentage > 15:
        issues.append({
            "category": "Missing Data",
            "severity": "critical",
            "message": f"High cell missing rate: {missing_percentage:.1f}% of all cells are null"
        })
    elif missing_percentage > 0:
        issues.append({
            "category": "Missing Data",
            "severity": "info",
            "message": f"{missing_cells} empty cells ({missing_percentage:.1f}% missing)"
        })
        
    for col, anomalies in col_anomalies.items():
        for anom in anomalies:
            severity = "critical" if ("Mixed currencies" in anom or "Invalid negative" in anom) else "warning"
            issues.append({
                "category": f"Column: {col}",
                "severity": severity,
                "message": anom
            })
            
    # Calculate ProofGuard Data Health Score (0 to 100)
    score = 100
    score -= min(30, int(duplicate_percentage * 3))
    score -= min(30, int(missing_percentage))
    score -= min(30, len(issues) * 5)
    score = max(10, min(100, score))
    
    readiness_notes = []
    if duplicate_rows > 0:
        readiness_notes.append("ProofGuard Warning: Aggregation queries may double-count duplicate records unless deduplicated.")
    if any("Mixed currencies" in i["message"] for i in issues):
        readiness_notes.append("ProofGuard Warning: Currency conversion required before summing or comparing financial fields.")
    if any("Ambiguous day/month" in i["message"] for i in issues):
        readiness_notes.append("ProofGuard Warning: Temporal queries risk misaligned date ordering due to ambiguous DD/MM formats.")
    if not readiness_notes:
        readiness_notes.append("Dataset structure is clean and ready for Stage 2 code verification.")

    return {
        "health_score": score,
        "duplicate_rows": duplicate_rows,
        "duplicate_percentage": round(duplicate_percentage, 2),
        "total_missing_cells": missing_cells,
        "missing_cells_percentage": round(missing_percentage, 2),
        "detected_issues": issues,
        "readiness_notes": readiness_notes
    }
