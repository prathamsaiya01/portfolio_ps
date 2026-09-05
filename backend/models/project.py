from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    github_repo_id: str = Field(..., description="Stable identifier from GitHub repository ID")
    owner: str = ""
    repository_name: str = ""
    full_name: str = ""
    description: Optional[str] = None
    github_url: Optional[str] = None
    homepage_url: Optional[str] = None
    readme: Optional[str] = None
    languages: List[str] = Field(default_factory=list)
    detected_technologies: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    stars: int = 0
    forks: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_commit_at: Optional[datetime] = None
    contributors: List[str] = Field(default_factory=list)
    commit_count: int = 0
    pull_request_count: int = 0
    issue_count: int = 0
    repository_visibility: str = "public"
    analyzed_at: Optional[datetime] = None
    portfolio_status: str = "DISCOVERED"
    ai_score: Optional[float] = None
    ai_analysis: Dict[str, Any] = Field(default_factory=dict)
    sync_status: str = "synced"
    last_synced_at: Optional[datetime] = None
    analysis_status: str = "NOT_ANALYZED"
    analysis_version: str = "phase2-v1"
    analysis: Dict[str, Any] = Field(default_factory=dict)
    overall_score: Optional[int] = None
    recommendation: str = "IGNORE"
    created_at_db: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at_db: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    contribution_evidence: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "ProjectRecord":
        return cls(**payload)
