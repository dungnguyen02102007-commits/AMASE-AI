"""
Centralized State Object — shared across all 3 agents.
Acts as the single source of truth for the entire pipeline run.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime
import json
import uuid


@dataclass
class CVAnalysis:
    """
    Output schema from Agent 1.
    Covers portfolio content AND format/grammar/structure analysis.
    """

    # ── Portfolio: Content Analysis ───────────────────────────────────────────
    strengths: list[str]                  = field(default_factory=list)
    weaknesses: list[str]                 = field(default_factory=list)
    missing_sections: list[str]           = field(default_factory=list)
    present_sections: list[str]           = field(default_factory=list)
    key_skills_detected: list[str]        = field(default_factory=list)
    experience_summary: list[dict]        = field(default_factory=list)
    education_summary: list[dict]         = field(default_factory=list)
    certifications: list[str]             = field(default_factory=list)
    projects: list[dict]                  = field(default_factory=list)
    contact_info: dict                    = field(default_factory=dict)
    career_objective: Optional[str]       = None
    years_of_experience: Optional[float] = None

    # ── Format Analysis ───────────────────────────────────────────────────────
    format_issues: list[str]              = field(default_factory=list)
    format_goods: list[str]               = field(default_factory=list)
    ats_compatibility_issues: list[str]   = field(default_factory=list)
    ats_compatibility_goods: list[str]    = field(default_factory=list)
    layout_observations: list[str]        = field(default_factory=list)
    font_and_visual_notes: list[str]      = field(default_factory=list)
    length_assessment: Optional[str]      = None   # "too short" / "ideal" / "too long"
    page_count: Optional[int]            = None

    # ── Grammar and Language Analysis ────────────────────────────────────────
    grammar_errors: list[dict]            = field(default_factory=list)
    grammar_goods: list[str]              = field(default_factory=list)
    language_tone: Optional[str]          = None   # "professional" / "casual" / "inconsistent"
    action_verb_usage: Optional[str]      = None   # "strong" / "weak" / "absent"
    quantification_score: Optional[str]  = None   # "well-quantified" / "lacks metrics"
    passive_voice_instances: list[str]    = field(default_factory=list)

    # ── Structure Analysis ────────────────────────────────────────────────────
    section_order_issues: list[str]       = field(default_factory=list)
    section_order_goods: list[str]        = field(default_factory=list)
    bullet_point_analysis: Optional[str] = None
    consistency_issues: list[str]         = field(default_factory=list)
    consistency_goods: list[str]          = field(default_factory=list)
    date_format_issues: list[str]         = field(default_factory=list)

    # ── Benchmark Comparison ──────────────────────────────────────────────────
    benchmark_job_role: Optional[str]     = None
    benchmark_source_urls: list[str]      = field(default_factory=list)
    benchmark_gaps: list[str]             = field(default_factory=list)
    benchmark_matches: list[str]          = field(default_factory=list)

    # ── Raw Data ──────────────────────────────────────────────────────────────
    raw_cv_text: Optional[str]            = None
    agent1_reasoning: Optional[str]       = None

    def to_dict(self) -> dict:
        return {
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "missing_sections": self.missing_sections,
            "present_sections": self.present_sections,
            "key_skills_detected": self.key_skills_detected,
            "experience_summary": self.experience_summary,
            "education_summary": self.education_summary,
            "certifications": self.certifications,
            "projects": self.projects,
            "contact_info": self.contact_info,
            "career_objective": self.career_objective,
            "years_of_experience": self.years_of_experience,
            "format_issues": self.format_issues,
            "format_goods": self.format_goods,
            "ats_compatibility_issues": self.ats_compatibility_issues,
            "ats_compatibility_goods": self.ats_compatibility_goods,
            "layout_observations": self.layout_observations,
            "font_and_visual_notes": self.font_and_visual_notes,
            "length_assessment": self.length_assessment,
            "page_count": self.page_count,
            "grammar_errors": self.grammar_errors,
            "grammar_goods": self.grammar_goods,
            "language_tone": self.language_tone,
            "action_verb_usage": self.action_verb_usage,
            "quantification_score": self.quantification_score,
            "passive_voice_instances": self.passive_voice_instances,
            "section_order_issues": self.section_order_issues,
            "section_order_goods": self.section_order_goods,
            "bullet_point_analysis": self.bullet_point_analysis,
            "consistency_issues": self.consistency_issues,
            "consistency_goods": self.consistency_goods,
            "date_format_issues": self.date_format_issues,
            "benchmark_job_role": self.benchmark_job_role,
            "benchmark_source_urls": self.benchmark_source_urls,
            "benchmark_gaps": self.benchmark_gaps,
            "benchmark_matches": self.benchmark_matches,
            "raw_cv_text": self.raw_cv_text,
            "agent1_reasoning": self.agent1_reasoning,
        }


@dataclass
class ProbabilityResult:
    """Output schema from Agent 3."""

    probability_percentage: float         = 0.0
    confidence_level: Optional[str]       = None   # "high" / "medium" / "low"
    reasoning: list[dict]                 = field(default_factory=list)
    skill_gaps_vs_average: list[str]      = field(default_factory=list)
    skill_gaps_vs_job_desc: list[str]     = field(default_factory=list)
    recommended_skills: list[str]         = field(default_factory=list)
    recommended_experiences: list[str]    = field(default_factory=list)
    market_demand_insights: list[str]     = field(default_factory=list)
    job_role_fit_score: Optional[float]  = None
    agent3_reasoning: Optional[str]       = None

    def to_dict(self) -> dict:
        return {
            "probability_percentage": self.probability_percentage,
            "confidence_level": self.confidence_level,
            "reasoning": self.reasoning,
            "skill_gaps_vs_average": self.skill_gaps_vs_average,
            "skill_gaps_vs_job_desc": self.skill_gaps_vs_job_desc,
            "recommended_skills": self.recommended_skills,
            "recommended_experiences": self.recommended_experiences,
            "market_demand_insights": self.market_demand_insights,
            "job_role_fit_score": self.job_role_fit_score,
            "agent3_reasoning": self.agent3_reasoning,
        }


@dataclass
class SharedState:
    """
    The single centralized object passed between all 3 agents.
    All agents read from and write to this object exclusively.
    """

    session_id: str                                  = field(
        default_factory=lambda: str(uuid.uuid4())
    )
    created_at: str                                  = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    last_updated: str                                = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    # ── Input ─────────────────────────────────────────────────────────────────
    input_file_path: Optional[str]                  = None
    input_file_format: Optional[str]                = None   # "pdf" / "docx" / "txt"
    target_job_role: Optional[str]                  = None
    target_industry: Optional[str]                  = None
    employer_job_description: Optional[str]         = None

    # ── Agent Outputs ─────────────────────────────────────────────────────────
    cv_analysis: Optional[CVAnalysis]               = None     # Agent 1 output
    rewritten_cv_text: Optional[str]                = None     # Agent 2 output
    rewritten_cv_output_path: Optional[str]         = None     # Agent 2 saved file
    probability_result: Optional[ProbabilityResult] = None     # Agent 3 output

    # ── Pipeline Control ──────────────────────────────────────────────────────
    agent1_completed: bool                          = False
    agent2_completed: bool                          = False
    agent3_completed: bool                          = False
    errors: list[dict]                              = field(default_factory=list)
    pipeline_log: list[str]                         = field(default_factory=list)

    # ── Web Retrieval Cache ───────────────────────────────────────────────────
    benchmark_cv_data: Optional[str]                = None
    job_market_data: list[dict]                     = field(default_factory=list)

    def log(self, message: str) -> None:
        timestamp = datetime.utcnow().isoformat()
        entry = f"[{timestamp}] {message}"
        self.pipeline_log.append(entry)
        self.last_updated = timestamp
        print(entry)

    def add_error(self, agent: str, error: str, suggestion: str = "") -> None:
        self.errors.append({
            "agent": agent,
            "error": error,
            "suggestion": suggestion,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.log(f"ERROR in {agent}: {error}")

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "input_file_path": self.input_file_path,
            "input_file_format": self.input_file_format,
            "target_job_role": self.target_job_role,
            "target_industry": self.target_industry,
            "employer_job_description": self.employer_job_description,
            "cv_analysis": self.cv_analysis.to_dict() if self.cv_analysis else None,
            "rewritten_cv_text": self.rewritten_cv_text,
            "rewritten_cv_output_path": self.rewritten_cv_output_path,
            "probability_result": (
                self.probability_result.to_dict()
                if self.probability_result else None
            ),
            "agent1_completed": self.agent1_completed,
            "agent2_completed": self.agent2_completed,
            "agent3_completed": self.agent3_completed,
            "errors": self.errors,
            "pipeline_log": self.pipeline_log,
        }
