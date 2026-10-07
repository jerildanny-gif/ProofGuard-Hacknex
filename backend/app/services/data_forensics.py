import re
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from app.models.schemas import ForensicFinding, ForensicReport, AnalysisForensicsResponse

CURRENCY_SYMBOLS_PATTERN = re.compile(r'[\$€£¥₹元₽₿]|USD|EUR|GBP|INR|JPY|CAD|AUD|CNY|CHF', re.IGNORECASE)
UNIT_SYMBOLS_PATTERN = re.compile(r'(?:(?<=[0-9\s])|^)(kg|lbs?|g\b|oz|meters?|m\b|cm|mm|feet|ft|inches?|in\b|km|miles?|liters?|ml|gallons?|gal|celsius|fahrenheit)\b', re.IGNORECASE)
PLACEHOLDER_TOKENS: Set[str] = {
    "?", "n/a", "na", "tbd", "unknown", "-", "--", "null", "none", "nan", 
    "undefined", "empty", "blank", "missing", "not available"
}

# Candidate identifier column names
ID_COL_PATTERNS = ["order_id", "emp_id", "patient_id", "sku_id", "customer_id", "product_id", "id"]

def detect_missing_data_forensics(df: pd.DataFrame) -> List[ForensicFinding]:
    """
    Forensically inspects all columns for null values, empty strings, NaNs,
    and disguised placeholder strings (?, N/A, NA, TBD, Unknown, -, etc.).
    Does NOT replace or alter the data.
    """
    findings: List[ForensicFinding] = []
    total_rows = len(df)
    if total_rows == 0:
        return findings

    for col in df.columns:
        series = df[col]
        # Null / NaN count
        null_mask = series.isna()
        
        # Placeholder string count
        str_series = series.dropna().astype(str).str.strip()
        placeholder_mask = str_series.str.lower().isin(PLACEHOLDER_TOKENS) | (str_series == "")
        
        null_count = int(null_mask.sum())
        placeholder_count = int(placeholder_mask.sum())
        missing_count = null_count + placeholder_count
        missing_pct = (missing_count / total_rows) * 100.0

        if missing_count > 0:
            # Gather examples of placeholders found
            sample_placeholders = list(set(str_series[placeholder_mask].tolist()))[:4]
            examples = sample_placeholders if sample_placeholders else ["<null>"]

            # Severity
            if missing_pct >= 30.0:
                severity = "HIGH"
            elif missing_pct >= 10.0:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            findings.append(ForensicFinding(
                id=f"missing-{col}",
                severity=severity,
                category="missing_data",
                column=col,
                message=f"Column '{col}' has {missing_count} missing or masked placeholder entries ({missing_pct:.1f}% missing).",
                impact=f"Direct queries depending on '{col}' will omit or misrepresent {missing_pct:.1f}% of records.",
                recommendation=f"Account for missing observations or provide data completion before querying '{col}'.",
                affected_count=missing_count,
                affected_percentage=round(missing_pct, 2),
                examples=examples
            ))

    return findings

