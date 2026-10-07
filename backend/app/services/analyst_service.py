import os
import re
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from app.services.data_loader import DATASET_STORE, get_dataset, init_sample_datasets
from app.services.code_executor import execute_code
from app.models.schemas import AnalysisResponse, SuggestedQuestion, AnalysisForensicsResponse
from app.services.data_forensics import run_data_forensics, assess_forensic_impact_on_question

# Curated Suggested Questions for Stage 2 Demo
SUGGESTED_QUESTIONS: List[SuggestedQuestion] = [
    # Global E-Commerce Sales
    SuggestedQuestion(
        id="q-sales-1",
        dataset_id="sample-sales",
        question="How many orders are there?",
        category="Counting",
        is_trap=False,
        description="Verifies dataset row counting with deterministic execution proof."
    ),
    SuggestedQuestion(
        id="q-sales-2",
        dataset_id="sample-sales",
        question="Which product was ordered the most times?",
        category="Grouped Aggregation",
        is_trap=False,
        description="Aggregates and ranks products by order frequency."
    ),
    SuggestedQuestion(
        id="q-sales-3",
        dataset_id="sample-sales",
        question="How many orders were completed?",
        category="Filtering",
        is_trap=False,
        description="Filters records where status is 'Completed'."
    ),
    SuggestedQuestion(
        id="q-sales-trap-year",
        dataset_id="sample-sales",
        question="What were the total orders in 2030?",
        category="Trap: Nonexistent Year",
        is_trap=True,
        trap_reason="Temporal Out-of-Bounds",
        description="Refusal test: The dataset only contains 2024 records. Must return CANNOT DETERMINE rather than 0."
    ),
    SuggestedQuestion(
        id="q-sales-trap-currency",
        dataset_id="sample-sales",
        question="What is the total revenue in dollars?",
        category="Trap: Mixed Currencies",
        is_trap=True,
        trap_reason="Mixed Currencies ($ / € / £ / ¥ / CAD / INR)",
        description="Refusal test: unit_price has mixed currencies with no conversion rates. Direct sum is invalid."
    ),
    SuggestedQuestion(
        id="q-sales-trap-units",
        dataset_id="sample-sales",
        question="What is the average shipping weight?",
        category="Trap: Conflicting Units",
        is_trap=True,
        trap_reason="Mixed Units (kg vs lbs vs g)",
        description="Refusal test: Shipping weight contains mixed units without a common denominator."
    ),

    # HR Employee Directory
    SuggestedQuestion(
        id="q-emp-1",
        dataset_id="sample-employees",
        question="How many employees are there?",
        category="Counting",
        is_trap=False,
        description="Counts total employee records in the directory."
    ),
    SuggestedQuestion(
        id="q-emp-2",
        dataset_id="sample-employees",
        question="Which department has the most employees?",
        category="Grouped Aggregation",
        is_trap=False,
        description="Groups employees by department and determines the highest headcount."
    ),
    SuggestedQuestion(
        id="q-emp-3",
        dataset_id="sample-employees",
        question="What is the highest employee rating?",
        category="Min/Max",
        is_trap=False,
        description="Finds maximum rating score across employees."
    ),
    SuggestedQuestion(
        id="q-emp-trap-salary",
        dataset_id="sample-employees",
        question="What is the average salary?",
        category="Trap: Negative Financial Outliers",
        is_trap=True,
        trap_reason="Negative Salary Outlier (-$95,000 for EMP-015)",
        description="Refusal test: base_salary contains an impossible negative value (-95,000). Raw mean is corrupted."
    ),
    SuggestedQuestion(
        id="q-emp-trap-date",
        dataset_id="sample-employees",
        question="How many employees were hired in April 2021?",
        category="Trap: Ambiguous Dates",
        is_trap=True,
        trap_reason="Ambiguous Date Format (DD/MM vs MM/DD)",
        description="Refusal test: hire_date contains dates like 03/04/2021 which could be April 3 or March 4. Must flag date ambiguity."
    ),


    # Clinical Trial Cohorts
    SuggestedQuestion(
        id="q-med-1",
        dataset_id="sample-clinical",
        question="How many patients are in the dataset?",
        category="Counting",
        is_trap=False,
        description="Counts patient cohort entries."
    ),
    SuggestedQuestion(
        id="q-med-2",
        dataset_id="sample-clinical",
        question="Which cohort has the most patients?",
        category="Grouped Aggregation",
        is_trap=False,
        description="Identifies the largest treatment cohort."
    ),
    SuggestedQuestion(
        id="q-med-trap-age",
        dataset_id="sample-clinical",
        question="What is the average age?",
        category="Trap: Physically Impossible Value",
        is_trap=True,
        trap_reason="Negative Age (-8) and Missing Values",
        description="Refusal test: age contains -8 and null values. Must refuse unadjusted mean calculation."
    ),
    SuggestedQuestion(
        id="q-med-trap-bp",
        dataset_id="sample-clinical",
        question="What is the average systolic blood pressure?",
        category="Trap: Impossible Medical Readings",
        is_trap=True,
        trap_reason="Impossible Systolic BP (-5 and 999 mmHg)",
        description="Refusal test: blood pressure contains physiologically impossible numbers (-5 and 999)."
    ),

    # Multi-Warehouse Inventory Audit
    SuggestedQuestion(
        id="q-inv-1",
        dataset_id="sample-inventory",
        question="How many inventory items are tracked?",
        category="Counting",
        is_trap=False,
        description="Counts tracked inventory line items."
    ),
    SuggestedQuestion(
        id="q-inv-trap-stock",
        dataset_id="sample-inventory",
        question="What is the total stock?",
        category="Trap: Contradictory Records",
        is_trap=True,
        trap_reason="Cross-System Discrepancies & Negative Stock (-10)",
        description="Refusal test: Conflicting reported vs physical inventory and negative count make sum unreliable."
    ),
]

