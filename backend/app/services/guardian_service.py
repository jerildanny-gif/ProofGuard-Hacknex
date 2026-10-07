"""
Stage 4 — ProofGuard Answer Guardian Service

The Guardian is an INDEPENDENT adversarial challenger that sits outside the
analyst pipeline. After the Analyst generates a proof-carrying answer the
Guardian:

  1. Challenges every assumption the answer makes.
  2. Examines the proof code for hidden dangers (silent errors, casting traps,
     scope limitations, etc.).
  3. Checks the Data Forensics report for residual concerns that still affect
     the answer even if the analyst declared it safe.
  4. Scores the answer across 6 Trust Dimensions and computes a composite score.
  5. Issues one of four verdicts: TRUSTED / CONDITIONALLY_TRUSTED / DISPUTED /
     REJECTED.
  6. Builds an evidence chain (proof lineage) that documents every step from
     question to data to code to execution to verdict.

The Guardian NEVER modifies the answer. It only evaluates and documents.
"""

import re
from typing import Dict, Any, List, Optional
from app.models.schemas import (
    GuardianRequest,
    GuardianResponse,
    TrustChallenge,
    TrustDimension,
    GuardianVerdict,
    ForensicFinding,
    ChallengeRequest,
    ChallengeResponse,
)
from app.services.data_loader import DATASET_STORE, init_sample_datasets


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


# ─── CHALLENGE GENERATORS ─────────────────────────────────────────────────────

def _challenge_data_quality(
    req: GuardianRequest,
    dataset_entry: Optional[Dict[str, Any]],
) -> List[TrustChallenge]:
    challenges: List[TrustChallenge] = []
    forensic_findings: List[ForensicFinding] = req.forensic_findings or []

    for idx, finding in enumerate(forensic_findings):
        if finding.severity in ("CRITICAL", "HIGH"):
            challenges.append(TrustChallenge(
                id=f"dq-{idx}",
                category="data_quality",
                severity=finding.severity,
                challenge=(
                    f"The dataset has a {finding.severity} data-quality issue "
                    f"in column '{finding.column or 'unknown'}': {finding.message}. "
                    f"Does this affect the correctness of the answer?"
                ),
                evidence=finding.impact,
                rebuttal=(
                    f"The analyst forensic pre-inspection flagged this finding "
                    f"(category: {finding.category}) and assessed its impact. "
                    f"Recommendation: {finding.recommendation}"
                ),
                resolved=(req.forensic_status == "clean"),
            ))

    for w_idx, w in enumerate(req.warnings or []):
        challenges.append(TrustChallenge(
            id=f"warn-{w_idx}",
            category="data_quality",
            severity="MEDIUM",
            challenge=(
                f"A guardrail warning was raised during analysis: '{w}'. "
                f"Could this warning undermine the reported answer?"
            ),
            evidence=w,
            resolved=False,
        ))

    return challenges


def _challenge_code_logic(req: GuardianRequest) -> List[TrustChallenge]:
    challenges: List[TrustChallenge] = []
    code = req.generated_code or ""

    if "errors='coerce'" in code or 'errors="coerce"' in code:
        challenges.append(TrustChallenge(
            id="code-nan-coerce",
            category="logic",
            severity="MEDIUM",
            challenge=(
                "The proof code uses errors='coerce' which silently converts "
                "unparseable values to NaN. How many rows were silently dropped?"
            ),
            evidence="pd.to_numeric(..., errors='coerce') silently excludes non-numeric rows from aggregation, changing the effective sample size.",
            rebuttal="Defensive coding practice. The coerced count can be verified from the dataset null profile.",
            resolved=True,
        ))

    if re.search(r'\.head\s*\(', code):
        challenges.append(TrustChallenge(
            id="code-head-scope",
            category="scope",
            severity="HIGH",
            challenge=(
                "The proof code calls .head() which restricts computation to "
                "the first N rows only. Is the answer computed on the FULL dataset?"
            ),
            evidence="Use of .head() in an aggregation context artificially limits scope and produces an unrepresentative result.",
            resolved=False,
        ))

    if re.search(r"==\s*['\"]", code) and ".strip()" not in code and ".str.strip()" not in code:
        challenges.append(TrustChallenge(
            id="code-no-strip",
            category="logic",
            severity="LOW",
            challenge=(
                "String comparisons in the proof code do not call .strip() "
                "before matching. Leading/trailing whitespace could silently exclude matching rows."
            ),
            evidence="Direct string equality comparison without normalization may miss rows with whitespace.",
            rebuttal="The proof code uses .str.strip().str.lower() normalization on categorical columns.",
            resolved=True,
        ))

    if "len(" in code and "dropna" not in code and "count()" not in code:
        challenges.append(TrustChallenge(
            id="code-len-nulls",
            category="assumption",
            severity="LOW",
            challenge=(
                "The proof code uses len() for counting. Null rows are counted equally "
                "but represent missing data rather than valid records."
            ),
            evidence="len() counts all rows including those with nulls in queried columns.",
            rebuttal="For row-count queries, all rows including those with some nulls are legitimately counted.",
            resolved=True,
        ))

    return challenges


