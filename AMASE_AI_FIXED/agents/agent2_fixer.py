"""
agents/agent2_fixer.py
─────────────────────────────────────────────────────────────────
Agent 2: CV Fixing Agent
LLM Backbone: Anthropic Claude

Responsibilities:
  1. Read Agent1Output from shared state
  2. Generate human-readable suggested fixes for all issues
  3. Produce a corrected CV text (factual integrity preserved)
  4. Write Agent2Output to shared state
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from config import Config
from core.logger import get_logger
from core.schemas import (
    Agent2Output,
    AgentStatus,
    SuggestedFix,
)

logger = get_logger(__name__)


class Agent2CVFixer(BaseAgent):
    """
    CV Fixing Agent — Anthropic Claude backbone.

    Reads all issues identified by Agent 1 and produces:
      - Granular suggested fixes per issue
      - A corrected CV text with only wording/structure improvements
    """

    agent_id = "agent2"

    async def _run(self) -> None:
        state = self.state_manager.get()

        if state.agent1_output is None:
            raise RuntimeError(
                "Agent 2 requires Agent 1 output. "
                "Run Agent 1 before Agent 2."
            )

        a1 = state.agent1_output

        # ── Build context for Claude ─────────────────────────────
        issues_payload = {
            "grammar_issues": [g.model_dump() for g in a1.grammar_issues],
            "format_issues": [f.model_dump() for f in a1.format_issues],
            "weaknesses": [w.model_dump() for w in a1.weaknesses],
            "sections_missing": a1.parsed_cv.sections_missing,
            "market_alignment": (
                a1.market_alignment.model_dump()
                if a1.market_alignment else {}
            ),
        }

        cv_context = {
            "candidate_name": a1.parsed_cv.candidate_name,
            "target_role": a1.parsed_cv.target_role,
            "raw_cv_text": state.raw_cv_text,
            "current_score": a1.overall_cv_score,
        }

        system_prompt = self._build_system_prompt()
        user_content = (
            f"CV CONTEXT:\n{json.dumps(cv_context, indent=2)}\n\n"
            f"IDENTIFIED ISSUES:\n{json.dumps(issues_payload, indent=2)}"
        )

        messages = self._build_messages(system_prompt, user_content)
        llm_response = await self.llm.ainvoke(messages)

        # ── Parse Claude's response ───────────────────────────────
        result = self._parse_llm_response(llm_response)

        # ── Build Agent2Output ────────────────────────────────────
        suggested_fixes = [
            SuggestedFix(**fix)
            for fix in result.get("suggested_fixes", [])
        ]

        output = Agent2Output(
            status=AgentStatus.COMPLETED,
            suggested_fixes=suggested_fixes,
            corrected_cv_text=result.get("corrected_cv_text"),
            change_summary=result.get("change_summary"),
            fixes_applied_count=len(suggested_fixes),
            completed_at=datetime.now(),
        )

        await self.state_manager.set_agent2_output(output)
        logger.info(
            "agent2_output_saved",
            fixes_count=output.fixes_applied_count,
            has_corrected_cv=bool(output.corrected_cv_text),
        )

    def _build_system_prompt(self) -> str:
        return """
You are an expert CV editor and career consultant AI.

Your task: Given a CV and its identified issues, produce:
1. Granular suggested fixes for every grammar, format, and weakness issue.
2. A corrected version of the CV text.

CRITICAL RULES:
- NEVER hallucinate new facts, jobs, skills, or degrees.
- ONLY improve wording, structure, clarity, and grammar.
- Preserve all factual content (dates, company names, titles, metrics).
- Do not add bullet points where none existed in the original structure.
- Fixes must be targeted, not generic advice.

REQUIRED JSON STRUCTURE:
{
  "suggested_fixes": [
    {
      "original": "exact original phrase or issue description",
      "improved": "corrected or improved version",
      "rationale": "why this change improves the CV",
      "section": "which CV section this applies to",
      "fix_type": "grammar | clarity | structure | keyword | formatting"
    }
  ],
  "corrected_cv_text": "full corrected CV as plain text, preserving original structure",
  "change_summary": "1-2 sentence summary of the key improvements made"
}

Rules:
- Output ONLY raw JSON. No markdown code fences.
- suggested_fixes must be specific — quote exact phrases from the CV.
- corrected_cv_text must be the full CV with all fixes applied.
- change_summary is a concise executive summary for the candidate.
"""

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        text = response.strip()

        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text)

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error("agent2_json_parse_error", error=str(e))

            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass

            raise ValueError(
                f"Agent 2 LLM response is not valid JSON. "
                f"Preview: {text[:200]}"
            )