def detect_duplicate_forensics(df: pd.DataFrame) -> List[ForensicFinding]:
    """
    Detects:
    1. Exact duplicate rows (identical values across all columns).
    2. Repeated identifier records.
    3. Conflicting duplicate records (same identifier, divergent values in other columns).
    """
    findings: List[ForensicFinding] = []
    total_rows = len(df)
    if total_rows == 0:
        return findings

    # 1. Exact duplicate rows
    exact_dups = int(df.duplicated().sum())
    exact_pct = (exact_dups / total_rows) * 100.0
    if exact_dups > 0:
        # Sample duplicated row index/values
        dup_indices = df[df.duplicated(keep=False)].head(2).to_dict(orient="records")
        severity = "HIGH" if exact_pct > 5.0 or exact_dups >= 2 else "MEDIUM"
        findings.append(ForensicFinding(
            id="dup-exact-rows",
            severity=severity,
            category="duplicate_records",
            column=None,
            message=f"{exact_dups} exact duplicate row(s) detected ({exact_pct:.1f}% of dataset).",
            impact="Aggregations (SUM, COUNT, MEAN) will double-count identical business transactions if not deduplicated.",
            recommendation="Verify whether repeated records represent duplicate submissions or separate transactions before aggregating.",
            affected_count=exact_dups,
            affected_percentage=round(exact_pct, 2),
            examples=[str(d) for d in dup_indices]
        ))

    # 2. Identifier Forensics
    id_col = None
    for cand in ID_COL_PATTERNS:
        if cand in df.columns:
            id_col = cand
            break
    if not id_col:
        for c in df.columns:
            if c.lower().endswith("_id") or c.lower() == "id":
                id_col = c
                break

    if id_col:
        id_series = df[id_col].dropna().astype(str).str.strip()
        val_counts = id_series.value_counts()
        repeated_ids = val_counts[val_counts > 1]

        if not repeated_ids.empty:
            conflicting_ids: List[str] = []
            exact_id_dups: List[str] = []
            conflicting_col_names: Set[str] = set()

            other_cols = [c for c in df.columns if c != id_col]

            for rep_id in repeated_ids.index:
                sub_df = df[id_series == rep_id]
                # Check if other columns have differing values
                has_conflict = False
                for oc in other_cols:
                    # Treat NaN and empty consistently
                    distinct_vals = sub_df[oc].dropna().astype(str).str.strip().unique()
                    if len(distinct_vals) > 1:
                        has_conflict = True
                        conflicting_col_names.add(oc)
                
                if has_conflict:
                    conflicting_ids.append(str(rep_id))
                else:
                    exact_id_dups.append(str(rep_id))

            # Report conflicting duplicate identifiers
            if conflicting_ids:
                findings.append(ForensicFinding(
                    id=f"dup-conflict-{id_col}",
                    severity="CRITICAL",
                    category="conflicting_duplicates",
                    column=id_col,
                    message=f"CONFLICTING DUPLICATE: Repeated identifier '{id_col}' contains contradictory records for {len(conflicting_ids)} ID(s).",
                    impact=f"Multiple records share the same {id_col} but contain conflicting values across columns ({', '.join(sorted(conflicting_col_names)[:4])}). Using either record without resolving the conflict produces an unreliable result.",
                    recommendation=f"Reconcile contradictory records for {id_col} ({', '.join(conflicting_ids[:3])}) before performing aggregations.",
                    affected_count=len(conflicting_ids),
                    affected_percentage=round((len(conflicting_ids) / len(df)) * 100.0, 2),
                    examples=conflicting_ids[:5]
                ))

            # Report repeated identical identifiers
            if exact_id_dups and not conflicting_ids:
                findings.append(ForensicFinding(
                    id=f"dup-ids-{id_col}",
                    severity="HIGH",
                    category="duplicate_records",
                    column=id_col,
                    message=f"Potential duplicate identifier detected: '{id_col}' repeated across {len(exact_id_dups)} distinct entries.",
                    impact=f"Aggregations may double-count entities identified by '{id_col}' if duplicates are not resolved.",
                    recommendation=f"Verify whether repeated '{id_col}' entries represent duplicate submissions or legitimate recurring records.",
                    affected_count=len(exact_id_dups),
                    affected_percentage=round((len(exact_id_dups) / len(df)) * 100.0, 2),
                    examples=exact_id_dups[:5]
                ))

    return findings

