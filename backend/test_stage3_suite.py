"""
Comprehensive Verification Suite for ProofGuard Stage 3 — DATA FORENSICS.
Tests all requirements specified in the Stage 3 Specification:
1. Missing-value & placeholder forensics
2. Exact duplicate & duplicate identifier forensics
3. Conflicting duplicate forensics
4. Date forensics (ambiguous DD/MM vs MM/DD & mixed formats)
5. Currency mismatch forensics
6. Measurement unit mismatch forensics
7. Invalid / impossible value forensics
8. Contradictory inventory forensics
9. Analysis Impact Assessment (safe questions allowed, unsafe questions blocked)
10. Stage 3 API Endpoints (/api/datasets/{id}/forensics and /api/analyze/forensics)
11. Preserved Stage 1 & Stage 2 functionality
"""
import sys
from pathlib import Path

# Force UTF-8 stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("=" * 65)
    print("PROOFGUARD STAGE 3 — DATA FORENSICS VERIFICATION SUITE")
    print("=" * 65)

    # -------------------------------------------------------------
    # TEST 1: Global E-Commerce Sales - Currency Mismatch Detected
    # -------------------------------------------------------------
    print("\n--- [TEST 1: Global E-Commerce Sales Currency Forensics] ---")
    res = client.get("/api/datasets/sample-sales/forensics")
    assert res.status_code == 200, f"Forensics endpoint failed: {res.text}"
    sales_forensics = res.json()
    assert sales_forensics["dataset_id"] == "sample-sales"
    assert sales_forensics["overall_status"] in ["NEEDS REVIEW", "UNSAFE_FOR_REQUESTED_ANALYSIS"]
    
    currency_findings = [f for f in sales_forensics["findings"] if f["category"] == "currency_mismatch"]
    assert len(currency_findings) > 0, "Expected currency mismatch finding in sample-sales"
    curr_f = currency_findings[0]
    assert curr_f["severity"] == "CRITICAL"
    assert curr_f["column"] == "unit_price"
    assert "mixed" in curr_f["message"].lower() or "conflicting currencies" in curr_f["message"].lower()
    assert "conversion" in curr_f["recommendation"].lower()
    print(f"[PASS] Test 1: Currency mismatch successfully detected (Severity: {curr_f['severity']}, Column: {curr_f['column']})")
    print(f"       Message: {curr_f['message']}")

    # -------------------------------------------------------------
    # TEST 2: Global E-Commerce Sales - Duplicate Order IDs Detected
    # -------------------------------------------------------------
    print("\n--- [TEST 2: Global E-Commerce Sales Duplicate Forensics] ---")
    dup_findings = [f for f in sales_forensics["findings"] if f["category"] in ["duplicate_records", "conflicting_duplicates"]]
    assert len(dup_findings) > 0, "Expected duplicate findings in sample-sales"
    print(f"[PASS] Test 2: Duplicate records detected ({len(dup_findings)} finding(s))")
    for df_item in dup_findings:
        print(f"       - [{df_item['severity']}] {df_item['message']}")
        assert df_item["impact"] is not None
        assert df_item["recommendation"] is not None

    # Missing Discount Check in Sales
    missing_findings = [f for f in sales_forensics["findings"] if f["category"] == "missing_data"]
    discount_missing = next((f for f in missing_findings if f["column"] == "discount_pct"), None)
    assert discount_missing is not None, "Expected missing discount placeholders detected"
    print(f"[PASS] Test 2b: Missing/masked placeholders detected in discount_pct: {discount_missing['message']}")

    # Unit Mismatch Check in Sales
    unit_findings = [f for f in sales_forensics["findings"] if f["category"] == "unit_mismatch"]
    assert len(unit_findings) > 0, "Expected unit mismatch finding in shipping_weight"
    print(f"[PASS] Test 2c: Unit mismatch detected in {unit_findings[0]['column']}: {unit_findings[0]['message']}")

    # -------------------------------------------------------------
    # TEST 3: HR Employee Directory - Date Ambiguity Detected
    # -------------------------------------------------------------
    print("\n--- [TEST 3: HR Employee Directory Date Forensics] ---")
    res = client.get("/api/datasets/sample-employees/forensics")
    assert res.status_code == 200
    emp_forensics = res.json()
    
    date_findings = [f for f in emp_forensics["findings"] if f["category"] in ["ambiguous_dates", "mixed_date_formats"]]
    assert len(date_findings) > 0, "Expected date ambiguity findings in HR directory"
    ambig_f = next((f for f in date_findings if f["category"] == "ambiguous_dates"), None)
    assert ambig_f is not None, "Expected ambiguous_dates finding"
    assert ambig_f["severity"] == "HIGH"
    assert "dd/mm" in ambig_f["message"].lower() or "ambiguous" in ambig_f["message"].lower()
    print(f"[PASS] Test 3: Date ambiguity detected in {ambig_f['column']}: {ambig_f['message']}")
    print(f"       Impact: {ambig_f['impact']}")

    # -------------------------------------------------------------
    # TEST 4: HR Employee Directory - Duplicate Employees & Salary
    # -------------------------------------------------------------
    print("\n--- [TEST 4: HR Employee Directory Duplicates & Outliers] ---")
    emp_dups = [f for f in emp_forensics["findings"] if f["category"] in ["duplicate_records", "conflicting_duplicates"]]
    assert len(emp_dups) > 0, "Expected duplicate employee records detected"
    print(f"[PASS] Test 4a: Duplicate employee records detected: {emp_dups[0]['message']}")

    salary_findings = [f for f in emp_forensics["findings"] if f["category"] == "invalid_impossible_values" and "salary" in (f["column"] or "").lower()]
    assert len(salary_findings) > 0, "Expected negative salary outlier detected"
    assert salary_findings[0]["severity"] == "CRITICAL"
    print(f"[PASS] Test 4b: Negative salary anomaly detected: {salary_findings[0]['message']}")

    # -------------------------------------------------------------
    # TEST 5: Clinical Trial Cohorts - Impossible Medical Values
    # -------------------------------------------------------------
    print("\n--- [TEST 5: Clinical Trial Cohorts Impossible Values Forensics] ---")
    res = client.get("/api/datasets/sample-clinical/forensics")
    assert res.status_code == 200
    clin_forensics = res.json()
    
    med_impossible = [f for f in clin_forensics["findings"] if f["category"] == "invalid_impossible_values"]
    assert len(med_impossible) >= 2, f"Expected both age and BP impossible values, got {len(med_impossible)}"
    age_f = next((f for f in med_impossible if "age" in (f["column"] or "").lower()), None)
    bp_f = next((f for f in med_impossible if any(k in (f["column"] or "").lower() for k in ["bp", "systolic"])), None)
    assert age_f is not None and age_f["severity"] == "CRITICAL"
    assert bp_f is not None and bp_f["severity"] == "CRITICAL"
    print(f"[PASS] Test 5a: Physically impossible age detected: {age_f['message']}")
    print(f"[PASS] Test 5b: Physiologically impossible blood pressure detected: {bp_f['message']}")

    # -------------------------------------------------------------
    # TEST 6: Inventory Audit - Contradictory Stock Detected
    # -------------------------------------------------------------
    print("\n--- [TEST 6: Inventory Audit Contradictory Records Forensics] ---")
    res = client.get("/api/datasets/sample-inventory/forensics")
    assert res.status_code == 200
    inv_forensics = res.json()
    
    # Check conflicting duplicate (SKU-502) and cross-system discrepancy
    conflict_findings = [f for f in inv_forensics["findings"] if f["category"] in ["conflicting_duplicates", "contradictory_data"]]
    assert len(conflict_findings) > 0, "Expected conflicting duplicates / discrepancies in inventory"
    print(f"[PASS] Test 6a: Contradictory inventory records detected:")
    for cf in conflict_findings:
        print(f"       - [{cf['severity']}] {cf['message']}")

    # Check negative stock / inventory (SKU-506)
    neg_stock = [f for f in inv_forensics["findings"] if f["category"] == "invalid_impossible_values" and any(k in (f["column"] or "").lower() for k in ["stock", "inventory", "physical_audit"])]
    assert len(neg_stock) > 0, "Expected negative stock finding in inventory"
    print(f"[PASS] Test 6b: Negative stock count detected: {neg_stock[0]['message']}")


    # -------------------------------------------------------------
    # TEST 7: Forensic Gate Before Analysis - Total Revenue Blocked
    # -------------------------------------------------------------
    print("\n--- [TEST 7: Pre-Execution Forensic Gate — Total Revenue Unsafe] ---")
    res = client.post("/api/analyze/forensics", json={
        "question": "What is the total revenue?",
        "dataset_ids": ["sample-sales"]
    })
    assert res.status_code == 200
    gate_res = res.json()
    assert gate_res["safe_to_analyze"] is False
    assert gate_res["status"] == "unsafe_for_requested_analysis"
    assert "unit_price" in gate_res["affected_columns"]
    print(f"[PASS] Test 7a: POST /api/analyze/forensics correctly identified unsafe question")
    print(f"       Status: {gate_res['status']}, Reason: '{gate_res['reason']}'")

    # Now verify POST /api/analyze is guarded
    res = client.post("/api/analyze", json={
        "question": "What is the total revenue?",
        "dataset_id": "sample-sales"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "cannot_determine"
    assert data["execution_success"] is False
    assert "mixed currencies" in data["reason"].lower() or "multiple currencies" in data["reason"].lower()
    assert data["forensic_status"] == "unsafe_for_requested_analysis"
    print(f"[PASS] Test 7b: Full analysis pipeline refused calculation before code execution")

    # -------------------------------------------------------------
    # TEST 8: Do Not Overblock - Unrelated Issues Allow Valid Question
    # -------------------------------------------------------------
    print("\n--- [TEST 8: Non-Overblocking Rule — Order Count Allowed] ---")
    # Even though sample-sales has mixed currency in unit_price and missing discount,
    # counting orders does not depend on those columns!
    res = client.post("/api/analyze/forensics", json={
        "question": "How many orders are there?",
        "dataset_ids": ["sample-sales"]
    })
    assert res.status_code == 200
    gate_order = res.json()
    assert gate_order["safe_to_analyze"] is True, f"Expected safe_to_analyze=True, got {gate_order}"
    print(f"[PASS] Test 8a: Forensic gate approved query 'How many orders are there?' (Status: {gate_order['status']})")

    res = client.post("/api/analyze", json={
        "question": "How many orders are there?",
        "dataset_id": "sample-sales"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "verified"
    assert data["execution_success"] is True
    assert data["execution_result"] == 20
    print(f"[PASS] Test 8b: Execution verified (Result: {data['execution_result']}) without being overblocked!")

    # -------------------------------------------------------------
    # TEST 9: Date Ambiguity Question Refused Without Guessing
    # -------------------------------------------------------------
    print("\n--- [TEST 9: Ambiguous Date Query Refusal] ---")
    res = client.post("/api/analyze", json={
        "question": "How many employees were hired in April 2021?",
        "dataset_id": "sample-employees"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "cannot_determine"
    assert "ambiguous" in data["reason"].lower() or "dd/mm" in data["reason"].lower()
    print(f"[PASS] Test 9: Ambiguous date query refused without guessing format")
    print(f"       Refusal Reason: '{data['reason']}'")

    # -------------------------------------------------------------
    # TEST 10: Regression Verification - Stage 1 Endpoints Intact
    # -------------------------------------------------------------
    print("\n--- [TEST 10: Stage 1 Foundation Regression Checks] ---")
    res = client.get("/api/health")
    assert res.status_code == 200
    res = client.get("/api/datasets/samples")
    assert res.status_code == 200 and len(res.json()) >= 4
    res = client.get("/api/datasets/sample-sales/preview?page=1&page_size=5")
    assert res.status_code == 200 and len(res.json()["rows"]) == 5
    print("[PASS] Test 10: Stage 1 sample catalogue, health, and pagination operational")

    # -------------------------------------------------------------
    # TEST 11: Regression Verification - Stage 2 Proofs Intact
    # -------------------------------------------------------------
    print("\n--- [TEST 11: Stage 2 Natural Language & Proof Execution Intact] ---")
    res = client.post("/api/analyze", json={
        "question": "Which product was ordered the most times?",
        "dataset_id": "sample-sales"
    })
    assert res.status_code == 200 and res.json()["status"] == "verified"
    assert "Cloud Server Gen3" in str(res.json()["execution_result"])

    res = client.post("/api/analyze", json={
        "question": "Which department has the most employees?",
        "dataset_id": "sample-employees"
    })
    assert res.status_code == 200 and res.json()["status"] == "verified"
    print("[PASS] Test 11: Stage 2 deterministic proof-carrying code execution intact")

    # -------------------------------------------------------------
    # TEST 12: Finding Metadata & Forensic Report Quality
    # -------------------------------------------------------------
    print("\n--- [TEST 12: Structured Forensic Report Quality & Fields] ---")
    res = client.get("/api/datasets/sample-sales/forensics")
    report = res.json()
    assert "summary_counts" in report
    sc = report["summary_counts"]
    assert sc["currency_issues_count"] > 0
    assert sc["unit_issues_count"] > 0
    assert sc["total_findings"] > 0
    for finding in report["findings"]:
        assert finding["severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
        assert finding["message"] and finding["impact"] and finding["recommendation"]
    print(f"[PASS] Test 12: All forensic findings conform to structured schema with severity, impact, and recommendations")

    print("\n" + "=" * 65)
    print("ALL 12 STAGE 3 FORENSIC TESTS PASSED SUCCESSFULLY!")
    print("STAGE 3 — DATA FORENSICS VERIFIED ON ALL SAMPLE DATASETS.")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
