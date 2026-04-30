"""
core/schemas.py
─────────────────────────────────────────────────────────────────
All Pydantic v2 schemas defining the strict data contracts
between agents, the shared state, and the training infrastructure.

These schemas act as the single source of truth for data shapes.
No agent should operate on raw dicts — always use these models.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import uuid


# ────────────────────────────────────────────────────────────────
# ENUMS
# ────────────────────────────────────────────────────────────────

class Severity(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


class AgentStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    SKIPPED   = "skipped"


class PipelineStage(str, Enum):
    INITIALIZED   = "initialized"
    COLLECTING    = "collecting"
    FIXING        = "fixing"
    EVALUATING    = "evaluating"
    REFINING      = "refining"
    COMPLETE      = "complete"
    ERROR         = "error"


# ────────────────────────────────────────────────────────────────
# CV SECTION MODELS
# ────────────────────────────────────────────────────────────────

class EducationEntry(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None
    institution_ranking: Optional[str] = None    # e.g. "Top 50 QS World Ranking"
    honors: Optional[str] = None


class ExperienceEntry(BaseModel):
    company: str
    role: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None              # "Present" or date string
    duration_months: Optional[int] = None
    responsibilities: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    is_quantified: bool = False                 # True if achievements have numbers/metrics


class SkillEntry(BaseModel):
    name: str
    category: str                               # e.g. "Technical", "Soft", "Language"
    proficiency: Optional[str] = None           # e.g. "Beginner", "Intermediate", "Expert"


class AchievementEntry(BaseModel):
    description: str
    is_quantified: bool = False
    year: Optional[int] = None


class ParsedCV(BaseModel):
    """Structured representation of a parsed CV/Resume."""
    candidate_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    target_role: str
    summary: Optional[str] = None

    education: List[EducationEntry]   = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    skills: List[SkillEntry]          = Field(default_factory=list)
    achievements: List[AchievementEntry] = Field(default_factory=list)
    certifications: List[str]         = Field(default_factory=list)
    languages: List[str]              = Field(default_factory=list)

    sections_found: List[str]    = Field(default_factory=list)
    sections_missing: List[str]  = Field(default_factory=list)


# ────────────────────────────────────────────────────────────────
# AGENT 1 SCHEMAS
# ────────────────────────────────────────────────────────────────

class StrengthItem(BaseModel):
    category: str         # "Skills" | "Experience" | "Education" | "Achievements"
    detail: str
    evidence: str         # Quote from CV


class WeaknessItem(BaseModel):
    category: str         # "Skills" | "Experience" | "Education" | "ATS"
    detail: str
    suggestion: str
    severity: Severity


class GrammarIssue(BaseModel):
    original: str         # Exact phrase from CV
    corrected: str
    explanation: str
    location: str         # Section where this appears


class FormatIssue(BaseModel):
    issue: str
    severity: Severity
    location: str


class JobMarketInsight(BaseModel):
    job_title: str
    location: str
    source: str           # "jsearch_api" | "mock_fallback"
    jobs_found: int
    in_demand_skills: List[str]
    common_requirements: List[str]
    top_hiring_employers: List[str]
    experience_range: Optional[str] = None
    fetched_at: datetime = Field(default_factory=datetime.now)


class MarketAlignment(BaseModel):
    matched_skills: List[str]
    missing_skills: List[str]
    competitive_score: int = Field(ge=0, le=100)

    @field_validator("competitive_score")
    @classmethod
    def validate_score(cls, v: int) -> int:
        return max(0, min(100, v))


class Agent1Output(BaseModel):
    """
    Complete output from Agent 1.
    Written to shared state under key: agent1_output
    """
    status: AgentStatus
    parsed_cv: ParsedCV
    strengths: List[StrengthItem]      = Field(default_factory=list)
    weaknesses: List[WeaknessItem]     = Field(default_factory=list)
    grammar_issues: List[GrammarIssue] = Field(default_factory=list)
    format_issues: List[FormatIssue]   = Field(default_factory=list)
    job_market: Optional[JobMarketInsight] = None
    market_alignment: Optional[MarketAlignment] = None
    overall_cv_score: int = Field(ge=0, le=100, default=0)
    error: Optional[str] = None
    completed_at: Optional[datetime] = None


# ────────────────────────────────────────────────────────────────
# AGENT 2 SCHEMAS
# ────────────────────────────────────────────────────────────────

class SuggestedFix(BaseModel):
    original: str
    improved: str
    rationale: str
    section: str
    fix_type: str          # "grammar" | "clarity" | "structure" | "keyword"


class Agent2Output(BaseModel):
    """
    Complete output from Agent 2.
    Written to shared state under key: agent2_output
    """
    status: AgentStatus
    suggested_fixes: List[SuggestedFix] = Field(default_factory=list)
    corrected_cv_text: Optional[str]    = None
    change_summary: Optional[str]       = None
    fixes_applied_count: int            = 0
    error: Optional[str]                = None
    completed_at: Optional[datetime]    = None


# ────────────────────────────────────────────────────────────────
# AGENT 3 SCHEMAS
# ────────────────────────────────────────────────────────────────

class HeuristicScore(BaseModel):
    component: str         # "skills_match" | "experience_depth" | "education" | etc.
    raw_score: int         # 0-100 for that component
    weight: float          # Contribution weight
    weighted_score: float
    rationale: str


class ImprovementTarget(BaseModel):
    priority: int          # 1 = highest priority
    area: str
    current_state: str
    recommended_action: str
    impact_estimate: str   # e.g. "+10 to +15 probability points"


class Agent3Output(BaseModel):
    """
    Complete output from Agent 3.
    Written to shared state under key: agent3_output
    """
    status: AgentStatus
    hire_probability: int = Field(ge=0, le=100)
    confidence_level: str                        # "low" | "medium" | "high"
    heuristic_breakdown: List[HeuristicScore]    = Field(default_factory=list)
    reasoning: str                               = ""
    improvement_targets: List[ImprovementTarget] = Field(default_factory=list)
    should_refine: bool                          = False   # Triggers Agent 2 re-run
    error: Optional[str]                         = None
    completed_at: Optional[datetime]             = None


# ────────────────────────────────────────────────────────────────
# SHARED STATE SCHEMA
# ────────────────────────────────────────────────────────────────

class AgentRunMeta(BaseModel):
    agent_id: str
    status: AgentStatus
    started_at: Optional[datetime]   = None
    completed_at: Optional[datetime] = None
    error: Optional[str]             = None
    retry_count: int                 = 0


class SharedState(BaseModel):
    """
    Centralized shared state object.
    All agents read from and write to this object.
    Versioned for auditability.
    """
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version: int    = 1
    stage: PipelineStage = PipelineStage.INITIALIZED
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Raw inputs
    raw_cv_text: str = ""
    cv_file_path: Optional[str] = None

    # Agent outputs
    agent1_output: Optional[Agent1Output] = None
    agent2_output: Optional[Agent2Output] = None
    agent3_output: Optional[Agent3Output] = None

    # Run metadata
    agent_meta: Dict[str, AgentRunMeta] = Field(default_factory=dict)

    # Refinement tracking
    refinement_cycle: int = 0
    max_refinement_cycles: int = 3
    refinement_history: List[Dict[str, Any]] = Field(default_factory=list)

    # Training labels (human-annotated feedback)
    feedback: Optional[Dict[str, Any]] = None

    def increment_version(self) -> None:
        """Bump version and update timestamp on every mutation."""
        self.version += 1
        self.updated_at = datetime.now()

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "SharedState":
        return cls.model_validate_json(json_str)


# ────────────────────────────────────────────────────────────────
# TRAINING SCHEMAS
# ────────────────────────────────────────────────────────────────

class TrainingExample(BaseModel):
    """A single labeled training example for agent fine-tuning."""
    example_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str                          # "agent1" | "agent2" | "agent3"
    raw_cv_text: str
    expected_output: Dict[str, Any]        # Ground truth for that agent
    actual_output: Optional[Dict[str, Any]] = None
    feedback_score: Optional[int] = None  # 0-100 human rating
    feedback_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class TrainingBatch(BaseModel):
    """A collection of training examples for batch processing."""
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    examples: List[TrainingExample]
    created_at: datetime = Field(default_factory=datetime.now)


# ────────────────────────────────────────────────────────────────
# MESSAGE QUEUE SCHEMAS
# ────────────────────────────────────────────────────────────────

class QueueMessage(BaseModel):
    """Envelope for all messages passed through the queue."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    event_type: str   # "agent1_done" | "agent2_done" | "agent3_done" | "refine"
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