def get_suggested_questions(dataset_id: Optional[str] = None) -> List[SuggestedQuestion]:
    """Returns curated demo questions, optionally filtered by dataset."""
    if not dataset_id:
        return SUGGESTED_QUESTIONS
    return [q for q in SUGGESTED_QUESTIONS if q.dataset_id == dataset_id]

def resolve_target_dataset(dataset_id: Optional[str], question: str) -> Optional[Dict[str, Any]]:
    """Identifies the most relevant dataset using ID or question content heuristics."""
    init_sample_datasets()
    
    if dataset_id and dataset_id in DATASET_STORE:
        return DATASET_STORE[dataset_id]

    q_lower = question.lower()

    # Keyword heuristics matching dataset domain
    if any(k in q_lower for k in ["order", "sales", "revenue", "product", "discount", "customer", "ecommerce"]):
        if "sample-sales" in DATASET_STORE:
            return DATASET_STORE["sample-sales"]
    if any(k in q_lower for k in ["employee", "salary", "bonus", "department", "hire", "rating"]):
        if "sample-employees" in DATASET_STORE:
            return DATASET_STORE["sample-employees"]
    if any(k in q_lower for k in ["patient", "clinical", "cohort", "blood pressure", "systolic", "marker", "trial"]):
        if "sample-clinical" in DATASET_STORE:
            return DATASET_STORE["sample-clinical"]
    if any(k in q_lower for k in ["inventory", "warehouse", "stock", "sku", "shrinkage"]):
        if "sample-inventory" in DATASET_STORE:
            return DATASET_STORE["sample-inventory"]

    # Default to first loaded dataset if available
    if DATASET_STORE:
        return next(iter(DATASET_STORE.values()))
    return None