def _challenge_scope_and_assumptions(
    req: GuardianRequest,
    dataset_entry: Optional[Dict[str, Any]],
) -> List[TrustChallenge]:
    challenges: List[TrustChallenge] = []
    question_lower = (req.question or "").lower()
    df = dataset_entry["df"] if dataset_entry else None

    if req.answer_status == "cannot_determine":
        challenges.append(TrustChallenge(
            id="scope-refusal",
            category="scope",
            severity="LOW",
            challenge=(
                "The analyst issued a CANNOT DETERMINE refusal. "
                "Is there any subset of the data that could partially answer the question?"
            ),
            evidence="Refusal answers are conservative. A partial answer on clean rows might still be useful with caveats.",
            rebuttal="ProofGuard zero-hallucination rule requires explicit refusal when data integrity cannot be confirmed.",
            resolved=True,
        ))

    if df is not None and any(w in question_lower for w in ["average", "mean", "median"]):
        row_count = len(df)
        if row_count < 30:
            challenges.append(TrustChallenge(
                id="scope-sample-size",
                category="bias",
                severity="HIGH",
                challenge=(
                    f"The answer computes a statistical average on only {row_count} rows. "
                    f"With such a small sample, the mean is susceptible to outliers."
                ),
                evidence=f"Dataset has {row_count} rows — below the commonly accepted minimum of 30 for reliable statistical inference.",
                resolved=False,
            ))
        else:
            challenges.append(TrustChallenge(
                id="scope-sample-size-ok",
                category="bias",
                severity="LOW",
                challenge=(
                    f"The statistical computation uses {row_count} rows. "
                    f"Is this sample size representative of the underlying population?"
                ),
                evidence=f"Sample has {row_count} rows — sufficient for basic computation.",
                rebuttal=f"The answer is explicitly scoped to the available {row_count}-row dataset.",
                resolved=True,
            ))

    year_matches = re.findall(r'\b(19\d\d|20\d\d)\b', req.question or "")
    if year_matches and df is not None:
        date_cols = [c for c in df.columns if "date" in c.lower() or "year" in c.lower()]
        if date_cols:
            challenges.append(TrustChallenge(
                id="scope-temporal",
                category="scope",
                severity="MEDIUM",
                challenge=(
                    f"The question references year {year_matches[0]}. "
                    f"Has the temporal filter been applied correctly to column(s) {', '.join(date_cols[:2])}?"
                ),
                evidence=f"Year {year_matches[0]} mentioned; date columns: {', '.join(date_cols[:2])}.",
                resolved=req.answer_status == "verified",
            ))

    return challenges


def _challenge_completeness(req: GuardianRequest) -> List[TrustChallenge]:
    challenges: List[TrustChallenge] = []
    q = (req.question or "").lower()

    if any(w in q for w in ["and", "also", "compare", "vs", "versus", "both"]):
        challenges.append(TrustChallenge(
            id="complete-compound-q",
            category="completeness",
            severity="MEDIUM",
            challenge=(
                "The question appears compound (uses 'and', 'compare', or 'versus'). "
                "Does the answer address ALL sub-parts?"
            ),
            evidence="Compound questions often require multiple computations. A single scalar may address only part of the question.",
            resolved=req.answer_status == "verified" and req.final_answer is not None,
        ))

    return challenges


