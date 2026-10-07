from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    GuardianRequest,
    GuardianResponse,
    ChallengeRequest,
    ChallengeResponse,
)
from app.services.guardian_service import run_guardian, run_user_challenge

router = APIRouter(prefix="/guardian", tags=["guardian"])


@router.post("/evaluate", response_model=GuardianResponse)
async def guardian_evaluate(payload: GuardianRequest):
    """
    Stage 4 — Answer Guardian Evaluation Endpoint.

    Accepts a GuardianRequest containing the analyst's answer (question,
    status, code, result, forensic findings) and returns a full
    GuardianResponse with:
    - Composite Trust Score (0-100)
    - Trust Grade (A/B/C/D/F)
    - Trust Dimension Breakdown (5 dimensions)
    - Adversarial Challenges raised by the Guardian
    - Final Verdict (TRUSTED / CONDITIONALLY_TRUSTED / DISPUTED / REJECTED)
    - Proof Lineage Chain
    - Evidence Chain Summary
    - Actionable Recommendation

    The Guardian is INDEPENDENT — it never modifies the answer, only evaluates.
    """
    try:
        return run_guardian(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Guardian evaluation failed: {str(e)}")


@router.post("/challenge", response_model=ChallengeResponse)
async def user_challenge(payload: ChallengeRequest):
    """
    Stage 4 — User Counter-Challenge Endpoint.

    Allows users to challenge the Guardian's verdict with their own reasoning.
    The Guardian evaluates the counter-challenge and either upholds its verdict
    or revises it to CONDITIONALLY_TRUSTED if sufficient evidence is provided.
    """
    try:
        return run_user_challenge(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Challenge evaluation failed: {str(e)}")
