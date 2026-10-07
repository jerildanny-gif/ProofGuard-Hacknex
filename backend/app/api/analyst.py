from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from app.models.schemas import (
    AnalysisRequest, 
    AnalysisResponse, 
    SuggestedQuestion,
    AnalysisForensicsRequest,
    AnalysisForensicsResponse
)
from app.services.analyst_service import (
    analyze_user_question,
    get_suggested_questions,
    assess_question_forensics
)

router = APIRouter(prefix="/analyze", tags=["analyst"])

@router.post("", response_model=AnalysisResponse)
async def analyze_question(payload: AnalysisRequest):
    """
    Stage 2 Core Proof-Carrying Analyst Endpoint upgraded with Stage 3 Data Forensics:
    1. Interprets natural language question against registered datasets.
    2. Runs Stage 3 Data Forensics inspection & analysis impact assessment.
    3. If unsafe -> returns CANNOT DETERMINE / NEEDS REVIEW with forensic evidence.
    4. If safe -> synthesizes safe Python/Pandas code.
    5. Executes in isolated sandbox against real dataset copy.
    6. Returns verified answer alongside the exact execution proof code.
    """
    # Prefer dataset_id, fallback to first in dataset_ids if provided
    ds_id = payload.dataset_id
    if not ds_id and payload.dataset_ids:
        ds_id = payload.dataset_ids[0]

    response = analyze_user_question(
        question=payload.question,
        dataset_id=ds_id
    )
    return response

@router.post("/forensics", response_model=AnalysisForensicsResponse)
async def analyze_forensics_endpoint(payload: AnalysisForensicsRequest):
    """
    Stage 3 Data Forensics Assessment for a specific question:
    Evaluates whether the requested question touches corrupt, conflicting,
    or ambiguous columns before committing to code generation.
    """
    ds_id = payload.dataset_id
    if not ds_id and payload.dataset_ids:
        ds_id = payload.dataset_ids[0]

    return assess_question_forensics(
        question=payload.question,
        dataset_id=ds_id
    )

@router.get("/suggestions", response_model=List[SuggestedQuestion])
async def get_suggestions(dataset_id: Optional[str] = Query(None)):
    """Returns curated demo queries for dataset exploration and trap testing."""
    return get_suggested_questions(dataset_id)

