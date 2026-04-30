"""
agents/agent1_collector.py
─────────────────────────────────────────────────────────────────
Agent 1: Data Collection Agent
LLM Backbone: Google Gemini

Responsibilities:
  1. Parse CV file (PDF / DOCX / TXT) into structured JSON
  2. Extract sections with regex-first, LLM-fallback hybrid approach
  3. Evaluate strengths, weaknesses, grammar, and format issues
  4. Fetch real-time job market data via JSearch API
  5. Compute market alignment and overall CV score
  6. Write Agent1Output to SharedState
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import pdfplumber
import docx

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

from agents.base_agent import BaseAgent
from config import Config
from core.logger import get_logger
from core.schemas import (
    Agent1Output,
    AgentStatus,
    AchievementEntry,
    EducationEntry,
    ExperienceEntry,
    FormatIssue,
    GrammarIssue,
    JobMarketInsight,
    MarketAlignment,
    ParsedCV,
    Severity,
    SkillEntry,
    StrengthItem,
    WeaknessItem,
)

logger = get_logger(__name__)


# ────────────────────────────────────────────────────────────────
# DETERMINISTIC EXTRACTORS (Regex / Rule-based)
# These run BEFORE the LLM to reduce token usage and latency.
# ────────────────────────────────────────────────────────────────

class DeterministicExtractor:
    """
    Rule-based extraction layer.
    Handles well-structured CV fields that don't require semantic understanding.
    """

    EMAIL_RE    = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
    PHONE_RE    = re.compile(r"(\+?\d[\d\s\-().]{7,}\d)")
    LINKEDIN_RE = re.compile(r"linkedin\.com/in/[a-zA-Z0-9\-]+", re.IGNORECASE)
    GITHUB_RE   = re.compile(r"github\.com/[a-zA-Z0-9\-]+", re.IGNORECASE)
    YEAR_RE     = re.compile(r"\b(19|20)\d{2}\b")

    SECTION_HEADERS = [
        "education", "experience", "work experience", "employment",
        "skills", "technical skills", "projects", "achievements",
        "awards", "certifications", "languages", "summary",
        "objective", "profile", "publications", "references",
        "volunteer", "extracurricular",
    ]

    EXPECTED_SECTIONS = {
        "contact information", "summary", "education",
        "experience", "skills", "achievements",
    }

    def extract_contact_info(self, text: str) -> Dict[str, Optional[str]]:
        email   = m.group() if (m := self.EMAIL_RE.search(text)) else None
        phone   = m.group().strip() if (m := self.PHONE_RE.search(text)) else None
        linkedin = m.group() if (m := self.LINKEDIN_RE.search(text)) else None
        github   = m.group() if (m := self.GITHUB_RE.search(text)) else None
        return {
            "email": email,
            "phone": phone,
            "linkedin_url": f"https://{linkedin}" if linkedin else None,
            "github_url": f"https://{github}" if github else None,
        }

    def detect_sections(self, text: str) -> tuple[List[str], List[str]]:
        """Returns (sections_found, sections_missing)."""
        lower_text = text.lower()
        found = [s for s in self.SECTION_HEADERS if s in lower_text]
        found_set = set(found)
        missing = [s for s in self.EXPECTED_SECTIONS if s not in found_set]
        return found, missing

    def extract_years(self, text: str) -> List[int]:
        return [int(y) for y in self.YEAR_RE.findall(text)]

    def basic_grammar_check(self, text: str) -> List[Dict[str, str]]:
        """
        Lightweight rule-based grammar checks.
        LLM handles the nuanced analysis; this catches obvious patterns.
        """
        issues = []
        lines  = text.split("\n")

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Check for leading lowercase in sentences
            if stripped and stripped[0].islower() and len(stripped) > 10:
                issues.append({
                    "pattern": "lowercase_sentence_start",
                    "text": stripped[:80],
                })

            # Check for double spaces
            if "  " in stripped:
                issues.append({
                    "pattern": "double_space",
                    "text": stripped[:80],
                })

            # Check for inconsistent bullet points
            if stripped.startswith("-") or stripped.startswith("*"):
                issues.append({
                    "pattern": "inconsistent_bullet",
                    "text": stripped[:80],
                })

        return issues


# ────────────────────────────────────────────────────────────────
# FILE READER
# ────────────────────────────────────────────────────────────────

def read_cv_file(file_path: str) -> str:
    """
    Reads a CV file and returns raw plain text.
    Supports: .pdf, .docx, .txt
    """
    path = Path(file_path.strip())
    if not path.exists():
        raise FileNotFoundError(f"CV file not found: '{file_path}'")

    if path.suffix.lower() == ".pdf":
        parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    parts.append(extracted)
        return "\n".join(parts).strip()

    elif path.suffix.lower() in [".docx", ".doc"]:
        doc = docx.Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    elif path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8").strip()

    else:
        raise ValueError(f"Unsupported file format: '{path.suffix}'")


# ────────────────────────────────────────────────────────────────
# JOB MARKET FETCHER
# ────────────────────────────────────────────────────────────────

def fetch_job_market(job_title: str, location: str = "Philippines") -> JobMarketInsight:
    """
    Fetches job market data from JSearch API.
    Falls back to mock data if JSEARCH_API_KEY is not set.
    """
    if not Config.JSEARCH_API_KEY:
        logger.warning("jsearch_key_missing", fallback="mock_data")
        return JobMarketInsight(
            job_title=job_title,
            location=location,
            source="mock_fallback",
            jobs_found=0,
            in_demand_skills=[
                "Python", "Machine Learning", "SQL", "Communication",
                "Data Analysis", "Cloud Computing", "Docker",
            ],
            common_requirements=[
                "Bachelor's degree in relevant field",
                "Strong analytical and problem-solving skills",
                "1-3 years of relevant experience",
            ],
            top_hiring_employers=[],
            experience_range="1-3 years entry level, 3-5 years mid-level",
        )

    try:
        from collections import Counter
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            "X-RapidAPI-Key": Config.JSEARCH_API_KEY,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }
        params = {
            "query": f"{job_title} in {location}",
            "page": "1",
            "num_pages": "2",
            "date_posted": "month",
        }
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        jobs = resp.json().get("data", [])

        SKILL_KEYWORDS = [
            "Python", "SQL", "Java", "JavaScript", "TypeScript", "React",
            "Node.js", "Machine Learning", "Deep Learning", "TensorFlow",
            "PyTorch", "NLP", "Data Analysis", "Excel", "Power BI",
            "Tableau", "AWS", "Azure", "GCP", "Docker", "Kubernetes",
            "Git", "Agile", "Scrum", "Communication", "Leadership",
            "Research", "Statistics", "Flutter", "C++", "C#",
        ]

        skill_counts: List[str] = []
        employers: List[str]    = []

        for job in jobs[:15]:
            desc = job.get("job_description", "").lower()
            employer = job.get("employer_name", "")
            if employer:
                employers.append(employer)
            for kw in SKILL_KEYWORDS:
                if kw.lower() in desc:
                    skill_counts.append(kw)

        top_skills = [s for s, _ in Counter(skill_counts).most_common(12)]

        return JobMarketInsight(
            job_title=job_title,
            location=location,
            source="jsearch_api_live",
            jobs_found=len(jobs),
            in_demand_skills=top_skills or ["No skill data extracted"],
            common_requirements=[
                "Bachelor's degree or equivalent",
                "Relevant work experience",
            ],
            top_hiring_employers=list(set(employers))[:8],
        )

    except Exception as e:
        logger.error("job_market_fetch_error", error=str(e))
        raise


# ────────────────────────────────────────────────────────────────
# AGENT 1 CLASS
# ────────────────────────────────────────────────────────────────

class Agent1DataCollector(BaseAgent):
    """
    Data Collection Agent — Google Gemini backbone.

    Pipeline:
      1. Read raw CV text from shared state (or file path)
      2. Run deterministic extraction (contact info, sections)
      3. Run LLM analysis for structured CV parsing + evaluation
      4. Fetch job market data
      5. Compute market alignment
      6. Write Agent1Output to shared state
    """

    agent_id = "agent1"

    async def _run(self) -> None:
        state = self.state_manager.get()

        # ── Step 1: Get raw CV text ──────────────────────────────
        raw_text = state.raw_cv_text

        if not raw_text and state.cv_file_path:
            logger.info("reading_cv_from_file", path=state.cv_file_path)
            raw_text = read_cv_file(state.cv_file_path)
            state.raw_cv_text = raw_text

        if not raw_text.strip():
            raise ValueError("No CV text provided. Set raw_cv_text or cv_file_path.")

        # ── Step 2: Deterministic extraction ────────────────────
        extractor = DeterministicExtractor()
        contact_info   = extractor.extract_contact_info(raw_text)
        sections_found, sections_missing = extractor.detect_sections(raw_text)
        basic_grammar  = extractor.basic_grammar_check(raw_text)

        logger.info(
            "deterministic_extraction_done",
            sections_found=len(sections_found),
            sections_missing=len(sections_missing),
            basic_grammar_flags=len(basic_grammar),
        )

        # ── Step 3: LLM analysis ─────────────────────────────────
        system_prompt = self._build_system_prompt(
            contact_info, sections_found, sections_missing, basic_grammar
        )
        user_content = f"CV TEXT:\n{raw_text}"

        messages = self._build_messages(system_prompt, user_content)
        llm_response = await self.llm.ainvoke(messages)

        # ── Step 4: Parse LLM JSON response ──────────────────────
        analysis = self._parse_llm_response(llm_response)

        # ── Step 5: Fetch job market data ────────────────────────
        target_role = analysis.get("target_role", "Software Engineer")
        try:
            job_market = fetch_job_market(target_role)
        except Exception as e:
            logger.warning("job_market_fetch_failed", error=str(e))
            job_market = None

        # ── Step 6: Compute market alignment ─────────────────────
        market_alignment = None
        if job_market:
            candidate_skills = [s.get("name", "") for s in analysis.get("skills", [])]
            matched = [
                s for s in job_market.in_demand_skills
                if s.lower() in [cs.lower() for cs in candidate_skills]
            ]
            missing = [
                s for s in job_market.in_demand_skills
                if s.lower() not in [cs.lower() for cs in candidate_skills]
            ]
            competitive_score = min(
                100, int((len(matched) / max(len(job_market.in_demand_skills), 1)) * 100)
            )
            market_alignment = MarketAlignment(
                matched_skills=matched,
                missing_skills=missing,
                competitive_score=competitive_score,
            )

        # ── Step 7: Build Agent1Output ────────────────────────────
        parsed_cv = ParsedCV(
            candidate_name=analysis.get("candidate_name", "Unknown"),
            email=contact_info.get("email"),
            phone=contact_info.get("phone"),
            linkedin_url=contact_info.get("linkedin_url"),
            github_url=contact_info.get("github_url"),
            target_role=target_role,
            summary=analysis.get("summary"),
            education=[
                EducationEntry(**e) for e in analysis.get("education", [])
            ],
            experience=[
                ExperienceEntry(**e) for e in analysis.get("experience", [])
            ],
            skills=[
                SkillEntry(**s) for s in analysis.get("skills", [])
            ],
            achievements=[
                AchievementEntry(**a) for a in analysis.get("achievements", [])
            ],
            certifications=analysis.get("certifications", []),
            languages=analysis.get("languages", []),
            sections_found=sections_found,
            sections_missing=sections_missing,
        )

        output = Agent1Output(
            status=AgentStatus.COMPLETED,
            parsed_cv=parsed_cv,
            strengths=[StrengthItem(**s) for s in analysis.get("strengths", [])],
            weaknesses=[WeaknessItem(**w) for w in analysis.get("weaknesses", [])],
            grammar_issues=[GrammarIssue(**g) for g in analysis.get("grammar_issues", [])],
            format_issues=[FormatIssue(**f) for f in analysis.get("format_issues", [])],
            job_market=job_market,
            market_alignment=market_alignment,
            overall_cv_score=analysis.get("overall_cv_score", 50),
            completed_at=datetime.now(),
        )

        await self.state_manager.set_agent1_output(output)
        logger.info(
            "agent1_output_saved",
            score=output.overall_cv_score,
            strengths=len(output.strengths),
            weaknesses=len(output.weaknesses),
            grammar_issues=len(output.grammar_issues),
        )

    def _build_system_prompt(
        self,
        contact_info: Dict,
        sections_found: List[str],
        sections_missing: List[str],
        basic_grammar: List[Dict],
    ) -> str:
        return f"""