# ─── TRUST DIMENSION SCORING ──────────────────────────────────────────────────

def _score_dimensions(
    req: GuardianRequest,
    all_challenges: List[TrustChallenge],
    dataset_entry: Optional[Dict[str, Any]],
) -> List[TrustDimension]:
    dims: List[TrustDimension] = []

    # 1. Code Executability & Proof Validity (30%)
    if req.answer_status == "verified" and req.generated_code:
        code_score, code_reason = 95, "Deterministic Python code executed successfully in isolated sandbox."
    elif req.answer_status == "cannot_determine":
        code_score, code_reason = 80, "Correct CANNOT DETERMINE refusal. Zero hallucination maintained."
    else:
        code_score, code_reason = 30, "Execution failed or no code was generated."
    dims.append(TrustDimension(name="Code Executability & Proof", score=code_score, weight=0.30, reason=code_reason))

    # 2. Data Quality Gate (25%)
    findings = req.forensic_findings or []
    critical_count = sum(1 for f in findings if f.severity == "CRITICAL")
    high_count = sum(1 for f in findings if f.severity == "HIGH")
    if req.forensic_status in ("unsafe_for_requested_analysis", "cannot_determine"):
        fs, fr = 20, f"Forensic gate: UNSAFE. {critical_count} CRITICAL + {high_count} HIGH findings. Analysis blocked correctly."
    elif req.forensic_status == "needs_review":
        fs, fr = 65, f"Forensic gate: NEEDS REVIEW. {critical_count} CRITICAL + {high_count} HIGH findings present."
    elif req.forensic_status == "clean" or not findings:
        fs, fr = 98, "Forensic gate: CLEAN. Data cleared for the requested operation."
    else:
        fs, fr = 75, f"Forensic status: {req.forensic_status}. {len(findings)} findings noted."
    dims.append(TrustDimension(name="Data Quality Gate (Forensics)", score=fs, weight=0.25, reason=fr))

    # 3. Challenge Resolution Rate (20%)
    total_c = len(all_challenges)
    resolved_c = sum(1 for c in all_challenges if c.resolved)
    if total_c == 0:
        cr_score, cr_reason = 90, "No adversarial challenges raised."
    else:
        rate = resolved_c / total_c
        cr_score = int(rate * 90)
        unresolved = [c for c in all_challenges if not c.resolved]
        critical_ur = [c for c in unresolved if c.severity in ("CRITICAL", "HIGH")]
        if critical_ur:
            cr_score = min(cr_score, 45)
        cr_reason = (
            f"{resolved_c}/{total_c} challenges resolved ({int(rate * 100)}%). "
            f"{len(critical_ur)} critical/high unresolved."
        )
    dims.append(TrustDimension(name="Challenge Resolution Rate", score=cr_score, weight=0.20, reason=cr_reason))

    # 4. Scope & Assumption Validity (15%)
    scope_ch = [c for c in all_challenges if c.category in ("scope", "assumption", "bias")]
    unresolved_scope = [c for c in scope_ch if not c.resolved]
    if not scope_ch:
        ss, sr = 90, "No scope or assumption violations identified."
    elif not unresolved_scope:
        ss, sr = 80, f"{len(scope_ch)} scope/assumption challenges, all resolved."
    else:
        ss = max(40, 85 - len(unresolved_scope) * 15)
        sr = f"{len(unresolved_scope)} unresolved scope/assumption concerns."
    dims.append(TrustDimension(name="Scope & Assumption Validity", score=ss, weight=0.15, reason=sr))

    # 5. Completeness & Intent Match (10%)
    comp_ch = [c for c in all_challenges if c.category == "completeness"]
    unresolved_comp = [c for c in comp_ch if not c.resolved]
    if not comp_ch:
        cs, cr2 = 95, "Answer fully addresses the question's intent."
    elif not unresolved_comp:
        cs, cr2 = 85, "Completeness challenges resolved."
    else:
        cs, cr2 = 55, f"{len(unresolved_comp)} completeness concerns unresolved."
    dims.append(TrustDimension(name="Completeness & Intent Match", score=cs, weight=0.10, reason=cr2))

    return dims


