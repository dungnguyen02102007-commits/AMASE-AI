"""
feature_extractor.py
--------------------
Extracts structured features from raw CV text using regex and keyword matching.
No ML required — fast, deterministic, and easy to extend.
"""

import re
from typing import TypedDict


class CVFeatures(TypedDict):
    skills: list[str]
    experience: str
    education: str


# ---------------------------------------------------------------------------
# Keyword lists — extend these to improve coverage
# ---------------------------------------------------------------------------

SKILL_KEYWORDS = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "kotlin", "swift", "ruby", "php", "scala", "r",
    # Web / frameworks
    "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
    "spring", "laravel", "rails",
    # Data / ML
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    "spark", "hadoop", "dbt",
    # Cloud / DevOps
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ci/cd",
    "github actions", "jenkins",
    # Other
    "git", "rest api", "graphql", "microservices", "agile", "scrum",
    "tableau", "power bi", "excel",
]

# Section header patterns for experience / education detection
EXPERIENCE_HEADERS = re.compile(
    r"(work experience|professional experience|employment|experience)",
    re.IGNORECASE,
)
EDUCATION_HEADERS = re.compile(
    r"(education|academic background|qualifications|degrees?)",
    re.IGNORECASE,
)


def extract_features(raw_text: str) -> CVFeatures:
    """
    Extract skills, experience summary, and education summary from raw CV text.

    Args:
        raw_text: Plain text output from cv_parser.

    Returns:
        CVFeatures dict with keys: skills, experience, education.
    """
    skills = _extract_skills(raw_text)
    experience = _extract_section(raw_text, EXPERIENCE_HEADERS)
    education = _extract_section(raw_text, EDUCATION_HEADERS)

    return CVFeatures(
        skills=skills,
        experience=experience,
        education=education,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_skills(text: str) -> list[str]:
    """
    Scan text for known skill keywords (case-insensitive, word-boundary aware).
    Returns a deduplicated, sorted list of matched skills.
    """
    text_lower = text.lower()
    found = set()

    for skill in SKILL_KEYWORDS:
        # Use word-boundary matching to avoid partial matches (e.g. "r" in "react")
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.add(skill)

    return sorted(found)


def _extract_section(text: str, header_pattern: re.Pattern) -> str:
    """
    Extract the text block that follows a recognised section header.

    Strategy:
      1. Find the first line matching the header pattern.
      2. Collect lines until the next all-caps header or end of text.
      3. Return the block joined as a single string (max 500 chars for brevity).
    """
    lines = text.splitlines()
    capture = False
    section_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            if capture:
                section_lines.append("")  # Preserve paragraph breaks
            continue

        if header_pattern.search(stripped):
            capture = True
            continue  # Skip the header line itself

        if capture:
            # Stop at the next likely section header (all-caps short line or
            # a line that matches another common header)
            if _looks_like_header(stripped) and section_lines:
                break
            section_lines.append(stripped)

    result = " ".join(l for l in section_lines if l).strip()

    # Truncate to keep the feature compact; the full text is used for embedding
    return result[:500] if result else "Not found"


def _looks_like_header(line: str) -> bool:
    """
    Heuristic: a section header is a short line (≤ 6 words) that is either
    all-caps or title-cased and contains no sentence-ending punctuation.
    """
    words = line.split()
    if len(words) > 6:
        return False
    if line.endswith((".", ",", ";", "—")):
        return False
    return line.isupper() or line.istitle()