You are a highly specialized CV Analysis AI.

Pre-extracted context (deterministic layer):
- Contact info found: {json.dumps(contact_info)}
- Sections found: {sections_found}
- Sections missing: {sections_missing}
- Basic grammar flags: {json.dumps(basic_grammar[:10])}

Your task: Perform a deep analysis of the CV and return a single valid JSON object.

REQUIRED JSON STRUCTURE:
{{
  "candidate_name": "string",
  "target_role": "string — infer from experience/objective section",
  "summary": "string or null",
  "education": [
    {{
      "institution": "string",
      "degree": "string",
      "field_of_study": "string",
      "graduation_year": integer or null,
      "gpa": float or null,
      "institution_ranking": "string or null",
      "honors": "string or null"
    }}
  ],
  "experience": [
    {{
      "company": "string",
      "role": "string",
      "start_date": "string or null",
      "end_date": "string or null",
      "duration_months": integer or null,
      "responsibilities": ["string"],
      "achievements": ["string"],
      "is_quantified": boolean
    }}
  ],
  "skills": [
    {{
      "name": "string",
      "category": "Technical | Soft | Language | Tool",
      "proficiency": "Beginner | Intermediate | Advanced | Expert or null"
    }}
  ],
  "achievements": [
    {{
      "title": "string",
      "description": "string",
      "is_quantified": boolean,
      "year": integer or null
    }}
  ],
  "certifications": ["string"],
  "languages": ["string"],
  "strengths": [
    {{
      "category": "Skills | Experience | Education | Achievements | Format",
      "detail": "string",
      "evidence": "exact quote from CV"
    }}
  ],
  "weaknesses": [
    {{
      "category": "Skills | Experience | ATS | Quantification | Format | Keywords",
      "detail": "string",
      "suggestion": "actionable improvement",
      "severity": "low | medium | high"
    }}
  ],
  "grammar_issues": [
    {{
      "original": "exact phrase from CV",
      "corrected": "corrected version",
      "explanation": "why it is wrong",
      "location": "which section"
    }}
  ],
  "format_issues": [
    {{
      "issue": "string",
      "severity": "low | medium | high",
      "location": "section name"
    }}
  ],
  "overall_cv_score": integer 0-100
}}

RULES:
- Output ONLY raw JSON. No markdown, no explanation text.
- Do NOT hallucinate facts. Only use information present in the CV.
- Quote grammar issues EXACTLY as they appear in the CV.
- overall_cv_score must be a justified integer based on quality signals.
- Minimum 3 strengths and 3 weaknesses where they exist.
"""

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parses JSON from LLM response.
        Handles cases where the model wraps JSON in markdown code fences.
        """
        text = response.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text)

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error("llm_json_parse_error", error=str(e), raw_preview=text[:300])

            # Attempt to extract JSON from partial response
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass

            raise ValueError(
                f"Agent 1 LLM response is not valid JSON. "
                f"Preview: {text[:200]}"
            )