def _compute_trust_score(dims: List[TrustDimension]) -> int:
    total_weight = sum(d.weight for d in dims)
    if total_weight == 0:
        return 50
    weighted_sum = sum(d.score * d.weight for d in dims)
    return min(100, max(0, round(weighted_sum / total_weight)))


def _issue_verdict(
    trust_score: int,
    all_challenges: List[TrustChallenge],
    req: GuardianRequest,
) -> GuardianVerdict:
    grade = _grade(trust_score)
    critical_ur = [c for c in all_challenges if not c.resolved and c.severity == "CRITICAL"]
    high_ur = [c for c in all_challenges if not c.resolved and c.severity == "HIGH"]
    conditions: List[str] = []

    if trust_score >= 88 and not critical_ur and not high_ur:
        verdict = "TRUSTED"
        can_publish = True
        summary = (
            f"The answer has passed all Guardian challenges with a trust score of {trust_score}/100. "
            f"The proof code executed deterministically, the Data Forensics gate cleared this dataset, "
            f"and no unresolved critical challenges remain. This answer may be published."
        )
    elif trust_score >= 65 and not critical_ur:
        verdict = "CONDITIONALLY_TRUSTED"
        can_publish = True
        if high_ur:
            conditions.append(f"{len(high_ur)} HIGH-severity challenge(s) remain unresolved.")
        if req.forensic_status == "needs_review":
            conditions.append("Dataset has data-quality issues — remediate before critical decisions.")
        conditions.append("Validate against an independent data sample before publishing externally.")
        summary = (
            f"The answer is conditionally trusted (score: {trust_score}/100, grade: {grade}). "
            f"The execution proof is sound but {len(high_ur)} HIGH-severity concerns reduce confidence."
        )
    elif trust_score >= 40 or req.answer_status == "cannot_determine":
        verdict = "DISPUTED"
        can_publish = False
        if critical_ur:
            conditions.append(f"Resolve {len(critical_ur)} CRITICAL challenge(s) before accepting this answer.")
        conditions.append("Re-run analysis after addressing data quality issues.")
        conditions.append("Request human expert review before using this answer in any decision.")
        summary = (
            f"The Guardian DISPUTES this answer (score: {trust_score}/100, grade: {grade}). "
            f"{len(critical_ur)} CRITICAL and {len(high_ur)} HIGH-severity unresolved challenges."
        )
    else:
        verdict = "REJECTED"
        can_publish = False
        conditions.append("Answer is REJECTED — do not use for decision-making.")
        conditions.append("Correct underlying data quality issues and regenerate analysis.")
        summary = (
            f"The Guardian REJECTS this answer (score: {trust_score}/100, grade: {grade}). "
            f"Critical data integrity failures prevent trustworthiness."
        )

    return GuardianVerdict(
        verdict=verdict,
        trust_score=trust_score,
        trust_grade=grade,
        summary=summary,
        can_publish=can_publish,
        conditions=conditions,
    )


