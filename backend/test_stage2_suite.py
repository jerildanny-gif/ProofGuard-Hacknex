"""
Comprehensive Verification Suite for ProofGuard Stage 1 & Stage 2.
Tests all requirements, including execution proof and refusal guarantees.
"""
import sys
import os
from pathlib import Path

# Force UTF-8 stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("PROOFGUARD STAGE 1 & 2 AUTOMATED VERIFICATION SUITE")
    print("=" * 60)

    # TEST GROUP 1: STAGE 1 REGRESSION TESTS
    print("\n--- [GROUP 1: Stage 1 Foundation Intact] ---")
    
    # 1.1 Health endpoint
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] Health check endpoint operational:", res.json())

    # 1.2 Catalog of sample datasets
    res = client.get("/api/datasets/samples")
    assert res.status_code == 200
    samples = res.json()
    assert len(samples) == 4, f"Expected 4 sample datasets, got {len(samples)}"
    print(f"[PASS] Sample datasets catalog loaded ({len(samples)} presets verified)")

    # 1.3 Datasets list
    res = client.get("/api/datasets")
    assert res.status_code == 200
    datasets = res.json()
    assert len(datasets) >= 4
    print(f"[PASS] Datasets registry operational ({len(datasets)} datasets registered)")

    # 1.4 Dataset details & Stage 1 anomalies for sample-sales
    res = client.get("/api/datasets/sample-sales")
    assert res.status_code == 200
    details = res.json()
    assert "health" in details and "columns" in details
    unit_price_col = next((c for c in details["columns"] if c["name"] == "unit_price"), None)
    assert unit_price_col is not None
    assert any("mixed currencies" in a.lower() for a in unit_price_col["anomalies"])
    print("[PASS] Stage 1 anomaly detection profiling operational (mixed currencies correctly flagged)")

    # 1.5 Preview pagination
    res = client.get("/api/datasets/sample-sales/preview?page=1&page_size=5")
    assert res.status_code == 200
    preview = res.json()
    assert len(preview["rows"]) == 5
    print("[PASS] Stage 1 dataset preview pagination operational")

    # TEST GROUP 2: STAGE 2 CORE PROOF-CARRYING ANALYST
    print("\n--- [GROUP 2: Stage 2 Natural Language & Proof Execution] ---")

    # Test 1: Count query - "How many orders are there?"
    res = client.post("/api/analyze", json={
        "question": "How many orders are there?",
        "dataset_id": "sample-sales"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "verified", f"Expected verified, got {data}"
    assert data["execution_success"] is True
    assert data["execution_result"] == 20
    assert data["generated_code"] is not None
    assert "len(" in data["generated_code"]
    print("[PASS] Test 1: Count query verified")
    print(f"   Answer: '{data['final_answer']}'")
    print(f"   Execution Result: {data['execution_result']}")
    print(f"   Execution Time: {data['execution_time_ms']} ms")

    # Test 2: Filtering query - "How many orders were completed?"
    res = client.post("/api/analyze", json={
        "question": "How many orders were completed?",
        "dataset_id": "sample-sales"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "verified"
    assert data["execution_result"] == 14
    print("[PASS] Test 2: Filtering query verified")
    print(f"   Answer: '{data['final_answer']}'")
    print(f"   Execution Result: {data['execution_result']}")

    # Test 3: Grouped aggregation - "Which product was ordered the most times?"
    res = client.post("/api/analyze", json={
        "question": "Which product was ordered the most times?",
        "dataset_id": "sample-sales"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "verified"
    assert "Cloud Server Gen3" in str(data["execution_result"])
    print("[PASS] Test 3: Grouped aggregation verified")
    print(f"   Answer: '{data['final_answer']}'")
    print(f"   Execution Result: {data['execution_result']}")

    # Test 4: HR Employee counting - "How many employees are there?"
    res = client.post("/api/analyze", json={
        "question": "How many employees are there?",
        "dataset_id": "sample-employees"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "verified"
    assert data["execution_result"] == 17
    print("[PASS] Test 4: HR directory counting verified (17 employees)")

    # Test 5: Clinical cohort patient counting - "How many patients are in the dataset?"
    res = client.post("/api/analyze", json={
        "question": "How many patients are in the dataset?",
        "dataset_id": "sample-clinical"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "verified"
    assert data["execution_result"] == 13
    print("[PASS] Test 5: Clinical trial patient count verified (13 patients)")

    # TEST GROUP 3: REFUSALS & CANNOT DETERMINE GUARANTEES (PS08 CORE)
    print("\n--- [GROUP 3: Strict Refusal / CANNOT DETERMINE Rules] ---")

    # Test 6: Nonexistent year - "What were the total orders in 2030?"
    res = client.post("/api/analyze", json={
        "question": "What were the total orders in 2030?",
        "dataset_id": "sample-sales"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "cannot_determine", f"Expected cannot_determine, got {data['status']}"
    assert data["execution_success"] is False
    assert data["final_answer"] is None
    assert "2030" in data["reason"]
    print("[PASS] Test 6: Out-of-bounds year refused")
    print(f"   Refusal Reason: '{data['reason']}'")

    # Test 7: Mixed currencies calculation - "What is the total revenue in dollars?"
    res = client.post("/api/analyze", json={
        "question": "What is the total revenue in dollars?",
        "dataset_id": "sample-sales"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "cannot_determine"
    assert data["execution_success"] is False
    assert "mixed currencies" in data["reason"].lower()
    print("[PASS] Test 7: Mixed currency calculation refused")
    print(f"   Refusal Reason: '{data['reason']}'")

    # Test 8: Mixed measurement units calculation - "What is the average shipping weight?"
    res = client.post("/api/analyze", json={
        "question": "What is the average shipping weight?",
        "dataset_id": "sample-sales"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "cannot_determine"
    assert "measurement units" in data["reason"].lower() or "conflicting measurement" in data["reason"].lower()
    print("[PASS] Test 8: Mixed measurement units calculation refused")
    print(f"   Refusal Reason: '{data['reason']}'")

    # Test 9: Impossible/negative values in clinical trial - "What is the average age?"
    res = client.post("/api/analyze", json={
        "question": "What is the average age?",
        "dataset_id": "sample-clinical"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "cannot_determine"
    assert "negative" in data["reason"].lower()
    print("[PASS] Test 9: Corrupted medical values refused")
    print(f"   Refusal Reason: '{data['reason']}'")

    # Test 10: Negative salary anomaly in HR directory - "What is the average salary?"
    res = client.post("/api/analyze", json={
        "question": "What is the average salary?",
        "dataset_id": "sample-employees"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "cannot_determine"
    assert "negative" in data["reason"].lower()
    print("[PASS] Test 10: Negative salary outlier calculation refused")
    print(f"   Refusal Reason: '{data['reason']}'")

    # Test 11: Inventory contradictions - "What is the total stock across warehouses?"
    res = client.post("/api/analyze", json={
        "question": "What is the total stock across warehouses?",
        "dataset_id": "sample-inventory"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "cannot_determine"
    assert "discrepancies" in data["reason"].lower() or "contradictions" in data["reason"].lower()
    print("[PASS] Test 11: Contradictory inventory sum refused")
    print(f"   Refusal Reason: '{data['reason']}'")

    # Test 12: Nonexistent/missing metric - "What is the profit margin?"
    res = client.post("/api/analyze", json={
        "question": "What is the profit margin?",
        "dataset_id": "sample-employees"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "cannot_determine"
    assert "not contained" in data["reason"].lower() or "profit" in data["reason"].lower()
    print("[PASS] Test 12: Missing column/metric refused without hallucination")
    print(f"   Refusal Reason: '{data['reason']}'")

    # TEST GROUP 4: SANDBOX SECURITY REJECTION
    print("\n--- [GROUP 4: Controlled Sandbox Security Boundary] ---")
    from app.services.code_executor import execute_code
    sec_res = execute_code("import os; result = os.listdir('.')", {})
    assert sec_res["success"] is False
    assert "Security boundary violation" in sec_res["error"]
    print(f"[PASS] Security check passed: Disallowed import blocked ('{sec_res['error']}')")

    sec_res2 = execute_code("open('/etc/passwd', 'r')", {})
    assert sec_res2["success"] is False
    assert "Security boundary violation" in sec_res2["error"]
    print(f"[PASS] Security check passed: Disallowed builtin call blocked ('{sec_res2['error']}')")

    # TEST GROUP 5: SUGGESTIONS ENDPOINT
    print("\n--- [GROUP 5: Demo & Trap Suggestions Catalog] ---")
    res = client.get("/api/analyze/suggestions")
    assert res.status_code == 200
    suggestions = res.json()
    assert len(suggestions) >= 10
    traps = [s for s in suggestions if s["is_trap"]]
    assert len(traps) >= 5
    print(f"[PASS] Suggestions endpoint verified ({len(suggestions)} queries, {len(traps)} traps)")

    print("\n" + "=" * 60)
    print("ALL 17 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("STAGE 2 — CORE PROOF-CARRYING ANALYST VERIFIED.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
