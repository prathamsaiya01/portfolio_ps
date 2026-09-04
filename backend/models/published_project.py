from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PublishedProject(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: "published-" + __import__("uuid").uuid4().hex)
    github_repo_id: str
    candidate_id: Optional[str] = None
    title: str
    description: str = ""
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    image_url: Optional[str] = None
    languages: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    category: str = "Software Project"
    featured: bool = False
    display_order: int = 0
    status: str = "PUBLISHED"
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "GITHUB_APPROVAL"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    title_manual: bool = False
    description_manual: bool = False
    live_url_manual: bool = False
    recommended_rank: Optional[int] = None
    recommended_featured: Optional[bool] = None
    ranking_score: Optional[float] = None
    diversity_score: Optional[float] = None
    similarity_penalty: Optional[float] = None
    ranking_explanation: Optional[str] = None
    manually_featured: bool = False
    manual_rank: Optional[int] = None
    ranking_updated_at: Optional[datetime] = None


class PublicPublishedProject(BaseModel):
    """Sanitized contract for public portfolio consumers."""

    model_config = ConfigDict(extra="ignore")

    github_repo_id: str
    title: str
    description: str
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    image_url: Optional[str] = None
    languages: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    category: str = "Software Project"
    featured: bool = False
    display_order: int = 0
    published_at: datetime
    updated_at: datetime
    source: str = "GITHUB_APPROVAL"
