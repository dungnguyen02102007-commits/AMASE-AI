"""
Agent 2: CV Fixing Agent
- LLM: Claude (Anthropic)
- Reads CVAnalysis from SharedState (produced by Agent 1)
- Rewrites the CV to industry-standard, ATS-friendly format
- Preserves all portfolio facts; rephrasing allowed if intensity unchanged
- Outputs rewritten CV text + saves to original file format
"""

from __future__ import annotations
import json

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from config import (
    ANTHROPIC_API_KEY, AGENT2_MODEL, AGENT2_TEMPERATURE, ERROR_LLM_FAILURE
)
from state.shared_state import SharedState
from tools.document_writer import write_cv
from training.trainer import CVTrainer


class CVFixingAgent:

    SYSTEM_PROMPT = """
You are an elite CV/Resume Rewriting Specialist AI with expertise in:
- ATS-optimized resume writing across all industries
- Professional formatting standards (chronological, functional, hybrid)
- Industry-specific language, keywords, and phrasing
- Transforming weak, poorly written CVs into powerful, impactful documents
- Grammar, style, and professional tone correction

## YOUR STRICT RULES:
1. NEVER fabricate skills, experiences, companies, dates, or qualifications
2. You MAY rephrase — but only if the rephrasing preserves the EXACT scope and intensity
   of the original content. "Worked on ML model" -> "Developed ML classification model" is FINE
   "Worked on ML model" -> "Led company-wide AI transformation" is FORBIDDEN
3. Fix ALL grammar errors identified in the analysis
4. Fix ALL formatting issues identified in the analysis
5. Add appropriate section headers where missing
6. Reorder sections to the optimal sequence for the job role/industry
7. Strengthen bullet points with action verbs and quantification WHERE data exists
8. Make the CV ATS-friendly (no tables, no graphics, clean structure)
9. Output clean, formatted plain text that can be rendered to PDF/DOCX

## OUTPUT FORMAT:
Return the full rewritten CV as clean formatted text.
Structure it exactly like a real CV document — not as JSON, not with explanations.
Start directly with the candidate's name.
"""

    REWRITE_PROMPT_TEMPLATE = """
## YOUR TASK
Rewrite the candidate's CV based on the comprehensive analysis provided below.
Apply ALL the fixes identified. Produce a complete, polished, professional CV.

---

## ORIGINAL CV TEXT
{original_cv}

---

## ANALYSIS REPORT FROM AGENT 1
### Identified Issues to Fix:

**Format Issues:**
{format_issues}

**ATS Compatibility Issues:**
{ats_issues}

**Grammar Errors:**
{grammar_errors}

**Structure Issues:**
{structure_issues}

**Section Order Issues:**
{section_order_issues}

**Consistency Issues:**
{consistency_issues}

**Date Format Issues:**
{date_issues}

**Passive Voice to Fix:**
{passive_voice}

**Missing Sections to Add:**
{missing_sections}

**Weaknesses to Address:**
{weaknesses}

---

## WHAT TO PRESERVE (DO NOT CHANGE):
**Present Sections (keep all content):**
{present_sections}

**Key Skills Detected (keep all):**
{skills}

**Strengths to Highlight:**
{strengths}

**What is Already Good:**
Format goods: {format_goods}
Grammar goods: {grammar_goods}

---

## CANDIDATE PROFILE
Name: {name}
Job Role Target: {job_role}
Industry: {industry}
Years of Experience: {years_exp}
Action Verb Usage Quality: {action_verbs}
Quantification Quality: {quantification}

---

## TRAINING CONTEXT (Good CV Examples for Reference):
{good_examples}

---

## REWRITING INSTRUCTIONS:
1. Start with candidate name (prominent, centered)
2. Contact info on next line (email | phone | linkedin | location)
3. Professional Summary/Objective (2-3 lines, powerful, role-specific)
4. Optimal section order for {job_role} in {industry}
5. All bullet points: start with strong action verb, include metric if data exists
6. ALL grammar errors from the report must be fixed
7. Consistent date format throughout (Month YYYY - Month YYYY)
8. Clean, ATS-readable structure — no tables, no special characters
9. Ideal length: {length_target} page(s)

Now rewrite the complete CV:
"""

    def __init__(self, trainer: CVTrainer) -> None:
        self.trainer = trainer
        self.llm = ChatAnthropic(
            model       = AGENT2_MODEL,
            temperature = AGENT2_TEMPERATURE,
            api_key     = ANTHROPIC_API_KEY,
            max_tokens  = 4096,
        )

    def run(self, state: SharedState) -> SharedState:
        state.log("[Agent 2] Starting CV Fixing & Rewriting...")

        if not state.agent1_completed or not state.cv_analysis:
            state.add_error(
                "Agent2",
                "Agent 1 must complete successfully before Agent 2 can run.",
                "Ensure Agent 1 has processed the CV."
            )
            return state

        analysis = state.cv_analysis

        # ── Retrieve Training Examples ────────────────────────────────────────
        good_examples = self.trainer.get_good_cv_examples(
            job_role=state.target_job_role or "General",
            top_k=2
        )
        if not good_examples:
            good_examples = "No training examples available."

        # ── Determine Target Length ───────────────────────────────────────────
        years_exp = analysis.years_of_experience or 0
        length_target = 1 if years_exp < 5 else 2

        # ── Format Grammar Errors for Prompt ─────────────────────────────────
        grammar_errors_text = "\n".join([
            f"- [{e.get('location', 'Unknown')}] '{e.get('original', '')}': "
            f"{e.get('issue', '')}"
            for e in analysis.grammar_errors
        ]) or "None detected."

        # ── Build Prompt ──────────────────────────────────────────────────────
        prompt = self.REWRITE_PROMPT_TEMPLATE.format(
            original_cv        = analysis.raw_cv_text or "",
            format_issues      = "\n".join(f"- {x}" for x in analysis.format_issues) or "None",
            ats_issues         = "\n".join(f"- {x}" for x in analysis.ats_compatibility_issues) or "None",
            grammar_errors     = grammar_errors_text,
            structure_issues   = "\n".join(f"- {x}" for x in analysis.consistency_issues) or "None",
            section_order_issues = "\n".join(f"- {x}" for x in analysis.section_order_issues) or "None",
            consistency_issues = "\n".join(f"- {x}" for x in analysis.consistency_issues) or "None",
            date_issues        = "\n".join(f"- {x}" for x in analysis.date_format_issues) or "None",
            passive_voice      = "\n".join(f"- {x}" for x in analysis.passive_voice_instances) or "None",
            missing_sections   = "\n".join(f"- {x}" for x in analysis.missing_sections) or "None",
            weaknesses         = "\n".join(f"- {x}" for x in analysis.weaknesses) or "None",
            present_sections   = ", ".join(analysis.present_sections),
            skills             = ", ".join(analysis.key_skills_detected),
            strengths          = "\n".join(f"- {x}" for x in analysis.strengths),
            format_goods       = "\n".join(f"- {x}" for x in analysis.format_goods),
            grammar_goods      = "\n".join(f"- {x}" for x in analysis.grammar_goods),
            name               = analysis.contact_info.get("name", "Candidate"),
            job_role           = state.target_job_role or "General",
            industry           = state.target_industry or "General",
            years_exp          = years_exp,
            action_verbs       = analysis.action_verb_usage or "Unknown",
            quantification     = analysis.quantification_score or "Unknown",
            good_examples      = good_examples[:2000],
            length_target      = length_target,
        )

        state.log("[Agent 2] Sending to Claude for CV rewrite...")

        # ── Call Claude ───────────────────────────────────────────────────────
        try:
            messages = [
                SystemMessage(content=self.SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]
            response = self.llm.invoke(messages)
            rewritten_cv = response.content.strip()
            state.log(f"[Agent 2] Rewrite complete. Length: {len(rewritten_cv)} chars.")
        except Exception as e:
            state.add_error("Agent2", f"Claude API call failed: {e}", ERROR_LLM_FAILURE)
            return state

        # ── Save Rewritten CV to File ─────────────────────────────────────────
        state.rewritten_cv_text = rewritten_cv

        if state.input_file_path and state.input_file_format:
            original_path     = state.input_file_path
            file_format       = state.input_file_format
            candidate_name    = (
                analysis.contact_info.get("name", "candidate")
                .replace(" ", "_").lower()
            )
            output_path = (
                f"output/{candidate_name}_rewritten_cv.{file_format}"
            )

            try:
                final_path = write_cv(rewritten_cv, output_path, file_format)
                state.rewritten_cv_output_path = final_path
                state.log(f"[Agent 2] Rewritten CV saved to: {final_path}")
            except Exception as e:
                state.add_error(
                    "Agent2",
                    f"Failed to save rewritten CV file: {e}",
                    "The CV text was generated but could not be saved. "
                    "Check output directory permissions."
                )

        state.agent2_completed = True
        state.log("[Agent 2] CV Fixing complete.")

        return state
