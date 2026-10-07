from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ColumnSummaryStats(BaseModel):
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[Any] = None
    q25: Optional[Any] = None
    median: Optional[Any] = None
    q75: Optional[Any] = None
    max: Optional[Any] = None
    top_values: Optional[List[Dict[str, Any]]] = None

class ColumnInfo(BaseModel):
    name: str
    dtype: str
    inferred_type: str  # numeric, categorical, datetime, text, boolean, mixed
    non_null_count: int
    null_count: int
    null_percentage: float
    unique_count: int
    sample_values: List[Any]
    stats: Optional[ColumnSummaryStats] = None
    anomalies: List[str] = []

class DatasetHealthSummary(BaseModel):
    health_score: int  # 0 to 100
    duplicate_rows: int
    duplicate_percentage: float
    total_missing_cells: int
    missing_cells_percentage: float
    detected_issues: List[Dict[str, Any]]
    readiness_notes: List[str]

class DatasetMeta(BaseModel):
    id: str
    name: str
    filename: str
    file_type: str
    size_bytes: int
    row_count: int
    column_count: int
    uploaded_at: str
    is_sample: bool = False
    description: Optional[str] = None

class DatasetDetailResponse(BaseModel):
    meta: DatasetMeta
    columns: List[ColumnInfo]
    health: DatasetHealthSummary
    sheets: Optional[List[str]] = None

class DatasetPreviewResponse(BaseModel):
    meta: DatasetMeta
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int
    page: int
    page_size: int
    total_pages: int

class SampleDatasetInfo(BaseModel):
    id: str
    title: str
    filename: str
    description: str
    challenge_type: str
    tags: List[str]

class ForensicFinding(BaseModel):
    id: str
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
    category: str  # "missing_data", "duplicate_records", "conflicting_duplicates", "ambiguous_dates", "mixed_date_formats", "currency_mismatch", "unit_mismatch", "invalid_impossible_values", "contradictory_data", "cross_table_integrity"
    column: Optional[str] = None
    message: str
    impact: str
    recommendation: str
    affected_count: int = 0
    affected_percentage: float = 0.0
    examples: List[Any] = []

class ForensicReport(BaseModel):
    dataset_id: str
    dataset_name: str
    overall_status: str  # "CLEAN", "NEEDS_REVIEW", "UNSAFE_FOR_REQUESTED_ANALYSIS", "CANNOT_DETERMINE"
    summary_counts: Dict[str, Any]
    findings: List[ForensicFinding]
    recommendation: str

class AnalysisForensicsRequest(BaseModel):
    question: str
    dataset_id: Optional[str] = None
    dataset_ids: Optional[List[str]] = None

class AnalysisForensicsResponse(BaseModel):
    status: str  # "clean", "needs_review", "unsafe_for_requested_analysis", "cannot_determine"
    safe_to_analyze: bool
    question: str
    dataset_id: Optional[str] = None
    dataset_name: Optional[str] = None
    affected_columns: List[str] = []
    reason: Optional[str] = None
    warnings: List[str] = []
    findings: List[ForensicFinding] = []

class AnalysisRequest(BaseModel):
    question: str
    dataset_id: Optional[str] = None
    dataset_ids: Optional[List[str]] = None

class AnalysisResponse(BaseModel):
    status: str  # "verified", "cannot_determine", "execution_failed"
    question: str
    dataset_used: Optional[str] = None
    dataset_name: Optional[str] = None
    columns_used: List[str] = []
    operation: Optional[str] = None
    generated_code: Optional[str] = None
    execution_success: bool = False
    execution_result: Optional[Any] = None
    final_answer: Optional[str] = None
    reason: Optional[str] = None
    warnings: List[str] = []
    execution_time_ms: Optional[float] = None
    forensic_status: Optional[str] = None
    forensic_findings: List[ForensicFinding] = []

class SuggestedQuestion(BaseModel):
    id: str
    dataset_id: str
    question: str
    category: str
    is_trap: bool = False
    trap_reason: Optional[str] = None
    description: str


# ─── STAGE 4: PROOFGUARD TRUST LAYER ────────────────────────────────────────

class TrustChallenge(BaseModel):
    """A single adversarial challenge raised by the Answer Guardian."""
    id: str
    category: str            # "assumption", "scope", "data_quality", "logic", "completeness", "bias"
    severity: str            # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    challenge: str           # The Guardian's challenge question / assertion
    evidence: str            # What the Guardian found in the data or logic
    rebuttal: Optional[str] = None  # How the analyst's proof addresses this (if applicable)
    resolved: bool = False   # Whether the challenge is satisfactorily answered


class TrustDimension(BaseModel):
    """One scored dimension of the Trust Score breakdown."""
    name: str
    score: int              # 0-100
    weight: float           # Relative weight (0.0-1.0)
    reason: str


class GuardianVerdict(BaseModel):
    """The final Guardian judgment: TRUSTED / CONDITIONALLY_TRUSTED / DISPUTED / REJECTED."""
    verdict: str             # "TRUSTED", "CONDITIONALLY_TRUSTED", "DISPUTED", "REJECTED"
    trust_score: int         # 0-100 composite trust score
    trust_grade: str         # "A", "B", "C", "D", "F"
    summary: str             # Human-readable verdict explanation
    can_publish: bool        # Whether this answer is safe to act on
    conditions: List[str] = []  # Conditions under which answer can be conditionally trusted


class GuardianRequest(BaseModel):
    question: str
    dataset_id: Optional[str] = None
    dataset_ids: Optional[List[str]] = None
    # The answer being challenged
    answer_status: str                 # "verified", "cannot_determine", "execution_failed"
    final_answer: Optional[str] = None
    generated_code: Optional[str] = None
    execution_result: Optional[Any] = None
    columns_used: List[str] = []
    operation: Optional[str] = None
    forensic_status: Optional[str] = None
    forensic_findings: List[ForensicFinding] = []
    warnings: List[str] = []


class GuardianResponse(BaseModel):
    # Request metadata
    question: str
    dataset_id: Optional[str] = None
    dataset_name: Optional[str] = None
    # Trust Score breakdown
    trust_score: int
    trust_grade: str
    trust_dimensions: List[TrustDimension]
    # Challenges raised by the Guardian
    challenges: List[TrustChallenge]
    # Final verdict
    verdict: GuardianVerdict
    # Evidence chain summary
    evidence_chain: List[str]
    # Guardian recommendation
    recommendation: str
    # Proof lineage
    proof_lineage: List[Dict[str, Any]]


class ChallengeRequest(BaseModel):
    """User manually submits a counter-challenge against the Guardian's verdict."""
    question: str
    dataset_id: Optional[str] = None
    challenge_text: str
    guardian_response_summary: Optional[str] = None


class ChallengeResponse(BaseModel):
    challenge_text: str
    counter_analysis: str
    upheld: bool          # True = Guardian verdict stands, False = challenge overturns it
    updated_trust_score: Optional[int] = None
    updated_verdict: Optional[str] = None
    reasoning: str