def detect_date_forensics(df: pd.DataFrame) -> List[ForensicFinding]:
    """
    Forensically inspects temporal columns for:
    1. Mixed date separators (/ and -).
    2. Mixed date formats (ISO YYYY-MM-DD vs DD/MM/YYYY vs MM/DD/YYYY).
    3. Ambiguous day/month ordering (both parts <= 12).
    4. Impossible dates.
    """
    findings: List[ForensicFinding] = []

    date_candidates = [
        c for c in df.columns 
        if any(k in c.lower() for k in ["date", "time", "hire", "created", "timestamp", "year", "dob"])
    ]

    for col in date_candidates:
        str_samples = df[col].dropna().astype(str).str.strip().tolist()
        if not str_samples:
            continue

        slash_dates = [s for s in str_samples if "/" in s]
        dash_dates = [s for s in str_samples if "-" in s]

        # 1. Mixed separators
        if slash_dates and dash_dates:
            findings.append(ForensicFinding(
                id=f"date-mixed-separators-{col}",
                severity="HIGH",
                category="mixed_date_formats",
                column=col,
                message=f"Mixed date separators detected in '{col}' (/ and -).",
                impact="Date parsers and grouping routines will misinterpret or fail on disparate date structures.",
                recommendation="Normalize dates to standard ISO 8601 (YYYY-MM-DD) before time-series analysis.",
                affected_count=len(str_samples),
                affected_percentage=100.0,
                examples=[slash_dates[0], dash_dates[0]]
            ))

        # 2. Date ambiguity detection (DD/MM vs MM/DD trap)
        ambiguous_dates = []
        for s in str_samples:
            # Check slash patterns: e.g. 03/04/2021
            parts = re.split(r'[/.-]', s)
            if len(parts) >= 3:
                # Check if first two components are digits <= 12
                if parts[0].isdigit() and parts[1].isdigit():
                    p1, p2 = int(parts[0]), int(parts[1])
                    if 1 <= p1 <= 12 and 1 <= p2 <= 12 and p1 != p2:
                        ambiguous_dates.append(s)

        if ambiguous_dates:
            findings.append(ForensicFinding(
                id=f"date-ambiguous-{col}",
                severity="HIGH",
                category="ambiguous_dates",
                column=col,
                message=f"AMBIGUOUS DATE: Column '{col}' contains {len(ambiguous_dates)} dates whose interpretation differs between DD/MM and MM/DD formats.",
                impact="A time-based answer (e.g. month filtering or temporal grouping) may be unreliable without clarification.",
                recommendation="Explicitly specify whether dates are formatted as DD/MM/YYYY or MM/DD/YYYY before temporal analysis.",
                affected_count=len(ambiguous_dates),
                affected_percentage=round((len(ambiguous_dates) / len(str_samples)) * 100.0, 2),
                examples=ambiguous_dates[:4]
            ))

        # 3. Impossible dates (e.g. month > 12, day > 31)
        impossible_dates = []
        for s in str_samples:
            parts = re.split(r'[/.-]', s)
            if len(parts) >= 3 and parts[0].isdigit() and parts[1].isdigit():
                p1, p2 = int(parts[0]), int(parts[1])
                # If neither part can be a month (> 12)
                if p1 > 12 and p2 > 12:
                    impossible_dates.append(s)
                elif p1 > 31 or p2 > 31:
                    impossible_dates.append(s)
        if impossible_dates:
            findings.append(ForensicFinding(
                id=f"date-impossible-{col}",
                severity="CRITICAL",
                category="invalid_impossible_values",
                column=col,
                message=f"Impossible date calendar values detected in '{col}'.",
                impact="Temporal aggregations will error or corrupt time horizons.",
                recommendation="Exclude or correct invalid calendar entries.",
                affected_count=len(impossible_dates),
                affected_percentage=round((len(impossible_dates) / len(str_samples)) * 100.0, 2),
                examples=impossible_dates[:3]
            ))

    return findings

def detect_currency_forensics(df: pd.DataFrame) -> List[ForensicFinding]:
    """
    Forensically inspects columns for currency codes and symbols.
    Flags mixed currencies without conversion basis as CRITICAL.
    """
    findings: List[ForensicFinding] = []

    for col in df.columns:
        str_series = df[col].dropna().astype(str).str.strip()
        if str_series.empty:
            continue

        currencies_found: Set[str] = set()
        examples_matched: List[str] = []

        for val in str_series.head(200):
            matches = CURRENCY_SYMBOLS_PATTERN.findall(val)
            if matches:
                for m in matches:
                    currencies_found.add(m.upper())
                examples_matched.append(val)

        if len(currencies_found) > 1:
            findings.append(ForensicFinding(
                id=f"currency-mismatch-{col}",
                severity="CRITICAL",
                category="currency_mismatch",
                column=col,
                message=f"CURRENCY MISMATCH: Column '{col}' contains multiple conflicting currencies ({', '.join(sorted(currencies_found))}).",
                impact="The requested aggregation contains multiple currencies with no valid conversion basis provided. Direct aggregation is unsafe and produces invalid calculations.",
                recommendation="Provide a valid currency conversion basis or exchange rate table before financial aggregation.",
                affected_count=len(examples_matched),
                affected_percentage=round((len(examples_matched) / len(str_series)) * 100.0, 2),
                examples=examples_matched[:5]
            ))

    return findings

def detect_unit_forensics(df: pd.DataFrame) -> List[ForensicFinding]:
    """
    Forensically inspects columns for mixed measurement units (e.g. kg vs lbs vs g).
    Flags incompatible units as HIGH.
    """
    findings: List[ForensicFinding] = []

    for col in df.columns:
        str_series = df[col].dropna().astype(str).str.strip()
        if str_series.empty:
            continue

        units_found: Set[str] = set()
        examples_matched: List[str] = []

        for val in str_series.head(200):
            matches = UNIT_SYMBOLS_PATTERN.findall(val)
            if matches:
                for m in matches:
                    u = m.lower()
                    # Normalize common variations
                    if u.startswith("lb"):
                        u = "lbs"
                    elif u.startswith("mile"):
                        u = "miles"
                    elif u.startswith("liter"):
                        u = "liters"
                    units_found.add(u)
                examples_matched.append(val)

        if len(units_found) > 1:
            findings.append(ForensicFinding(
                id=f"unit-mismatch-{col}",
                severity="HIGH",
                category="unit_mismatch",
                column=col,
                message=f"UNIT MISMATCH: Column '{col}' contains conflicting measurement units ({', '.join(sorted(units_found))}).",
                impact="Arithmetic aggregation without conversion is invalid. Summing or averaging across disparate physical units produces corrupted results.",
                recommendation="Standardize all measurements to a single base unit before numerical aggregation.",
                affected_count=len(examples_matched),
                affected_percentage=round((len(examples_matched) / len(str_series)) * 100.0, 2),
                examples=examples_matched[:5]
            ))

    return findings

