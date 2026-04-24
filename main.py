"""
Main Entry Point — Orchestrates the full 3-agent pipeline.
Handles session persistence and training data ingestion.
"""

from __future__ import annotations
import json
import argparse
from pathlib import Path

from state.shared_state import SharedState
from agents.agent1_parser import CVParserAgent
from agents.agent2_fixer import CVFixingAgent
from agents.agent3_probability import ProbabilityCalculatorAgent
from training.trainer import CVTrainer
from memory.session_store import SessionStore


def run_pipeline(
    cv_file_path: str,
    job_role: str,
    industry: str,
    job_description: str     = "",
    resume_session: str      = "",
) -> SharedState:
    """
    Executes the full 3-agent pipeline sequentially.
    Returns the final SharedState with all results.
    """

    # ── Initialize Components ─────────────────────────────────────────────────
    store   = SessionStore()
    trainer = CVTrainer()

    # ── Initialize or Resume State ────────────────────────────────────────────
    if resume_session:
        raw = store.load_session(resume_session)
        if raw:
            print(f"[Orchestrator] Resuming session: {resume_session}")
            state = SharedState(session_id=resume_session)
        else:
            print(f"[Orchestrator] Session {resume_session} not found. Starting fresh.")
            state = SharedState()
    else:
        state = SharedState()

    # ── Populate Input ────────────────────────────────────────────────────────
    state.input_file_path            = cv_file_path
    state.target_job_role            = job_role
    state.target_industry            = industry
    state.employer_job_description   = job_description

    state.log(f"[Orchestrator] Pipeline started. Session: {state.session_id}")
    state.log(f"[Orchestrator] Input: {cv_file_path} | Role: {job_role} | Industry: {industry}")

    # ── Agent 1: Parse & Screen ───────────────────────────────────────────────
    agent1 = CVParserAgent(trainer=trainer)
    state  = agent1.run(state)

    if not state.agent1_completed:
        state.log("[Orchestrator] Agent 1 failed. Aborting pipeline.")
        store.save_session(state)
        return state

    # ── Agent 2: Fix & Rewrite ────────────────────────────────────────────────
    agent2 = CVFixingAgent(trainer=trainer)
    state  = agent2.run(state)

    if not state.agent2_completed:
        state.log("[Orchestrator] Agent 2 failed. Continuing to Agent 3.")

    # ── Agent 3: Probability ──────────────────────────────────────────────────
    agent3 = ProbabilityCalculatorAgent()
    state  = agent3.run(state)

    # ── Save Session ──────────────────────────────────────────────────────────
    store.save_session(state)
    state.log(f"[Orchestrator] Session saved: {state.session_id}")

    # ── Print Summary ─────────────────────────────────────────────────────────
    _print_summary(state)

    return state


def train_agent(
    cv_file_path: str,
    label: str,
    job_role: str,
    industry: str = "General",
    notes: str    = "",
) -> None:
    """Feed a CV example into the agent training knowledge base."""
    trainer = CVTrainer()
    doc_id  = trainer.ingest_cv(
        file_path = cv_file_path,
        label     = label,
        job_role  = job_role,
        industry  = industry,
        notes     = notes,
    )
    print(f"[Training] CV ingested successfully. Doc ID: {doc_id}")


def _print_summary(state: SharedState) -> None:
    """Prints a clean summary of all agent outputs."""
    print("\n" + "=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)
    print(f"Session ID     : {state.session_id}")
    print(f"Input File     : {state.input_file_path}")
    print(f"Job Role       : {state.target_job_role}")
    print(f"Industry       : {state.target_industry}")
    print(f"Agent 1 Done   : {state.agent1_completed}")
    print(f"Agent 2 Done   : {state.agent2_completed}")
    print(f"Agent 3 Done   : {state.agent3_completed}")

    if state.cv_analysis:
        a = state.cv_analysis
        print(f"\n-- Agent 1 Results --")
        print(f"Candidate      : {a.contact_info.get('name', 'Unknown')}")
        print(f"Years Exp      : {a.years_of_experience}")
        print(f"Skills Found   : {', '.join(a.key_skills_detected[:5])}...")
        print(f"Strengths      : {len(a.strengths)} identified")
        print(f"Weaknesses     : {len(a.weaknesses)} identified")
        print(f"Grammar Errors : {len(a.grammar_errors)} found")
        print(f"ATS Issues     : {len(a.ats_compatibility_issues)} found")

    if state.rewritten_cv_output_path:
        print(f"\n-- Agent 2 Results --")
        print(f"Rewritten CV   : {state.rewritten_cv_output_path}")

    if state.probability_result:
        p = state.probability_result
        print(f"\n-- Agent 3 Results --")
        print(f"Recruitment Probability : {p.probability_percentage:.1f}%")
        print(f"Confidence Level        : {p.confidence_level}")
        print(f"Job Role Fit Score      : {p.job_role_fit_score}")
        print(f"Top Skill Gaps          : {', '.join(p.skill_gaps_vs_job_desc[:3])}")

    if state.errors:
        print(f"\n-- Errors ({len(state.errors)}) --")
        for err in state.errors:
            print(f"  [{err['agent']}] {err['error']}")

    print("=" * 70)


# ── CLI Interface ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CV Intelligence Multi-Agent System"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Run pipeline command
    run_parser = subparsers.add_parser("run", help="Run the full CV analysis pipeline")
    run_parser.add_argument("cv_file",       help="Path to the CV file (PDF/DOCX/TXT)")
    run_parser.add_argument("job_role",      help="Target job role")
    run_parser.add_argument("industry",      help="Target industry")
    run_parser.add_argument("--job_desc",    help="Employer job description text", default="")
    run_parser.add_argument("--session",     help="Resume an existing session ID", default="")

    # Train command
    train_parser = subparsers.add_parser("train", help="Feed a CV example to the training base")
    train_parser.add_argument("cv_file",   help="Path to the CV file")
    train_parser.add_argument("label",     help="Quality label: good | bad | mediocre")
    train_parser.add_argument("job_role",  help="Job role this CV is for")
    train_parser.add_argument("--industry", default="General")
    train_parser.add_argument("--notes",    default="")

    # List sessions
    sessions_parser = subparsers.add_parser("sessions", help="List all saved sessions")

    args = parser.parse_args()

    if args.command == "run":
        run_pipeline(
            cv_file_path    = args.cv_file,
            job_role        = args.job_role,
            industry        = args.industry,
            job_description = args.job_desc,
            resume_session  = args.session,
        )

    elif args.command == "train":
        train_agent(
            cv_file_path = args.cv_file,
            label        = args.label,
            job_role     = args.job_role,
            industry     = args.industry,
            notes        = args.notes,
        )

    elif args.command == "sessions":
        store = SessionStore()
        sessions = store.list_sessions()
        if not sessions:
            print("No sessions found.")
        else:
            for s in sessions:
                print(f"  [{s['session_id']}] {s['job_role']} | {s['industry']} "
                      f"| {s['last_updated']}")

    else:
        parser.print_help()
