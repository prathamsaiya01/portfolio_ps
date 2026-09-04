from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CandidateRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    candidate_id: str = Field(default_factory=lambda: "candidate-" + __import__("uuid").uuid4().hex)
    github_repo_id: str = ""
    project_id: Optional[str] = None
    repository_name: str = ""
    full_name: str = ""
    owner: str = ""
    repository_url: Optional[str] = None
    github_url: Optional[str] = None
    description: Optional[str] = None
    candidate_status: str = "DISCOVERED"
    recommendation: str = "REVIEW"
    overall_score: Optional[int] = None
    analysis_version: str = "phase2-v1"
    suggested_title: Optional[str] = None
    suggested_description: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    why_it_stands_out: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    status: str = "DISCOVERED"
    portfolio_status: str = "CANDIDATE"
    ai_score: Optional[float] = None
    ai_analysis: Dict[str, Any] = Field(default_factory=dict)
    suggested_technologies: List[str] = Field(default_factory=list)
    suggested_role: Optional[str] = None
    collaborators: List[str] = Field(default_factory=list)
    date_discovered: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    date_analyzed: Optional[datetime] = None
    approval_status: Optional[str] = None
    notification_status: Optional[str] = None
    notification_sent_at: Optional[datetime] = None
    decision: Optional[str] = None
    decision_at: Optional[datetime] = None
    decision_source: Optional[str] = None
    approval_token_version: str = "v1"
    approval_token_issued_at: Optional[datetime] = None
    consumed_approval_token_ids: List[str] = Field(default_factory=list)
    review_reason: Optional[str] = None
    last_email_sent_at: Optional[datetime] = None
    email_send_count: int = 0
    email_status: str = "NOT_SENT"
    candidate_priority: Optional[int] = None
    duplicate_risk: Optional[str] = None
    portfolio_fit_score: Optional[int] = None
    similarity_flags: List[str] = Field(default_factory=list)
    differentiation_reason: Optional[str] = None
    scores: Dict[str, Any] = Field(default_factory=dict)
    publishing_status: str = "NOT_PUBLISHED"
    publishing_error: Optional[str] = None
    published_project_id: Optional[str] = None

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "CandidateRecord":
        return cls(**payload)