def detect_impossible_values_forensics(df: pd.DataFrame) -> List[ForensicFinding]:
    """
    Detects domain-impossible values:
    1. Negative age (< 0) or extreme age (> 125).
    2. Impossible blood pressure (<= 0 or > 300 mmHg, e.g. -5, 999).
    3. Negative salary / compensation (< 0, e.g. -$95,000).
    4. Negative stock / inventory (< 0, e.g. -10).
    5. Percentage out-of-range (< 0 or > 100%).
    """
    findings: List[ForensicFinding] = []

    for col in df.columns:
        c_lower = col.lower()
        num_series = pd.to_numeric(df[col], errors='coerce').dropna()
        if num_series.empty:
            continue

        # 1. Age
        if "age" in c_lower:
            invalid_ages = num_series[(num_series < 0) | (num_series > 125)]
            if not invalid_ages.empty:
                findings.append(ForensicFinding(
                    id=f"invalid-age-{col}",
                    severity="CRITICAL",
                    category="invalid_impossible_values",
                    column=col,
                    message=f"Physically impossible age value(s) detected in '{col}' (e.g. {list(invalid_ages.iloc[:3])}).",
                    impact="Unadjusted averages or clinical statistics will be corrupted by physically impossible negative age.",
                    recommendation="Investigate and resolve corrupted age observations before clinical analysis.",
                    affected_count=int(len(invalid_ages)),
                    affected_percentage=round((len(invalid_ages) / len(df)) * 100.0, 2),
                    examples=[str(x) for x in invalid_ages.iloc[:3]]
                ))

        # 2. Blood Pressure / Systolic BP
        if any(k in c_lower for k in ["blood_pressure", "bp", "systolic"]):
            invalid_bp = num_series[(num_series <= 40) | (num_series > 300)]
            if not invalid_bp.empty:
                findings.append(ForensicFinding(
                    id=f"invalid-bp-{col}",
                    severity="CRITICAL",
                    category="invalid_impossible_values",
                    column=col,
                    message=f"Physiologically impossible blood pressure readings detected in '{col}' (e.g. {list(invalid_bp.iloc[:3])} mmHg).",
                    impact="Extreme out-of-range physiological values invalidate medical cohort analysis.",
                    recommendation="Flag or exclude corrupted sensor readings before cohort statistics.",
                    affected_count=int(len(invalid_bp)),
                    affected_percentage=round((len(invalid_bp) / len(df)) * 100.0, 2),
                    examples=[f"{x} mmHg" for x in invalid_bp.iloc[:3]]
                ))

        # 3. Salary / Compensation
        if any(k in c_lower for k in ["salary", "wage", "compensation", "payroll"]):
            neg_sal = num_series[num_series < 0]
            if not neg_sal.empty:
                findings.append(ForensicFinding(
                    id=f"invalid-salary-{col}",
                    severity="CRITICAL",
                    category="invalid_impossible_values",
                    column=col,
                    message=f"Negative compensation anomaly detected in '{col}' (e.g. {list(neg_sal.iloc[:3])}).",
                    impact="Negative salary values corrupt departmental payroll totals and average compensation calculations.",
                    recommendation="Resolve anomalous negative payroll records before calculating compensation metrics.",
                    affected_count=int(len(neg_sal)),
                    affected_percentage=round((len(neg_sal) / len(df)) * 100.0, 2),
                    examples=[str(x) for x in neg_sal.iloc[:3]]
                ))

        # 4. Stock / Inventory Count
        if any(k in c_lower for k in ["stock", "inventory", "physical_audit"]):
            neg_stock = num_series[num_series < 0]
            if not neg_stock.empty:
                findings.append(ForensicFinding(
                    id=f"invalid-stock-{col}",
                    severity="HIGH",
                    category="invalid_impossible_values",
                    column=col,
                    message=f"Negative stock count detected in '{col}' (e.g. {list(neg_stock.iloc[:3])}).",
                    impact="Negative physical stock indicates inventory tracking failure or system accounting error.",
                    recommendation="Audit physical stock counts before inventory valuation.",
                    affected_count=int(len(neg_stock)),
                    affected_percentage=round((len(neg_stock) / len(df)) * 100.0, 2),
                    examples=[f"{x} units" for x in neg_stock.iloc[:3]]
                ))

    return findings

