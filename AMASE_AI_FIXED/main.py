"""
main.py
─────────────────────────────────────────────────────────────────
Entry point for the CV multi-agent pipeline.

Supports:
  - analyze  : Run the full pipeline on a CV
  - train    : Feed a batch of CVs for training data collection
  - feedback : Submit a human score for a training example
"""

from __future__ import annotations

import asyncio
import json
import sys
import traceback
from pathlib import Path

from config import Config
from core.logger import configure_logging, get_logger
from orchestrator.pipeline import CVPipelineOrchestrator

configure_logging()
logger = get_logger(__name__)


async def run_analysis(cv_input: str) -> None:
    """
    Runs the full pipeline on a single CV.
    cv_input: Either a file path or raw CV text.
    """
    orchestrator = CVPipelineOrchestrator()

    try:
        # Detect if input is a file path or raw text
        path = Path(cv_input)
        if path.exists() and path.suffix.lower() in [".pdf", ".docx", ".txt"]:
            raw_text = ""
            file_path = str(path)
        else:
            raw_text = cv_input
            file_path = None

        final_state = await orchestrator.run(
            raw_cv_text=raw_text,
            cv_file_path=file_path,
            load_training=True,
        )

        # ── Print results summary ─────────────────────────────────
        print("\n" + "=" * 60)
        print(f"  SESSION: {final_state.session_id}")
        print(f"  STAGE  : {final_state.stage.value}")
        print(f"  VERSION: {final_state.version}")
        print("=" * 60)

        if final_state.agent1_output:
            a1 = final_state.agent1_output
            print(f"\n[Agent 1] CV Score       : {a1.overall_cv_score}/100")
            print(f"[Agent 1]")
    except:
        traceback.print_exc()