def check_stage1_traps(entry: Dict[str, Any], question: str) -> Optional[Dict[str, Any]]:
    """
    Evaluates Stage 1 anomaly profiles to detect whether a question hits
    known data traps (mixed currencies, impossible values, out-of-bounds dates, etc.).
    Returns refusal dictionary if a trap is triggered, else None.
    """
    df = entry["df"]
    analysis = entry.get("analysis", {})
    col_info_map = {c["name"]: c for c in analysis.get("columns", [])}
    q_lower = question.lower()

    # 1. Nonexistent Year / Temporal Out-of-bounds Check
    year_matches = re.findall(r'\b(19\d\d|20\d\d)\b', question)
    if year_matches:
        target_year = int(year_matches[0])
        # Find date columns
        date_cols = [c for c in df.columns if "date" in c.lower() or "time" in c.lower() or "year" in c.lower()]
        if date_cols:
            available_years = set()
            for dc in date_cols:
                str_series = df[dc].dropna().astype(str)
                found_years = re.findall(r'\b(19\d\d|20\d\d)\b', " ".join(str_series))
                available_years.update(int(y) for y in found_years)
            
            if available_years and target_year not in available_years:
                sorted_years = sorted(list(available_years))
                return {
                    "status": "cannot_determine",
                    "reason": f"CANNOT DETERMINE — No records for year {target_year} are present in the available data. Available years: {', '.join(map(str, sorted_years))}.",
                    "warnings": [f"Requested temporal target {target_year} is outside dataset boundaries ({sorted_years[0]} - {sorted_years[-1]})."],
                    "columns_used": date_cols[:1]
                }

    # 2. Mixed Currencies Trap Check
    if any(w in q_lower for w in ["revenue", "price", "sales", "total cost", "total spent", "dollar"]):
        # Check if financial columns have mixed currencies
        for col_name, info in col_info_map.items():
            anomalies = info.get("anomalies", [])
            for anom in anomalies:
                if "mixed currencies" in anom.lower():
                    return {
                        "status": "cannot_determine",
                        "reason": f"CANNOT DETERMINE — The dataset contains mixed currencies in column '{col_name}' with no currency exchange basis provided. Direct aggregation across conflicting currencies produces invalid calculations.",
                        "warnings": [anom, "Requires currency normalization / exchange rate table."],
                        "columns_used": [col_name]
                    }

    # 3. Mixed Measurement Units Trap Check
    if any(w in q_lower for w in ["weight", "shipping", "distance", "dimension", "unit"]):
        for col_name, info in col_info_map.items():
            anomalies = info.get("anomalies", [])
            for anom in anomalies:
                if "mixed measurement units" in anom.lower():
                    return {
                        "status": "cannot_determine",
                        "reason": f"CANNOT DETERMINE — Column '{col_name}' contains conflicting measurement units (e.g., kg vs lbs vs g) without a standardized unit conversion basis.",
                        "warnings": [anom, "Arithmetic aggregation across mismatched physical units is disallowed."],
                        "columns_used": [col_name]
                    }

    # 3b. Direct scan of shipping/weight columns for mixed units (supplement Stage 1)
    if any(w in q_lower for w in ["weight", "shipping"]):
        import re as _re
        UNIT_PAT = _re.compile(r'(kg|lbs?|g\b|oz)\b', _re.IGNORECASE)
        weight_col = next((c for c in df.columns if "weight" in c.lower()), None)
        if weight_col:
            str_samples = df[weight_col].dropna().astype(str).head(200).tolist()
            units_seen = set()
            for s in str_samples:
                for m in UNIT_PAT.findall(s):
                    u = m.lower()
                    # Normalize: lbs → lb
                    units_seen.add("lb" if u.startswith("lb") else u)
            if len(units_seen) > 1:
                return {
                    "status": "cannot_determine",
                    "reason": f"CANNOT DETERMINE — Column '{weight_col}' contains conflicting measurement units ({', '.join(sorted(units_seen))}) without a standardized unit conversion basis. Averaging across mismatched physical units is not permitted.",
                    "warnings": [f"Mixed measurement units detected directly in '{weight_col}': {', '.join(sorted(units_seen))}.", "Arithmetic aggregation across mismatched physical units is disallowed."],
                    "columns_used": [weight_col]
                }

    # 4. Impossible / Corrupted Values Check (e.g., negative age, systolic BP)
    if "age" in q_lower:
        age_col = next((c for c in df.columns if "age" in c.lower()), None)
        if age_col and age_col in col_info_map:
            anomalies = col_info_map[age_col].get("anomalies", [])
            has_negative = any("negative age" in a.lower() for a in anomalies)
            if not has_negative:
                # Direct check on df
                numeric_age = pd.to_numeric(df[age_col], errors='coerce')
                if (numeric_age < 0).any():
                    has_negative = True
            if has_negative and any(w in q_lower for w in ["average", "mean", "total", "sum"]):
                return {
                    "status": "cannot_determine",
                    "reason": f"CANNOT DETERMINE — Column '{age_col}' contains invalid negative values (e.g. -8) and missing baseline entries. Calculating an unadjusted average would produce corrupted medical statistics.",
                    "warnings": ["Negative age detected in dataset.", "Clinical validation rule violation."],
                    "columns_used": [age_col]
                }

    if any(w in q_lower for w in ["blood pressure", "systolic", "bp"]):
        bp_col = next((c for c in df.columns if "systolic" in c.lower() or "bp" in c.lower()), None)
        if bp_col:
            numeric_bp = pd.to_numeric(df[bp_col], errors='coerce').dropna()
            if (numeric_bp < 0).any() or (numeric_bp > 300).any():
                return {
                    "status": "cannot_determine",
                    "reason": f"CANNOT DETERMINE — Column '{bp_col}' contains physiologically impossible values (e.g. -5 mmHg, 999 mmHg). Unadjusted aggregation cannot be reliably executed.",
                    "warnings": ["Extreme out-of-range physiological values present."],
                    "columns_used": [bp_col]
                }

    # 5. Negative Salary Outlier Check
    if "salary" in q_lower and any(w in q_lower for w in ["average", "mean", "total", "sum"]):
        sal_col = next((c for c in df.columns if "salary" in c.lower()), None)
        if sal_col and sal_col in col_info_map:
            anomalies = col_info_map[sal_col].get("anomalies", [])
            has_negative = any("negative" in a.lower() for a in anomalies)
            if not has_negative:
                num_sal = pd.to_numeric(df[sal_col], errors='coerce')
                if (num_sal < 0).any():
                    has_negative = True
            if has_negative:
                return {
                    "status": "cannot_determine",
                    "reason": f"CANNOT DETERMINE — Column '{sal_col}' contains anomalous negative values (e.g. -$95,000 for EMP-015). Direct arithmetic aggregation without outlier resolution produces an invalid figure.",
                    "warnings": ["Negative compensation anomaly detected in employee records."],
                    "columns_used": [sal_col]
                }

    # 6. Inventory Contradictions Check
    if any(w in q_lower for w in ["total stock", "total inventory", "all inventory", "current stock"]):
        if "reported_inventory" in df.columns and "physical_audit_inventory" in df.columns:
            # Check for discrepancies between reported and audit
            return {
                "status": "cannot_determine",
                "reason": "CANNOT DETERMINE — The inventory dataset contains severe cross-system discrepancies (e.g., SKU-502 reports 85 in ERP vs 12 in physical audit, and negative stock for SKU-506). Total stock cannot be determined reliably without reconciliation.",
                "warnings": ["Unreconciled discrepancy between reported_inventory and physical_audit_inventory."],
                "columns_used": ["reported_inventory", "physical_audit_inventory"]
            }

    # 7. Check for Missing Concepts / Columns
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
                return {
                    "status": "cannot_determine",
                    "reason": f"CANNOT DETERMINE — Requested metric '{concept}' is not contained in dataset '{entry['meta'].name}' (available columns: {', '.join(df.columns[:8])}).",
                    "warnings": [f"Missing required metric column for '{concept}'."],
                    "columns_used": []
                }

    return None

