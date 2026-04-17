"""
main.py
-------
AMASE — Autonomous Multi-Agent System for Employment
End-to-end CV processing pipeline.

Usage
-----
  # With a real PDF:
  python main.py --cv path/to/cv.pdf

  # With built-in demo text (no PDF needed):
  python main.py --demo
"""

import argparse
import json
import sys
import os

# Ensure the ai/ directory is on the path when running as a script
sys.path.insert(0, os.path.dirname(__file__))

from cv_parser import parse_cv, parse_cv_from_text
from feature_extractor import extract_features
from embedding import get_embedding
from matching import match_jobs
from scorer import compute_score, score_breakdown


# ---------------------------------------------------------------------------
# Demo CV (used when --demo flag is passed)
# ---------------------------------------------------------------------------

DEMO_CV_TEXT = """
John Doe
Senior Data Engineer | john.doe@email.com | LinkedIn: /in/johndoe

WORK EXPERIENCE

Senior Data Engineer — TechCorp (2020–present)
  - Built and maintained ETL pipelines using Python, Apache Spark, and dbt
  - Managed PostgreSQL and MongoDB databases; optimised slow queries by 60%
  - Deployed microservices on AWS (ECS, Lambda, S3) with Terraform and Docker
  - Introduced CI/CD workflows via GitHub Actions; reduced deployment time by 40%

Data Analyst — DataStartup (2017–2020)
  - Analysed customer behaviour using SQL, Pandas, and NumPy
  - Built dashboards in Tableau and Power BI for executive stakeholders
  - Collaborated with ML team to integrate scikit-learn models into reporting

EDUCATION

M.Sc. Computer Science — State University (2017)
B.Sc. Mathematics — City College (2015)

SKILLS
Python, SQL, PostgreSQL, MongoDB, Apache Spark, dbt, AWS, Docker,
Terraform, GitHub Actions, Pandas, NumPy, scikit-learn, Tableau, Power BI,
REST API, Microservices, Git
"""


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(cv_text: str, verbose: bool = False) -> dict:
    """
    Execute the full AMASE pipeline on raw CV text.

    Args:
        cv_text:  Plain-text content of the CV.
        verbose:  Print intermediate outputs when True.

    Returns:
        Final result dict with cv_score and top_jobs.
    """

    # ── Step 1: Feature Extraction ──────────────────────────────────────────
    print("\n[1/4] Extracting features...")
    features = extract_features(cv_text)

    if verbose:
        print(f"      Skills found   : {features['skills']}")
        print(f"      Experience     : {features['experience'][:120]}...")
        print(f"      Education      : {features['education'][:120]}...")

    # ── Step 2: Embedding Generation ────────────────────────────────────────
    print("[2/4] Generating CV embedding...")
    cv_embedding = get_embedding(cv_text)

    if verbose:
        print(f"      Embedding shape: {cv_embedding.shape}")

    # ── Step 3: Job Matching ─────────────────────────────────────────────────
    print("[3/4] Matching against job dataset...")
    top_jobs = match_jobs(cv_embedding, top_k=3)

    if verbose:
        for job in top_jobs:
            print(f"      {job['job']:35s}  sim={job['score']:.4f}")

    # ── Step 4: CV Scoring ───────────────────────────────────────────────────
    print("[4/4] Computing CV score...")
    cv_score = compute_score(features, top_jobs)

    if verbose:
        breakdown = score_breakdown(features, top_jobs)
        print(f"      Skills component      : {breakdown['skills_component']}")
        print(f"      Match component       : {breakdown['match_component']}")
        print(f"      Completeness component: {breakdown['completeness_component']}")

    return {
        "cv_score": cv_score,
        "top_jobs": top_jobs,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="AMASE — AI pipeline for CV analysis and job matching"
    )
    parser.add_argument(
        "--cv",
        type=str,
        help="Path to a PDF CV file",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run with built-in demo CV text (no PDF required)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed intermediate outputs",
    )
    args = parser.parse_args()

    # ── Load CV text ─────────────────────────────────────────────────────────
    if args.demo:
        print("Running in DEMO mode with built-in CV text.")
        cv_text = parse_cv_from_text(DEMO_CV_TEXT)

    elif args.cv:
        print(f"Parsing PDF: {args.cv}")
        cv_text = parse_cv(args.cv)
        if not cv_text:
            print("ERROR: Could not extract any text from the PDF.", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(0)

    # ── Run pipeline ─────────────────────────────────────────────────────────
    result = run_pipeline(cv_text, verbose=args.verbose)

    # ── Print final output ───────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("AMASE — PIPELINE RESULT")
    print("=" * 50)
    print(json.dumps(result, indent=2))
    print("=" * 50 + "\n")

    return result


if __name__ == "__main__":
    main()