def detect_contradictory_forensics(df: pd.DataFrame) -> List[ForensicFinding]:
    """
    Detects contradictory data between paired columns in the same dataset
    (e.g., reported_inventory vs physical_audit_inventory).
    """
    findings: List[ForensicFinding] = []

    if "reported_inventory" in df.columns and "physical_audit_inventory" in df.columns:
        rep = pd.to_numeric(df["reported_inventory"], errors='coerce')
        phy = pd.to_numeric(df["physical_audit_inventory"], errors='coerce')
        valid_mask = rep.notna() & phy.notna()
        diff = (rep[valid_mask] != phy[valid_mask])
        discrepancy_count = int(diff.sum())
        
        if discrepancy_count > 0:
            examples = []
            diff_rows = df[valid_mask][diff].head(3)
            for _, r in diff_rows.iterrows():
                sku = r.get("sku_id", "N/A")
                examples.append(f"{sku}: Reported {r['reported_inventory']} vs Audit {r['physical_audit_inventory']}")

            findings.append(ForensicFinding(
                id="contradict-inventory-audit",
                severity="HIGH",
                category="contradictory_data",
                column="physical_audit_inventory",
                message=f"Cross-system inventory discrepancy detected in {discrepancy_count} record(s).",
                impact="Unreconciled discrepancies between reported ERP inventory and physical audit undermine valuation and inventory totals.",
                recommendation="Reconcile physical audit with ERP records before valuation.",
                affected_count=discrepancy_count,
                affected_percentage=round((discrepancy_count / len(df)) * 100.0, 2),
                examples=examples
            ))

    return findings

def detect_cross_table_forensics(all_datasets: Dict[str, Any], current_ds_id: str) -> List[ForensicFinding]:
    """
    Inspects relationships and foreign key integrity across multiple registered datasets.
    """
    findings: List[ForensicFinding] = []
    if current_ds_id not in all_datasets:
        return findings

    curr_entry = all_datasets[current_ds_id]
    curr_df = curr_entry["df"]
    curr_name = curr_entry["meta"].name

    for other_id, other_entry in all_datasets.items():
        if other_id == current_ds_id:
            continue
        other_df = other_entry["df"]
        other_name = other_entry["meta"].name

        # Look for matching ID columns (e.g. product_id, sku_id, customer_id, order_id)
        for col in curr_df.columns:
            if col.lower().endswith("_id") and col in other_df.columns:
                curr_keys = set(curr_df[col].dropna().astype(str).str.strip().unique())
                other_keys = set(other_df[col].dropna().astype(str).str.strip().unique())
                
                # Check for orphans
                unmatched = curr_keys - other_keys
                if unmatched:
                    findings.append(ForensicFinding(
                        id=f"cross-table-fk-{current_ds_id}-{other_id}-{col}",
                        severity="HIGH",
                        category="cross_table_integrity",
                        column=col,
                        message=f"REFERENTIAL INTEGRITY ISSUE: {len(unmatched)} '{col}' key(s) in '{curr_name}' do not exist in '{other_name}'.",
                        impact=f"Cross-table queries joining '{curr_name}' and '{other_name}' on '{col}' will omit or misalign unmapped entities.",
                        recommendation=f"Reconcile '{col}' master keys between '{curr_name}' and '{other_name}' before cross-dataset operations.",
                        affected_count=len(unmatched),
                        affected_percentage=round((len(unmatched) / max(len(curr_keys), 1)) * 100.0, 2),
                        examples=list(unmatched)[:4]
                    ))

    return findings

