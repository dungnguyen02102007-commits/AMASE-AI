"""
matching.py
-----------
Matches a CV embedding against a mock job dataset using cosine similarity.

Mock job descriptions are defined here and their embeddings are precomputed
once at import time so repeated calls pay no extra cost.
"""

from __future__ import annotations

import numpy as np
from typing import TypedDict

from embedding import get_embeddings_batch


# ---------------------------------------------------------------------------
# Mock job dataset — replace with DB / API calls in production
# ---------------------------------------------------------------------------

MOCK_JOBS: list[dict[str, str]] = [
    {
        "title": "Data Analyst",
        "description": (
            "Analyse large datasets using SQL, Python, and Pandas. "
            "Build dashboards in Tableau and Power BI. "
            "Work closely with product and engineering teams to surface insights. "
            "Experience with statistical modelling and data visualisation required."
        ),
    },
    {
        "title": "Backend Developer",
        "description": (
            "Design and implement scalable REST APIs using Python (FastAPI / Django) "
            "or Node.js. Work with PostgreSQL, Redis, and Docker. "
            "Solid understanding of microservices, CI/CD pipelines, and cloud "
            "infrastructure (AWS or GCP) expected."
        ),
    },
    {
        "title": "Machine Learning Engineer",
        "description": (
            "Build and deploy ML models using PyTorch, TensorFlow, and scikit-learn. "
            "Experience with NLP, computer vision, or recommendation systems. "
            "Comfortable with MLOps tooling, feature stores, and model monitoring. "
            "Strong Python skills and familiarity with Spark or distributed computing."
        ),
    },
    {
        "title": "Frontend Developer",
        "description": (
            "Develop responsive web applications with React and TypeScript. "
            "Collaborate with designers to implement pixel-perfect UIs. "
            "Familiarity with GraphQL, REST APIs, and modern build tooling required. "
            "Performance optimisation and accessibility experience is a plus."
        ),
    },
    {
        "title": "DevOps / Platform Engineer",
        "description": (
            "Build and maintain cloud infrastructure on AWS or Azure using Terraform. "
            "Manage Kubernetes clusters, CI/CD pipelines (GitHub Actions / Jenkins), "
            "and observability stacks. Strong scripting skills (Bash, Python). "
            "Experience with Docker, Helm, and secrets management."
        ),
    },
]


class JobMatch(TypedDict):
    job: str
    score: float


# ---------------------------------------------------------------------------
# Precomputed job embeddings (runs once at import time)
# ---------------------------------------------------------------------------

_job_embeddings: list[np.ndarray] | None = None


def _get_job_embeddings() -> list[np.ndarray]:
    """Lazily precompute and cache job description embeddings."""
    global _job_embeddings
    if _job_embeddings is None:
        print("[matching] Precomputing job embeddings...")
        descriptions = [j["description"] for j in MOCK_JOBS]
        _job_embeddings = get_embeddings_batch(descriptions)
        print(f"[matching] {len(_job_embeddings)} job embeddings ready.")
    return _job_embeddings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def match_jobs(cv_embedding: np.ndarray, top_k: int = 3) -> list[JobMatch]:
    """
    Rank mock jobs by cosine similarity to the CV embedding.

    Args:
        cv_embedding: 1-D numpy array from embedding.get_embedding().
        top_k:        Number of top results to return.

    Returns:
        Sorted list of JobMatch dicts (highest score first).
    """
    job_embeddings = _get_job_embeddings()

    scores: list[JobMatch] = []
    for job, job_vec in zip(MOCK_JOBS, job_embeddings):
        sim = _cosine_similarity(cv_embedding, job_vec)
        scores.append(JobMatch(job=job["title"], score=round(float(sim), 4)))

    # Sort descending by similarity score
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:top_k]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two 1-D vectors.
    Returns a value in [-1, 1]; higher means more similar.
    """
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))