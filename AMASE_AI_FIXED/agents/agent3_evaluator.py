"""
agents/agent3_evaluator.py
─────────────────────────────────────────────────────────────────
Agent 3: Evaluation Agent
LLM Backbone: Anthropic Claude

Responsibilities:
  1. Read Agent1Output + Agent2Output from shared state
  2. Compute hire probability via heuristic scoring first
  3. Pass heuristic breakdown to LLM for reasoning and targets
  4. Decide if another refinement cycle is needed
  5. Write Agent3Output to shared state
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent
from config import Config
from core.logger import get_logger
from core.schemas import (
    Agent3Output,
    AgentStatus,
    HeuristicScore,
    ImprovementTarget,
)

logger = get_logger(__name__)


# ────────────────────────────────────────────────────────────────
# HEURISTIC SCORING ENGINE
# ────────────────────────────────────────────────────────────────

class HeuristicScoringEngine:
    """
    Deterministic scoring layer for Agent 3.
    Runs BEFORE the LLM to produce an evidence-based breakdown.

    Weights sum to 1.0. Adjust based on target role context.
    """

    WEIGHTS = {
        "skills_match":       0.25,
        "experience_depth":   0.25,
        "education":          0.15,
        "achievements":       0.15,
        "cv_quality":         0.10,
        "market_alignment":   0.10,
    }

    def score(self, state) -> tuple[int, List[HeuristicScore]]:
        """
        Computes a weighted hire probability score.

        Returns:
            (final_score, list of HeuristicScore breakdowns)
        """
        a1 = state.agent1_output
        a2 = state.agent2_output
        scores = []

        # ── 1. Skills match ──────────────────────────────────────
        total_skills = len(a1.parsed_cv.skills)
        technical_skills = sum(
            1 for s in a1.parsed_cv.skills if s.category == "Technical"
        )
        skills_raw = min(100, (technical_skills / max(total_skills, 1)) * 100 + 20)
        if a1.market_alignment:
            skills_raw = max(skills_raw, a1.market_alignment.competitive_score)
        scores.append(HeuristicScore(
            component="skills_match",
            raw_score=int(skills_raw),
            weight=self.WEIGHTS["skills_match"],
            weighted_score=round(skills_raw * self.WEIGHTS["skills_match"], 2),
            rationale=(
                f"{total_skills} skills found, {technical_skills} technical. "
                f"Market competitive score: "
                f"{a1.market_alignment.competitive_score if a1.market_alignment else 'N/A'}"
            ),
        ))

        # ── 2. Experience depth ──────────────────────────────────
        exp_count     = len(a1.parsed_cv.experience)
        total_months  = sum(
            e.duration_months or 0 for e in a1.parsed_cv.experience
        )
        quantified    = sum(1 for e in a1.parsed_cv.experience if e.is_quantified)
        exp_raw = min(
            100,
            (exp_count * 10)
            + (min(total_months, 60) / 60 * 40)
            + (quantified / max(exp_count, 1) * 20)
        )
        scores.append(HeuristicScore(
            component="experience_depth",
            raw_score=int(exp_raw),
            weight=self.WEIGHTS["experience_depth"],
            weighted_score=round(exp_raw * self.WEIGHTS["experience_depth"], 2),
            rationale=(
                f"{exp_count} experience entries, ~{total_months} months total. "
                f"{quantified}/{exp_count} entries have quantified achievements."
            ),
        ))

        # ── 3. Education ─────────────────────────────────────────
        edu_count = len(a1.parsed_cv.education)
        has_degree = any(
            "bachelor" in e.degree.lower() or "master" in e.degree.lower()
            or "phd" in e.degree.lower()
            for e in a1.parsed_cv.education
            if e.degree
        )
        has_gpa = any(e.gpa and e.gpa >= 3.0 for e in a1.parsed_cv.education)
        edu_raw = (
            40 * int(has_degree)
            + 20 * int(edu_count > 0)
            + 20 * int(has_gpa)
            + 10 * int(len(a1.parsed_cv.certifications) > 0)
        )
        scores.append(HeuristicScore(
            component="education",
            raw_score=int(edu_raw),
            weight=self.WEIGHTS["education"],
            weighted_score=round(edu_raw * self.WEIGHTS["education"], 2),
            rationale=(
                f"{edu_count} education entries. "
                f"Degree: {has_degree}, Good GPA: {has_gpa}, "
                f"Certifications: {len(a1.parsed_cv.certifications)}"
            ),
        ))

        # ── 4. Achievements ──────────────────────────────────────
        ach_count     = len(a1.parsed_cv.achievements)
        quantified_ach = sum(1 for a in a1.parsed_cv.achievements if a.is_quantified)
        ach_raw = min(100, (ach_count * 15) + (quantified_ach * 20))
        scores.append(HeuristicScore(
            component="achievements",
            raw_score=int(ach_raw),
            weight=self.WEIGHTS["achievements"],
            weighted_score=round(ach_raw * self.WEIGHTS["achievements"], 2),
            rationale=(
                f"{ach_count} achievements found, "
                f"{quantified_ach} are quantified."
            ),
        ))

        # ── 5. CV quality ────────────────────────────────────────
        grammar_penalty = min(30, len(a1.grammar_issues) * 5)
        format_penalty  = min(20, len(a1.format_issues) * 4)
        base_quality    = a1.overall_cv_score
        cv_quality_raw  = max(0, base_quality - grammar_penalty - format_penalty)

        # Reward if Agent 2 has applied fixes
        if a2 and a2.fixes_applied_count > 0:
            cv_quality_raw = min(100, cv_quality_raw + (a2.fixes_applied_count * 2))

        scores.append(HeuristicScore(
            component="cv_quality",
            raw_score=int(cv_quality_raw),
            weight=self.WEIGHTS["cv_quality"],
            weighted_score=round(cv_quality_raw * self.WEIGHTS["cv_quality"], 2),
            rationale=(
                f"Base CV score: {base_quality}. "
                f"Grammar penalty: -{grammar_penalty}, Format penalty: -{format_penalty}. "
                f"Agent 2 fixes applied: {a2.fixes_applied_count if a2 else 0}."
            ),
        ))

        # ── 6. Market alignment ──────────────────────────────────
        alignment_raw = (
            a1.market_alignment.competitive_score
            if a1.market_alignment else 30
        )
        scores.append(HeuristicScore(
            component="market_alignment",
            raw_score=int(alignment_raw),
            weight=self.WEIGHTS["market_alignment"],
            weighted_score=round(alignment_raw * self.WEIGHTS["market_alignment"], 2),
            rationale=(
                f"Market competitive score: {alignment_raw}. "
                f"Matched: {a1.market_alignment.matched_skills if a1.market_alignment else []}. "
                f"Missing: {a1.market_alignment.missing_skills[:5] if a1.market_alignment else []}."
            ),
        ))

        # ── Final weighted score ──────────────────────────────────
        final_score = int(sum(s.weighted_score for s in scores))
        final_score = max(0, min(100, final_score))

        return final_score, scores


# ────────────────────────────────────────────────────────────────
# AGENT 3 CLASS
# ────────────────────────────────────────────────────────────────

class Agent3Evaluator(BaseAgent):
    """
    Evaluation Agent — Anthropic Claude backbone.

    Uses a heuristic scoring engine first, then passes the breakdown
    to Claude for reasoning, improvement targets, and refinement decisions.
    """

    agent_id = "agent3"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._scorer = HeuristicScoringEngine()

    async def _run(self) -> None:
        state = self.state_manager.get()

        if state.agent1_output is None:
            raise RuntimeError("Agent 3 requires Agent 1 output.")

        # ── Step 1: Heuristic scoring ─────────────────────────────
        heuristic_score, score_breakdown = self._scorer.score(state)
        logger.info(
            "heuristic_score_computed",
            score=heuristic_score,
            components=[s.component for s in score_breakdown],
        )

        # ── Step 2: LLM reasoning + improvement targets ───────────
        system_prompt = self._build_system_prompt()
        user_content  = self._build_user_content(
            state, heuristic_score, score_breakdown
        )

        messages    = self._build_messages(system_prompt, user_content)
        llm_response = await self.llm.ainvoke(messages)

        result = self._parse_llm_response(llm_response)

        # ── Step 3: Determine if refinement is needed ────────────
        should_refine = (
            heuristic_score < Config.REFINEMENT_SCORE_THRESHOLD
            and state.refinement_cycle < state.max_refinement_cycles
        )

        # ── Step 4: Determine confidence level ───────────────────
        confidence = (
            "high" if heuristic_score >= 70
            else "medium" if heuristic_score >= 45
            else "low"
        )

        output = Agent3Output(
            status=AgentStatus.COMPLETED,
            hire_probability=heuristic_score,
            confidence_level=confidence,
            heuristic_breakdown=score_breakdown,
            reasoning=result.get("reasoning", ""),
            improvement_targets=[
                ImprovementTarget(**t)
                for t in result.get("improvement_targets", [])
            ],
            should_refine=should_refine,
            completed_at=datetime.now(),
        )

        await self.state_manager.set_agent3_output(output)
        logger.info(
            "agent3_output_saved",
            probability=output.hire_probability,
            confidence=output.confidence_level,
            should_refine=output.should_refine,
        )

    def _build_user_content(
        self,
        state,
        heuristic_score: int,
        score_breakdown: List[HeuristicScore],
    ) -> str:
        a1 = state.agent1_output
        a2 = state.agent2_output

        return json.dumps({
            "candidate": {
                "name": a1.parsed_cv.candidate_name,
                "target_role": a1.parsed_cv.target_role,
            },
            "heuristic_score": heuristic_score,
            "score_breakdown": [s.model_dump() for s in score_breakdown],
            "cv_summary": {
                "strengths_count": len(a1.strengths),
                "weaknesses_count": len(a1.weaknesses),
                "grammar_issues": len(a1.grammar_issues),
                "format_issues": len(a1.format_issues),
                "overall_cv_score": a1.overall_cv_score,
            },
            "market_alignment": (
                a1.market_alignment.model_dump()
                if a1.market_alignment else {}
            ),
            "fixes_applied": a2.fixes_applied_count if a2 else 0,
            "refinement_cycle": state.refinement_cycle,
        }, indent=2)

    def _build_system_prompt(self) -> str:
        return f"""
You are an expert HR analytics AI and career coach.

You receive a heuristic-computed hire probability score with a breakdown.
Your task: Interpret this data and produce actionable insights.

REQUIRED JSON STRUCTURE:
{{
  "reasoning": "3-5 sentence professional analysis of the candidate's hire probability",
  "improvement_targets": [
    {{
      "priority": 1,
      "area": "component name",
      "current_state": "what exists now",
      "recommended_action": "specific action to take",
      "impact_estimate": "estimated score improvement, e.g. +8 to +12 probability points"
    }}
  ]
}}

RULES:
- Output ONLY raw JSON.
- reasoning must reference the heuristic breakdown specifically.
- improvement_targets must be sorted by priority (1 = most impactful).
- impact_estimate must be realistic, not inflated.
- Minimum 3 improvement targets.
- Refinement threshold: {Config.REFINEMENT_SCORE_THRESHOLD}%
"""

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        text = response.strip()

        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text)

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error("agent3_json_parse_error", error=str(e))

            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass

            raise ValueError(f"Agent 3 response is not valid JSON. Preview: {text[:200]}")