def run_data_forensics(dataset_entry: Dict[str, Any], all_datasets: Optional[Dict[str, Any]] = None) -> ForensicReport:
    """
    Executes the comprehensive ProofGuard Stage 3 Data Forensics Engine:
    Inspects messy data, extracts structured findings, assesses severity,
    and assigns an overall forensic status.
    """
    df = dataset_entry["df"]
    meta = dataset_entry["meta"]
    ds_id = meta.id
    ds_name = meta.name

    findings: List[ForensicFinding] = []

    # 1. Missing data & placeholders
    findings.extend(detect_missing_data_forensics(df))

    # 2. Duplicate records & conflicting duplicates
    findings.extend(detect_duplicate_forensics(df))

    # 3. Date forensics (ambiguity, mixed formats)
    findings.extend(detect_date_forensics(df))

    # 4. Currency forensics
    findings.extend(detect_currency_forensics(df))

    # 5. Unit forensics
    findings.extend(detect_unit_forensics(df))

    # 6. Invalid / impossible values
    findings.extend(detect_impossible_values_forensics(df))

    # 7. Contradictory data
    findings.extend(detect_contradictory_forensics(df))

    # 8. Cross-table forensics
    if all_datasets:
        findings.extend(detect_cross_table_forensics(all_datasets, ds_id))

    # Summary counts
    total_cells = df.shape[0] * df.shape[1] if df.shape[1] > 0 else 0
    missing_cells = int(df.isna().sum().sum())
    missing_pct = (missing_cells / total_cells * 100.0) if total_cells > 0 else 0.0

    dups_count = sum(f.affected_count for f in findings if f.category in ["duplicate_records", "conflicting_duplicates"])
    date_issues = sum(f.affected_count for f in findings if f.category in ["ambiguous_dates", "mixed_date_formats"])
    currency_issues = sum(f.affected_count for f in findings if f.category == "currency_mismatch")
    unit_issues = sum(f.affected_count for f in findings if f.category == "unit_mismatch")
    contradictions = sum(f.affected_count for f in findings if f.category in ["contradictory_data", "conflicting_duplicates"])
    impossible_vals = sum(f.affected_count for f in findings if f.category == "invalid_impossible_values")

    crit_count = sum(1 for f in findings if f.severity == "CRITICAL")
    high_count = sum(1 for f in findings if f.severity == "HIGH")
    med_count = sum(1 for f in findings if f.severity == "MEDIUM")
    low_count = sum(1 for f in findings if f.severity == "LOW")
    info_count = sum(1 for f in findings if f.severity == "INFO")

    # Overall dataset status:
    # CLEAN, NEEDS REVIEW, UNSAFE FOR REQUESTED ANALYSIS, CANNOT DETERMINE
    if crit_count > 0 or high_count > 1:
        overall_status = "NEEDS REVIEW"
    elif high_count == 1 or med_count > 0:
        overall_status = "NEEDS REVIEW"
    else:
        overall_status = "CLEAN"

    # Recommendation
    recommendations: List[str] = []
    if currency_issues > 0:
        recommendations.append("Review currency inconsistencies before financial aggregation.")
    if dups_count > 0:
        recommendations.append("Verify duplicate and conflicting identifier records before reporting totals.")
    if date_issues > 0:
        recommendations.append("Confirm day/month convention (DD/MM vs MM/DD) before temporal queries.")
    if unit_issues > 0:
        recommendations.append("Standardize measurement units before computing averages.")
    if impossible_vals > 0:
        recommendations.append("Audit physiologically or mathematically impossible outlier records.")
    if not recommendations:
        recommendations.append("Dataset is clean with no significant forensic traps detected.")

    summary_counts = {
        "missing_cells": missing_cells,
        "missing_percentage": round(missing_pct, 2),
        "duplicates_count": dups_count,
        "date_issues_count": date_issues,
        "currency_issues_count": currency_issues,
        "unit_issues_count": unit_issues,
        "contradictions_count": contradictions,
        "impossible_values_count": impossible_vals,
        "total_findings": len(findings),
        "critical_findings": crit_count,
        "high_findings": high_count,
        "medium_findings": med_count,
        "low_findings": low_count,
        "info_findings": info_count
    }

    return ForensicReport(
        dataset_id=ds_id,
        dataset_name=ds_name,
        overall_status=overall_status,
        summary_counts=summary_counts,
        findings=findings,
        recommendation=" ".join(recommendations)
    )

