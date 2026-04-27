"""
Agent 3: Probability Calculation Agent
- LLM: Claude (Anthropic)
- Depends entirely on Agent 1 output (CVAnalysis)
- Retrieves job market data from multiple web sources
- Uses employer-provided job description if available
- Outputs single recruitment probability percentage + detailed reasoning JSON
"""

from __future__ import annotations
import json
import re

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from config import (
    ANTHROPIC_API_KEY, AGENT3_MODEL, AGENT3_TEMPERATURE, ERROR_LLM_FAILURE
)
from state.shared_state import SharedState, ProbabilityResult
from tools.web_scraper import fetch_job_market_data


class ProbabilityCalculatorAgent:

    def __init__(self) -> None:
        self.llm = ChatAnthropic(
            model=AGENT3_MODEL,
            temperature=AGENT3_TEMPERATURE,
            api_key=ANTHROPIC_API_KEY,
            max_tokens=4096,
        )

    def run(self, state: SharedState) -> SharedState:
        state.log("[Agent 3] Starting Probability Calculation...")

        if not state.agent1_completed or not state.cv_analysis:
            state.add_error(
                "Agent3",
                "Agent 1 must complete successfully before Agent 3 can run.",
                "Ensure Agent 1 has processed the CV."
            )
            return state

        analysis = state.cv_analysis

        # ── Fetch Job Market Data ─────────────────────────────────────────────
        state.log("[Agent 3] Fetching job market data from multiple sources...")
        try:
            market_data_list = fetch_job_market_data(
                job_role=state.target_job_role or "General",
                industry=state.target_industry or "General",
            )
            state.job_market_data = market_data_list

            market_data_text = "\n\n".join([
                f"[{d['title']}] ({d['source']})\n{d['content']}"
                for d in market_data_list[:8]  # Cap to control token usage
            ])
            state.log(f"[Agent 3] Market data fetched. "
                      f"Sources: {len(market_data_list)}")
        except Exception as e:
            state.log(f"[Agent 3] Market data fetch warning: {e}. Proceeding.")
            market_data_text = "Market data unavailable. Use general knowledge."

        # ── Format Education ──────────────────────────────────────────────────
        education_text = "\n".join([
            f"- {e.get('degree', '')} in {e.get('field', '')} "
            f"from {e.get('institution', '')} ({e.get('year', '')})"
            for e in analysis.education_summary
        ]) or "Not specified."

        # ── Build Prompt ──────────────────────────────────────────────────────
        prompt = self.PROBABILITY_PROMPT_TEMPLATE.format(
            job_role=state.target_job_role or "General",
            industry=state.target_industry or "General",
            strengths="\n".join(f"- {x}" for x in analysis.strengths) or "None",
            weaknesses="\n".join(f"- {x}" for x in analysis.weaknesses) or "None",
            skills=", ".join(analysis.key_skills_detected) or "None",
            years_exp=analysis.years_of_experience or "Unknown",
            education=education_text,
            certifications=", ".join(analysis.certifications) or "None",
            ats_issues="\n".join(f"- {x}" for x in analysis.ats_compatibility_issues) or "None",
            grammar_quality=analysis.language_tone or "Unknown",
            action_verbs=analysis.action_verb_usage or "Unknown",
            quantification=analysis.quantification_score or "Unknown",
            tone=analysis.language_tone or "Unknown",
            length=analysis.length_assessment or "Unknown",
            benchmark_gaps="\n".join(f"- {x}" for x in analysis.benchmark_gaps) or "None",
            benchmark_matches="\n".join(f"- {x}" for x in analysis.benchmark_matches) or "None",
            job_description=state.employer_job_description or "Not provided by employer.",
            market_data=market_data_text[:6000],
        )

        state.log("[Agent 3] Sending to Claude for probability analysis...")

        # ── Call Claude ───────────────────────────────────────────────────────
        try:
            messages = [
                SystemMessage(content=self.SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]
            response = self.llm.invoke(messages)
            raw_output = response.content
            state.log("[Agent 3] Claude response received.")
        except Exception as e:
            state.add_error("Agent3", f"Claude API call failed: {e}", ERROR_LLM_FAILURE)
            return state

        # ── Parse JSON Output ─────────────────────────────────────────────────
        try:
            json_text = _extract_json(raw_output)
            data = json.loads(json_text)
        except (json.JSONDecodeError, ValueError) as e:
            state.add_error(
                "Agent3",
                f"Failed to parse Claude JSON output: {e}",
                "The AI model returned an unexpected format. Please retry."
            )
            return state

        # ── Populate ProbabilityResult in SharedState ─────────────────────────
        result = ProbabilityResult(
            probability_percentage=float(data.get("probability_percentage", 0.0)),
            confidence_level=data.get("confidence_level"),
            reasoning=data.get("reasoning", []),
            skill_gaps_vs_average=data.get("skill_gaps_vs_average", []),
            skill_gaps_vs_job_desc=data.get("skill_gaps_vs_job_desc", []),
            recommended_skills=data.get("recommended_skills", []),
            recommended_experiences=data.get("recommended_experiences", []),
            market_demand_insights=data.get("market_demand_insights", []),
            job_role_fit_score=data.get("job_role_fit_score"),
            agent3_reasoning=data.get("agent3_reasoning", ""),
        )

        state.probability_result = result
        state.agent3_completed = True
        state.log(
            f"[Agent 3] Probability calculation complete. "
            f"Result: {result.probability_percentage:.1f}%"
        )

        return state
    def _extract_json(text: str) -> str:
        """Extract JSON block from LLM response."""
        match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
        if match:
            return match.group(1).strip()

        # Try raw JSON
        match = re.search(r"(\{[\s\S]+\})", text)
        if match:
            return match.group(1).strip()

        raise ValueError("No valid JSON found in model output.")
    SYSTEM_PROMPT = """
You are an elite Recruitment Probability Analyst AI with deep expertise in:
- Talent acquisition and HR analytics
- Job market intelligence and hiring trend analysis
- Candidate profiling and skill gap analysis
- ATS scoring systems and recruiter decision-making psychology
- Industry-specific hiring standards and benchmarks

Your role is to calculate the realistic probability that a candidate will be
recruited for a specific job role, based on their CV analysis and job market data.

## YOUR ANALYTICAL FRAMEWORK:
You consider these weighted factors:
1. Skills Match vs Job Description (30% weight)
2. Experience Level and Relevance (25% weight)
3. Education and Certifications (15% weight)
4. CV Quality and ATS Compatibility (15% weight)
5. Market Demand and Competition (10% weight)
6. Soft Skills and Professionalism Indicators (5% weight)

## REASONING STANDARDS:
- Be brutally honest. Do not inflate scores to make candidates feel good.
- Base your probability on realistic market standards, not idealistic ones.
- A 70-80% probability means a strong candidate. 50-60% is average. Below 40% is weak.
- Provide SPECIFIC, ACTIONABLE improvements — not vague advice.
- Compare to BOTH the average candidate AND the job description benchmark.

## OUTPUT: Return ONLY valid JSON. No text outside the JSON.
"""

    PROBABILITY_PROMPT_TEMPLATE = """
## TASK
Calculate the recruitment probability for this candidate applying for:
Role: {job_role}
Industry: {industry}

---

## CANDIDATE CV ANALYSIS (from Agent 1)

### Portfolio Strengths:
{strengths}

### Portfolio Weaknesses:
{weaknesses}

### Key Skills Detected:
{skills}

### Years of Experience: {years_exp}

### Education:
{education}

### Certifications:
{certifications}

### CV Quality Metrics:
- ATS Compatibility Issues: {ats_issues}
- Grammar Quality: {grammar_quality}
- Action Verb Usage: {action_verbs}
- Quantification of Achievements: {quantification}
- Language Tone: {tone}
- CV Length Assessment: {length}

### Benchmark Gaps (vs high-standard CV):
{benchmark_gaps}

### Benchmark Matches:
{benchmark_matches}

---

## EMPLOYER JOB DESCRIPTION (if provided):
{job_description}

---

## JOB MARKET DATA (from multiple sources):
{market_data}

---

## ANALYSIS INSTRUCTIONS

### STEP 1: Job Description Match Analysis
Compare the candidate's skills and experience to the employer's job description.
List matching skills and missing skills explicitly.

### STEP 2: Market Benchmark Analysis
Compare the candidate against an average candidate in the market for this role.
What does the average candidate look like? How does this candidate compare?

### STEP 3: Weighted Score Calculation
Calculate a score for each factor:
1. Skills Match vs Job Description: /30
2. Experience Level and Relevance: /25
3. Education and Certifications: /15
4. CV Quality and ATS Compatibility: /15
5. Market Demand and Competition: /10
6. Soft Skills and Professionalism: /5

Total: /100 = Probability Percentage

### STEP 4: Improvement Recommendations
What specific skills should the candidate acquire?
What experiences would strengthen their application?
What market trends should they be aware of?

---

## OUTPUT FORMAT (strict JSON only):

```json
{{
  "agent3_reasoning": "<detailed step-by-step reasoning including scores per factor>",
  "probability_percentage": <number 0-100>,
  "confidence_level": "<high | medium | low>",
  "reasoning": [
    {{
      "factor": "<factor name>",
      "score": <score>,
      "max_score": <max>,
      "explanation": "<detailed explanation>"
    }}
  ],
  "skill_gaps_vs_job_desc": ["<specific skills missing vs job description>"],
  "skill_gaps_vs_average": ["<specific skills missing vs average candidate>"],
  "recommended_skills": ["<specific skills to acquire with priority level>"],
  "recommended_experiences": ["<specific types of experience to gain>"],
  "market_demand_insights": ["<market trends and insights relevant to candidate>"],
  "job_role_fit_score": <number 0-100>
}}"""
