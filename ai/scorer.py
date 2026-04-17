"""
scorer.py
---------
Computes a composite CV score (0–100) from extracted features and job match scores.

Scoring breakdown
-----------------
  Skills richness    : 40 pts  — how many relevant skills are present
  Top job match      : 40 pts  — best cosine similarity score scaled to 0–40
  Profile completeness: 20 pts  — whether experience and education sections exist

This is intentionally simple and transparent. Weights are easy to tune.
"""

from __future__ import annotations

from feature_extractor import CVFeatures
from matching import JobMatch


# ---------------------------------------------------------------------------
# Tuneable weights (must sum to 100)
# ---------------------------------------------------------------------------

WEIGHT_SKILLS = 40
WEIGHT_MATCH = 40
WEIGHT_COMPLETENESS = 20

# Skill count at which the skills score saturates (40/40)
MAX_SKILLS_THRESHOLD = 15


def compute_score(
    features: CVFeatures,
    match_results: list[JobMatch],
) -> int:
    """
    Compute a 0–100 CV quality / relevance score.

    Args:
        features:      Output of feature_extractor.extract_features().
        match_results: Output of matching.match_jobs() (sorted, best first).

    Returns:
        Integer score in [0, 100].
    """
    skills_score = _score_skills(features["skills"])
    match_score = _score_match(match_results)
    completeness_score = _score_completeness(features)

    total = skills_score + match_score + completeness_score

    # Clamp to [0, 100] as a safety measure
    return max(0, min(100, round(total)))


# ---------------------------------------------------------------------------
# Component scorers
# ---------------------------------------------------------------------------

def _score_skills(skills: list[str]) -> float:
    """
    More skills → higher score, capped at MAX_SKILLS_THRESHOLD.
    Score = (skill_count / threshold) * WEIGHT_SKILLS
    """
    ratio = min(len(skills) / MAX_SKILLS_THRESHOLD, 1.0)
    return ratio * WEIGHT_SKILLS


def _score_match(match_results: list[JobMatch]) -> float:
    """
    The top cosine similarity (already in [0, 1]) scales linearly to WEIGHT_MATCH.
    If no matches, score is 0.
    """
    if not match_results:
        return 0.0
    best_score = match_results[0]["score"]  # Already sorted best-first
    return best_score * WEIGHT_MATCH


def _score_completeness(features: CVFeatures) -> float:
    """
    Award points for each section that was successfully extracted.
    Full marks when both experience and education are present.
    """
    points = 0.0
    if features["experience"] and features["experience"] != "Not found":
        points += WEIGHT_COMPLETENESS * 0.6  # Experience is more important
    if features["education"] and features["education"] != "Not found":
        points += WEIGHT_COMPLETENESS * 0.4
    return points


# ---------------------------------------------------------------------------
# Score breakdown (optional helper for debugging / reporting)
# ---------------------------------------------------------------------------

def score_breakdown(
    features: CVFeatures,
    match_results: list[JobMatch],
) -> dict:
    """Return a dict showing the contribution of each scoring component."""
    return {
        "skills_component": round(_score_skills(features["skills"]), 2),
        "match_component": round(_score_match(match_results), 2),
        "completeness_component": round(_score_completeness(features), 2),
        "total": compute_score(features, match_results),
    }