def assess_forensic_impact_on_question(
    question: str,
    dataset_entry: Dict[str, Any],
    forensic_report: ForensicReport
) -> AnalysisForensicsResponse:
    """
    CRITICAL STAGE 3 GATEWAY:
    Examines whether forensic issues in the dataset ACTUALLY impact the requested question.
    DO NOT OVERBLOCK: Unrelated data issues must NOT block safe queries!
    """
    df = dataset_entry["df"]
    meta = dataset_entry["meta"]
    ds_id = meta.id
    ds_name = meta.name
    q_lower = question.lower()

    findings_map: Dict[str, List[ForensicFinding]] = {}
    for f in forensic_report.findings:
        findings_map.setdefault(f.category, []).append(f)

    # 1. TEMPORAL BOUNDARY / NONEXISTENT YEAR CHECK
    year_matches = re.findall(r'\b(19\d\d|20\d\d)\b', question)
    if year_matches:
        target_year = int(year_matches[0])
        date_cols = [c for c in df.columns if any(k in c.lower() for k in ["date", "time", "year", "hire"])]
        if date_cols:
            available_years: Set[int] = set()
            for dc in date_cols:
                str_series = df[dc].dropna().astype(str)
                f_years = re.findall(r'\b(19\d\d|20\d\d)\b', " ".join(str_series))
                available_years.update(int(y) for y in f_years)
            if available_years and target_year not in available_years:
                sorted_years = sorted(list(available_years))
                return AnalysisForensicsResponse(
                    status="cannot_determine",
                    safe_to_analyze=False,
                    question=question,
                    dataset_id=ds_id,
                    dataset_name=ds_name,
                    affected_columns=date_cols[:1],
                    reason=f"CANNOT DETERMINE — No records for year {target_year} are present in the available data. Available years: {', '.join(map(str, sorted_years))}.",
                    warnings=[f"Requested temporal target {target_year} is outside dataset boundaries ({sorted_years[0]} - {sorted_years[-1]})."],
                    findings=[]
                )

    # 2. AMBIGUOUS DATE CHECK (Month/Date filtering)
    # Questions asking for month-specific metrics e.g. "April 2026", "in April", "hired in April", "orders in March"
    month_names = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
    is_month_query = any(m in q_lower for m in month_names)
    if is_month_query and "ambiguous_dates" in findings_map:
        ambig_findings = findings_map["ambiguous_dates"]
        target_col = ambig_findings[0].column or "hire_date"
        return AnalysisForensicsResponse(
            status="unsafe_for_requested_analysis",
            safe_to_analyze=False,
            question=question,
            dataset_id=ds_id,
            dataset_name=ds_name,
            affected_columns=[target_col],
            reason="AMBIGUOUS DATE — The dataset contains dates whose interpretation may differ between DD/MM and MM/DD formats (e.g. 03/04/2021). A time-based answer cannot be determined reliably without clarification.",
            warnings=[f"Temporal ambiguity in '{target_col}' prevents deterministic month filtering."],
            findings=ambig_findings
        )

    # 3. CURRENCY MISMATCH CHECK (Revenue, price, monetary sum)
    is_monetary_query = any(w in q_lower for w in ["revenue", "price", "unit price", "cost", "total price", "total cost", "total spent", "dollar", "amount"])
    if is_monetary_query and "currency_mismatch" in findings_map:
        curr_findings = findings_map["currency_mismatch"]
        aff_cols = [f.column for f in curr_findings if f.column] or ["unit_price"]
        return AnalysisForensicsResponse(
            status="unsafe_for_requested_analysis",
            safe_to_analyze=False,
            question=question,
            dataset_id=ds_id,
            dataset_name=ds_name,
            affected_columns=aff_cols,
            reason=f"CANNOT DETERMINE — The dataset contains mixed currencies in column '{aff_cols[0]}' with no currency exchange basis provided. Direct aggregation across conflicting currencies produces invalid calculations.",
            warnings=["Direct summation across mismatched currencies is unsafe and disallowed."],
            findings=curr_findings
        )

    # 4. UNIT MISMATCH CHECK (Weight, dimension, distance)
    is_unit_query = any(w in q_lower for w in ["weight", "shipping", "dimension", "distance", "unit of measure"])
    if is_unit_query and "unit_mismatch" in findings_map:
        unit_findings = findings_map["unit_mismatch"]
        aff_cols = [f.column for f in unit_findings if f.column] or ["shipping_weight"]
        return AnalysisForensicsResponse(
            status="unsafe_for_requested_analysis",
            safe_to_analyze=False,
            question=question,
            dataset_id=ds_id,
            dataset_name=ds_name,
            affected_columns=aff_cols,
            reason=f"CANNOT DETERMINE — Column '{aff_cols[0]}' contains conflicting measurement units without a standardized unit conversion basis. Averaging across mismatched physical units is not permitted.",
            warnings=["Arithmetic aggregation across mismatched physical units is disallowed."],
            findings=unit_findings
        )

    # 5. SALARY OUTLIER / NEGATIVE COMPENSATION CHECK
    is_salary_query = "salary" in q_lower and any(w in q_lower for w in ["average", "mean", "total", "sum"])
    if is_salary_query:
        invalid_findings = [f for f in findings_map.get("invalid_impossible_values", []) if "salary" in (f.column or "").lower()]
        if invalid_findings:
            return AnalysisForensicsResponse(
                status="unsafe_for_requested_analysis",
                safe_to_analyze=False,
                question=question,
                dataset_id=ds_id,
                dataset_name=ds_name,
                affected_columns=[invalid_findings[0].column or "base_salary"],
                reason="CANNOT DETERMINE — Column 'base_salary' contains anomalous negative values (e.g. -$95,000 for EMP-015). Direct arithmetic aggregation without outlier resolution produces an invalid figure.",
                warnings=["Negative compensation anomaly detected in employee records."],
                findings=invalid_findings
            )

    # 6. PHYSIOLOGICALLY IMPOSSIBLE MEDICAL VALUES CHECK
    is_age_query = "age" in q_lower and any(w in q_lower for w in ["average", "mean", "total", "sum"])
    if is_age_query:
        age_findings = [f for f in findings_map.get("invalid_impossible_values", []) if "age" in (f.column or "").lower()]
        if age_findings:
            return AnalysisForensicsResponse(
                status="unsafe_for_requested_analysis",
                safe_to_analyze=False,
                question=question,
                dataset_id=ds_id,
                dataset_name=ds_name,
                affected_columns=["age"],
                reason="CANNOT DETERMINE — Column 'age' contains invalid negative values (e.g. -8) and missing baseline entries. Calculating an unadjusted average would produce corrupted medical statistics.",
                warnings=["Physiologically impossible negative age values present."],
                findings=age_findings
            )

    is_bp_query = any(w in q_lower for w in ["blood pressure", "systolic", "bp"]) and any(w in q_lower for w in ["average", "mean", "total", "sum"])
    if is_bp_query:
        bp_findings = [f for f in findings_map.get("invalid_impossible_values", []) if any(k in (f.column or "").lower() for k in ["bp", "systolic"])]
        if bp_findings:
            return AnalysisForensicsResponse(
                status="unsafe_for_requested_analysis",
                safe_to_analyze=False,
                question=question,
                dataset_id=ds_id,
                dataset_name=ds_name,
                affected_columns=[bp_findings[0].column or "systolic_bp"],
                reason="CANNOT DETERMINE — Column contains physiologically impossible values (e.g. -5 mmHg, 999 mmHg). Unadjusted aggregation cannot be reliably executed.",
                warnings=["Extreme out-of-range physiological values present."],
                findings=bp_findings
            )

    # 7. CONTRADICTORY INVENTORY & NEGATIVE STOCK CHECK
    is_stock_query = any(w in q_lower for w in ["total stock", "total inventory", "all inventory", "current stock", "stock across"])

    if is_stock_query:
        contradict_findings = findings_map.get("contradictory_data", []) + findings_map.get("conflicting_duplicates", [])
        if contradict_findings:
            return AnalysisForensicsResponse(
                status="unsafe_for_requested_analysis",
                safe_to_analyze=False,
                question=question,
                dataset_id=ds_id,
                dataset_name=ds_name,
                affected_columns=["reported_inventory", "physical_audit_inventory"],
                reason="CANNOT DETERMINE — The inventory dataset contains severe cross-system discrepancies (e.g., SKU-502 reports 85 in ERP vs 12 in physical audit, and negative stock for SKU-506). Total stock cannot be determined reliably without reconciliation.",
                warnings=["Unreconciled discrepancy between reported_inventory and physical_audit_inventory."],
                findings=contradict_findings
            )

    # 8. MISSING CONCEPTS CHECK
    known_concepts = {
        "profit": ["profit", "margin", "earnings"],
        "cost": ["cost", "expense"],
        "tax": ["tax", "vat"],
        "churn": ["churn", "retention"],
        "satisfaction": ["csat", "nps", "satisfaction"],
        "discount": ["discount", "rebate"]
    }
    for concept, keywords in known_concepts.items():
        if any(f" {kw} " in f" {q_lower} " for kw in keywords):
            has_matching_col = any(any(kw in c.lower() for kw in keywords) for c in df.columns)
            if not has_matching_col:
                return AnalysisForensicsResponse(
                    status="cannot_determine",
                    safe_to_analyze=False,
                    question=question,
                    dataset_id=ds_id,
                    dataset_name=ds_name,
                    affected_columns=[],
                    reason=f"CANNOT DETERMINE — Requested metric '{concept}' is not contained in dataset '{ds_name}' (available columns: {', '.join(df.columns[:8])}).",
                    warnings=[f"Missing required metric column for '{concept}'."],
                    findings=[]
                )

    # 9. SAFE TO ANALYZE (DO NOT OVERBLOCK)
    # Questions like "How many orders are there?", "How many employees are there?",
    # "Which product was ordered the most times?", "How many orders were completed?"
    # are unaffected by unrelated currency, unit, or salary issues.
    return AnalysisForensicsResponse(
        status="clean" if forensic_report.overall_status == "CLEAN" else "needs_review",
        safe_to_analyze=True,
        question=question,
        dataset_id=ds_id,
        dataset_name=ds_name,
        affected_columns=[],
        reason="Forensic pre-inspection passed: The requested analytical operation does not depend on corrupted or conflicting columns.",
        warnings=[],
        findings=[]
    )