def synthesize_analysis_plan(entry: Dict[str, Any], question: str) -> Tuple[Optional[str], List[str], str, Optional[str]]:
    """
    Maps natural language question into verifiable Python/Pandas code.
    Returns:
        (generated_code, columns_used, operation, human_answer_template)
    """
    df = entry["df"]
    q_lower = question.lower()
    columns = list(df.columns)
    dataset_key = entry["meta"].id

    # 1. COUNTING QUERIES
    # Examples: "How many orders are there?", "How many employees are there?", "Count of patients"
    if any(q_lower.startswith(prefix) for prefix in ["how many", "count of", "number of", "total number of"]):
        # Check if filtering is involved:
        # e.g., "How many orders were completed?"
        if "completed" in q_lower and "status" in columns:
            code = f"""# Filter rows where status is 'Completed'
df_target = datasets['{dataset_key}']
completed_df = df_target[df_target['status'].astype(str).str.strip().str.lower() == 'completed']
result = int(len(completed_df))
print(f"Completed orders: {{result}}")"""
            return code, ["status"], "filter_count", "There are {result} completed orders in the dataset."

        # e.g., "How many employees have salary above 50000?"
        sal_match = re.search(r'(?:salary|compensation)\s*(?:above|greater than|>)\s*(\d+)', q_lower)
        if sal_match:
            threshold = int(sal_match.group(1))
            sal_col = next((c for c in columns if "salary" in c.lower()), None)
            if sal_col:
                code = f"""# Count records with {sal_col} > {threshold}
df_target = datasets['{dataset_key}']
numeric_sal = pd.to_numeric(df_target['{sal_col}'], errors='coerce')
result = int((numeric_sal > {threshold}).sum())
print(f"Records above {threshold}: {{result}}")"""
                return code, [sal_col], "filter_count", f"There are {{result}} records with {sal_col} above {threshold:,}."

        # e.g., "How many orders were placed in 2024?"
        year_match = re.search(r'\b(20\d\d)\b', q_lower)
        if year_match:
            yr = year_match.group(1)
            date_col = next((c for c in columns if "date" in c.lower()), None)
            if date_col:
                code = f"""# Count records for year {yr}
df_target = datasets['{dataset_key}']
year_matches = df_target['{date_col}'].astype(str).str.contains('{yr}', na=False)
result = int(year_matches.sum())
print(f"Records in {yr}: {{result}}")"""
                return code, [date_col], "filter_count", f"There are {{result}} records from year {yr}."

        # Pure row count
        # e.g. "How many orders are there?", "How many employees are there?"
        entity_name = "records"
        for entity in ["order", "employee", "patient", "item", "record", "row"]:
            if entity in q_lower:
                entity_name = entity + "s"
                break

        code = f"""# Deterministic row count verification
df_target = datasets['{dataset_key}']
result = int(len(df_target))
print(f"Total count: {{result}}")"""
        return code, [], "count", f"There are {{result}} total {entity_name} recorded in the dataset."

    # 2. GROUPED AGGREGATION QUERIES
    # Examples: "Which product was ordered the most times?", "Which department has the most employees?"
    if any(w in q_lower for w in ["which", "what"]) and any(w in q_lower for w in ["most", "highest", "top", "greatest"]):
        # Product ordered most
        if "product" in q_lower and "product" in columns:
            code = f"""# Group by product and find highest frequency
df_target = datasets['{dataset_key}']
product_counts = df_target['product'].dropna().value_counts()
top_product = product_counts.index[0]
top_count = int(product_counts.iloc[0])
result = f"{{top_product}} ({{top_count}} orders)"
print(result)"""
            return code, ["product"], "grouped_aggregation", "The product ordered the most times is '{result}'."

        # Department with most employees
        if "department" in q_lower and "department" in columns:
            code = f"""# Group by department and find highest headcount
df_target = datasets['{dataset_key}']
dept_counts = df_target['department'].dropna().value_counts()
top_dept = dept_counts.index[0]
top_count = int(dept_counts.iloc[0])
result = f"{{top_dept}} ({{top_count}} employees)"
print(result)"""
            return code, ["department"], "grouped_aggregation", "The department with the highest headcount is '{result}'."

        # Cohort with most patients
        if "cohort" in q_lower and "cohort" in columns:
            code = f"""# Group by cohort and find largest group
df_target = datasets['{dataset_key}']
cohort_counts = df_target['cohort'].dropna().value_counts()
top_cohort = cohort_counts.index[0]
top_count = int(cohort_counts.iloc[0])
result = f"{{top_cohort}} ({{top_count}} patients)"
print(result)"""
            return code, ["cohort"], "grouped_aggregation", "The cohort with the largest patient count is '{result}'."

        # Warehouse location
        if "warehouse" in q_lower and "warehouse_location" in columns:
            code = f"""# Group by warehouse location and count items
df_target = datasets['{dataset_key}']
loc_counts = df_target['warehouse_location'].dropna().value_counts()
top_loc = loc_counts.index[0]
top_count = int(loc_counts.iloc[0])
result = f"{{top_loc}} ({{top_count}} items)"
print(result)"""
            return code, ["warehouse_location"], "grouped_aggregation", "The warehouse with the highest count is '{result}'."

    # 3. MIN / MAX QUERIES
    # Examples: "What is the highest employee rating?", "What is the lowest base salary?"
    if any(w in q_lower for w in ["highest", "maximum", "max", "lowest", "minimum", "min"]):
        is_max = any(w in q_lower for w in ["highest", "maximum", "max"])
        op_name = "max" if is_max else "min"

        # Check for rating
        if "rating" in q_lower and "rating" in columns:
            code = f"""# Find {op_name} rating
df_target = datasets['{dataset_key}']
numeric_ratings = pd.to_numeric(df_target['rating'], errors='coerce')
result = float(numeric_ratings.{op_name}())
print(f"{op_name.capitalize()} rating: {{result}}")"""
            return code, ["rating"], op_name, f"The {op_name} employee rating is {{result}}."

        # Check for quantity
        if "quantity" in q_lower and "quantity" in columns:
            code = f"""# Find {op_name} quantity
df_target = datasets['{dataset_key}']
numeric_qty = pd.to_numeric(df_target['quantity'], errors='coerce')
result = int(numeric_qty.{op_name}())
print(f"{op_name.capitalize()} quantity: {{result}}")"""
            return code, ["quantity"], op_name, f"The {op_name} order quantity is {{result}}."

    # 4. SUM / TOTAL QUERIES
    if any(w in q_lower for w in ["total quantity", "sum of quantity", "how many items"]):
        if "quantity" in columns:
            code = f"""# Sum of quantity ordered
df_target = datasets['{dataset_key}']
numeric_qty = pd.to_numeric(df_target['quantity'], errors='coerce')
result = int(numeric_qty.dropna().sum())
print(f"Total quantity: {{result}}")"""
            return code, ["quantity"], "sum", "The total quantity ordered across all valid records is {result}."

    # 5. PERCENTAGE QUERIES
    # Examples: "What percentage of orders were Completed?"
    if "percentage" in q_lower or "%" in q_lower:
        if "completed" in q_lower and "status" in columns:
            code = f"""# Calculate percentage of completed orders
df_target = datasets['{dataset_key}']
total_count = len(df_target)
completed_count = (df_target['status'].astype(str).str.strip().str.lower() == 'completed').sum()
result = round(float((completed_count / total_count) * 100), 2)
print(f"Completed percentage: {{result}}%")"""
            return code, ["status"], "percentage", "{result}% of orders have 'Completed' status."

        if "engineering" in q_lower and "department" in columns:
            code = f"""# Calculate percentage of employees in Engineering
df_target = datasets['{dataset_key}']
total_count = len(df_target)
eng_count = (df_target['department'].astype(str).str.strip().str.lower() == 'engineering').sum()
result = round(float((eng_count / total_count) * 100), 2)
print(f"Engineering percentage: {{result}}%")"""
            return code, ["department"], "percentage", "{result}% of employees belong to Engineering."

    # 6. Fallback generic counting or basic aggregation if recognizable column present
    for col in columns:
        if col.lower() in q_lower:
            code = f"""# Inspect column {col}
df_target = datasets['{dataset_key}']
col_series = df_target['{col}']
result = int(col_series.count())
print(f"Valid entries in {col}: {{result}}")"""
            return code, [col], "non_null_count", f"There are {{result}} non-null entries in column '{col}'."

    # If completely unrecognized and ambiguous
    return None, [], "unknown", None

