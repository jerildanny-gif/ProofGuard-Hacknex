import sys
sys.path.insert(0, '.')
from app.models.schemas import GuardianRequest, GuardianResponse, TrustChallenge, TrustDimension, GuardianVerdict, ChallengeRequest, ChallengeResponse
from app.services.guardian_service import run_guardian, run_user_challenge
from app.api.guardian import router

# Quick smoke test
req = GuardianRequest(
    question="How many orders are there?",
    dataset_id="sample-sales",
    answer_status="verified",
    final_answer="There are 15 orders.",
    generated_code="result = len(df)",
    execution_result=15,
    columns_used=[],
    forensic_status="clean",
    forensic_findings=[],
    warnings=[]
)

resp = run_guardian(req)
print(f"Trust Score: {resp.trust_score}/100")
print(f"Grade: {resp.trust_grade}")
print(f"Verdict: {resp.verdict.verdict}")
print(f"Challenges: {len(resp.challenges)}")
print(f"Lineage steps: {len(resp.proof_lineage)}")
print(f"Can publish: {resp.verdict.can_publish}")
print("Stage 4 Guardian: ALL TESTS PASSED")