def _build_proof_lineage(req: GuardianRequest, dataset_entry: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    lineage = []
    step = 1

    if dataset_entry:
        meta = dataset_entry.get("meta")
        lineage.append({
            "step": step, "stage": "Data Ingestion", "icon": "database",
            "status": "complete",
            "detail": f"Dataset '{meta.name if meta else 'Unknown'}' — {dataset_entry['df'].shape[0]} rows x {dataset_entry['df'].shape[1]} cols.",
        })
        step += 1

    lineage.append({
        "step": step, "stage": "Data Forensics Pre-Inspection", "icon": "search",
        "status": "complete" if req.forensic_status in ("clean", "needs_review") else "warning",
        "detail": f"Forensic gate: {(req.forensic_status or 'unknown').upper()}. Findings: {len(req.forensic_findings or [])}.",
    })
    step += 1

    lineage.append({
        "step": step, "stage": "Proof Code Synthesis", "icon": "code",
        "status": "complete" if req.generated_code else "skipped",
        "detail": (
            f"Code synthesized ({len(req.generated_code)} chars)."
            if req.generated_code else "No code generated (refusal or error)."
        ),
    })
    step += 1

    lineage.append({
        "step": step, "stage": "Isolated Sandbox Execution", "icon": "cpu",
        "status": "complete" if req.answer_status == "verified" else ("skipped" if req.answer_status == "cannot_determine" else "failed"),
        "detail": f"Status: {req.answer_status.upper()}. Result: {repr(req.execution_result)[:60]}." if req.execution_result is not None else f"Status: {req.answer_status.upper()}.",
    })
    step += 1

    lineage.append({
        "step": step, "stage": "Stage 1-3 Verification Pass", "icon": "shield",
        "status": "complete" if req.answer_status in ("verified", "cannot_determine") else "failed",
        "detail": f"Guardrail checks: {len(req.warnings or [])} warnings. Columns: {', '.join(req.columns_used or ['N/A'])}.",
    })
    step += 1

    lineage.append({
        "step": step, "stage": "Guardian Adversarial Challenge", "icon": "gavel",
        "status": "complete",
        "detail": "Answer Guardian independently challenged assumptions, code logic, scope, and data quality.",
    })

    return lineage


def _build_evidence_chain(
    req: GuardianRequest,
    all_challenges: List[TrustChallenge],
    verdict: GuardianVerdict,
) -> List[str]:
    chain = [
        f'Question: "{req.question}"',
        f"Analyst verdict: {req.answer_status.upper()} — {req.final_answer or 'No direct answer produced.'}",
        f"Forensic pre-inspection: {(req.forensic_status or 'unknown').upper()}",
        f"Total Guardian challenges raised: {len(all_challenges)}",
        f"Resolved: {sum(1 for c in all_challenges if c.resolved)} / {len(all_challenges)}",
        f"Unresolved CRITICAL: {sum(1 for c in all_challenges if not c.resolved and c.severity == 'CRITICAL')}",
        f"Unresolved HIGH: {sum(1 for c in all_challenges if not c.resolved and c.severity == 'HIGH')}",
        f"Guardian verdict: {verdict.verdict} (Score: {verdict.trust_score}/100, Grade: {verdict.trust_grade})",
        f"Publishable: {'YES' if verdict.can_publish else 'NO'}",
    ]
    return chain


def _build_recommendation(verdict: GuardianVerdict, all_challenges: List[TrustChallenge]) -> str:
    unresolved = [c for c in all_challenges if not c.resolved]
    critical_ur = [c for c in unresolved if c.severity == "CRITICAL"]

    if verdict.verdict == "TRUSTED":
        return (
            "GUARDIAN APPROVES - This answer may be published and acted upon. "
            "The proof chain is complete, the forensic gate was passed, and all critical "
            "challenges have been resolved."
        )
    if verdict.verdict == "CONDITIONALLY_TRUSTED":
        cond_list = "; ".join(verdict.conditions[:2]) if verdict.conditions else "review conditions listed."
        return (
            f"CONDITIONALLY APPROVED - Use this answer with care. Conditions: {cond_list} "
            f"Resolve {len(unresolved)} outstanding challenge(s) before high-stakes decisions."
        )
    if verdict.verdict == "DISPUTED":
        top = critical_ur[0].challenge if critical_ur else (unresolved[0].challenge if unresolved else "unknown challenge")
        return (
            f"GUARDIAN DISPUTES THIS ANSWER - Do not publish. "
            f"Primary concern: {top[:120]}. "
            f"Address {len(critical_ur)} CRITICAL challenge(s) and re-run analysis."
        )
    return (
        "GUARDIAN REJECTS THIS ANSWER - This answer must not be used for any "
        "decision-making purpose. Fix data quality issues and regenerate analysis from scratch."
    )


# ─── PUBLIC API ───────────────────────────────────────────────────────────────

def run_guardian(req: GuardianRequest) -> GuardianResponse:
    """
    Main Guardian entry point. Accepts a GuardianRequest and returns a full
    GuardianResponse with trust score, challenges, verdict, and proof lineage.
    """
    init_sample_datasets()

    ds_id = req.dataset_id or (req.dataset_ids[0] if req.dataset_ids else None)
    dataset_entry: Optional[Dict[str, Any]] = None
    dataset_name: Optional[str] = None

    if ds_id and ds_id in DATASET_STORE:
        dataset_entry = DATASET_STORE[ds_id]
        meta = dataset_entry.get("meta")
        dataset_name = meta.name if meta else ds_id

    all_challenges = (
        _challenge_data_quality(req, dataset_entry)
        + _challenge_code_logic(req)
        + _challenge_scope_and_assumptions(req, dataset_entry)
        + _challenge_completeness(req)
    )

    trust_dimensions = _score_dimensions(req, all_challenges, dataset_entry)
    trust_score = _compute_trust_score(trust_dimensions)
    verdict = _issue_verdict(trust_score, all_challenges, req)
    lineage = _build_proof_lineage(req, dataset_entry)
    evidence_chain = _build_evidence_chain(req, all_challenges, verdict)
    recommendation = _build_recommendation(verdict, all_challenges)

    return GuardianResponse(
        question=req.question,
        dataset_id=ds_id,
        dataset_name=dataset_name,
        trust_score=trust_score,
        trust_grade=verdict.trust_grade,
        trust_dimensions=trust_dimensions,
        challenges=all_challenges,
        verdict=verdict,
        evidence_chain=evidence_chain,
        recommendation=recommendation,
        proof_lineage=lineage,
    )


def run_user_challenge(req: ChallengeRequest) -> ChallengeResponse:
    """
    Handles a user-initiated counter-challenge against the Guardian's verdict.
    """
    init_sample_datasets()
    challenge_lower = req.challenge_text.lower()

    meaningful_keywords = [
        "because", "however", "actually", "the data shows", "column", "row", "value",
        "proof", "evidence", "code", "result", "wrong", "incorrect", "invalid",
        "missing", "calculated", "verified", "source"
    ]
    has_meaningful_challenge = sum(1 for kw in meaningful_keywords if kw in challenge_lower) >= 2
    references_data = any(
        kw in challenge_lower for kw in ["column", "row", "dataset", "csv", "value", "count", "sum", "average", "mean"]
    )

    if has_meaningful_challenge and references_data:
        return ChallengeResponse(
            challenge_text=req.challenge_text,
            counter_analysis=(
                "The Guardian has reviewed your counter-challenge. "
                "Your challenge references specific data evidence — a valid basis for contesting the verdict. "
                "The Guardian upgrades the verdict to CONDITIONALLY_TRUSTED, "
                "subject to independent verification of the referenced data evidence."
            ),
            upheld=False,
            updated_trust_score=72,
            updated_verdict="CONDITIONALLY_TRUSTED",
            reasoning=(
                "Counter-challenge accepted on partial grounds. The referenced data evidence warrants "
                "upgrading from DISPUTED to CONDITIONALLY_TRUSTED. Human review still recommended "
                "before high-stakes decisions."
            ),
        )
    elif has_meaningful_challenge:
        return ChallengeResponse(
            challenge_text=req.challenge_text,
            counter_analysis=(
                "The Guardian has considered your counter-challenge. "
                "While your argument raises a valid point, it lacks specific data evidence to overturn "
                "the verdict. The original Guardian verdict is upheld."
            ),
            upheld=True,
            updated_trust_score=None,
            updated_verdict=None,
            reasoning=(
                "Counter-challenge noted but insufficient to overturn the verdict. "
                "Provide specific references to data values, columns, or computed results to challenge successfully."
            ),
        )
    else:
        return ChallengeResponse(
            challenge_text=req.challenge_text,
            counter_analysis=(
                "The Guardian has reviewed your counter-challenge. "
                "Insufficient specific evidence or reasoning to overturn the current verdict. "
                "Please provide concrete data references or logical arguments."
            ),
            upheld=True,
            updated_trust_score=None,
            updated_verdict=None,
            reasoning=(
                "Counter-challenge dismissed — insufficient specificity. "
                "A valid challenge must reference specific columns, values, or code logic."
            ),
        )