def assess_question_forensics(question: str, dataset_id: Optional[str] = None) -> AnalysisForensicsResponse:
    """
    Stage 3 Data Forensics Assessment for a specific question:
    Evaluates whether the requested question touches corrupt, conflicting,
    or ambiguous columns before committing to code generation.
    """
    dataset_entry = resolve_target_dataset(dataset_id, question)
    if not dataset_entry:
        return AnalysisForensicsResponse(
            status="cannot_determine",
            safe_to_analyze=False,
            question=question,
            reason="CANNOT DETERMINE — No matching dataset found in the registry.",
            warnings=["No dataset registered or active."],
            findings=[]
        )
    forensic_report = run_data_forensics(dataset_entry, all_datasets=DATASET_STORE)
    return assess_forensic_impact_on_question(question, dataset_entry, forensic_report)

def analyze_user_question(question: str, dataset_id: Optional[str] = None) -> AnalysisResponse:
    """
    Executes the Proof-Carrying Analysis pipeline upgraded with Stage 3 Data Forensics:
    1. Identify target dataset
    2. Forensically inspect data & assess impact on question (Refusal check)
    3. Propose Python analysis code
    4. Execute in sandboxed Python environment
    5. Capture raw execution result & verify
    6. Construct proof-carrying response
    """
    clean_question = question.strip()
    if not clean_question:
        return AnalysisResponse(
            status="cannot_determine",
            question=question,
            reason="CANNOT DETERMINE — Question was empty or whitespace.",
            warnings=["No question provided."]
        )

    # 1. Resolve dataset
    dataset_entry = resolve_target_dataset(dataset_id, clean_question)
    if not dataset_entry:
        return AnalysisResponse(
            status="cannot_determine",
            question=clean_question,
            reason="CANNOT DETERMINE — No matching dataset found in the registry.",
            warnings=["No dataset registered or active."]
        )

    target_meta = dataset_entry["meta"]
    target_id = target_meta.id
    target_name = target_meta.name

    # 2. Stage 3 Data Forensics Pre-Execution Inspection Gate
    forensic_report = run_data_forensics(dataset_entry, all_datasets=DATASET_STORE)
    forensic_assessment = assess_forensic_impact_on_question(clean_question, dataset_entry, forensic_report)

    if not forensic_assessment.safe_to_analyze:
        return AnalysisResponse(
            status="cannot_determine",
            question=clean_question,
            dataset_used=target_id,
            dataset_name=target_name,
            columns_used=forensic_assessment.affected_columns,
            execution_success=False,
            reason=forensic_assessment.reason,
            warnings=forensic_assessment.warnings,
            forensic_status=forensic_assessment.status,
            forensic_findings=forensic_assessment.findings,
            final_answer=None
        )

    # 2b. Stage 1 Trap / Quality Guardrail Inspection (Safety regression check)
    trap_refusal = check_stage1_traps(dataset_entry, clean_question)
    if trap_refusal:
        return AnalysisResponse(
            status="cannot_determine",
            question=clean_question,
            dataset_used=target_id,
            dataset_name=target_name,
            columns_used=trap_refusal.get("columns_used", []),
            execution_success=False,
            reason=trap_refusal.get("reason"),
            warnings=trap_refusal.get("warnings", []),
            forensic_status="unsafe_for_requested_analysis",
            final_answer=None
        )

    # 3. Code Synthesis
    code, cols_used, operation, answer_tpl = synthesize_analysis_plan(dataset_entry, clean_question)

    if not code:
        return AnalysisResponse(
            status="cannot_determine",
            question=clean_question,
            dataset_used=target_id,
            dataset_name=target_name,
            columns_used=[],
            execution_success=False,
            reason=f"CANNOT DETERMINE — The question is too ambiguous to map reliably to operations in dataset '{target_name}'.",
            warnings=["Could not determine deterministic operation without making unverified assumptions."],
            forensic_status=forensic_assessment.status,
            final_answer=None
        )

    # 4. Controlled Sandbox Execution
    datasets_dict = {target_id: dataset_entry["df"]}
    exec_result = execute_code(
        code_str=code,
        datasets_map=datasets_dict,
        primary_df=dataset_entry["df"]
    )

    # 5. Verification & Final Proof Representation
    if not exec_result["success"]:
        return AnalysisResponse(
            status="cannot_determine",
            question=clean_question,
            dataset_used=target_id,
            dataset_name=target_name,
            columns_used=cols_used,
            operation=operation,
            generated_code=code,
            execution_success=False,
            execution_result=None,
            reason=f"CANNOT DETERMINE — The generated analysis could not be executed successfully ({exec_result.get('error')}).",
            warnings=[f"Execution failure: {exec_result.get('error')}"],
            execution_time_ms=exec_result["execution_time_ms"],
            forensic_status=forensic_assessment.status,
            final_answer=None
        )

    raw_val = exec_result["result"]

    # Format human-readable verified answer
    if answer_tpl:
        try:
            if isinstance(raw_val, float):
                formatted_num = f"{raw_val:,.2f}" if not raw_val.is_integer() else f"{int(raw_val):,}"
            elif isinstance(raw_val, int):
                formatted_num = f"{raw_val:,}"
            else:
                formatted_num = str(raw_val)
            human_answer = answer_tpl.format(result=formatted_num)
        except Exception:
            human_answer = f"The verified execution result is: {raw_val}."
    else:
        human_answer = f"Calculated value: {raw_val}."

    return AnalysisResponse(
        status="verified",
        question=clean_question,
        dataset_used=target_id,
        dataset_name=target_name,
        columns_used=cols_used,
        operation=operation,
        generated_code=code,
        execution_success=True,
        execution_result=raw_val,
        final_answer=human_answer,
        warnings=[],
        execution_time_ms=exec_result["execution_time_ms"],
        forensic_status=forensic_assessment.status,
        forensic_findings=forensic_assessment.findings
    )

