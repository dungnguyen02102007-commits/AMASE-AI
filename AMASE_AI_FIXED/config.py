"""
config.py
─────────────────────────────────────────────────────────────────
Central configuration loaded from environment variables.
All secrets are injected at runtime — never hardcoded.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── API Keys ────────────────────────────────────────────────
    GOOGLE_API_KEY: str    = os.environ.get("GOOGLE_API_KEY", "")
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    JSEARCH_API_KEY: str   = os.environ.get("JSEARCH_API_KEY", "")

    # ── LLM Models ──────────────────────────────────────────────
    GEMINI_MODEL: str  = "gemini-2.5-pro"
    CHATGPT_MODEL: str  = "gpt-4"

    # ── Redis ───────────────────────────────────────────────────
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379")
    USE_REDIS: bool = os.environ.get("USE_REDIS", "false").lower() == "true"

    # ── File Paths ───────────────────────────────────────────────
    BASE_DIR: Path = Path(__file__).parent
    SHARED_DATA_DIR: Path = BASE_DIR / "agent_shared_data"
    TRAINING_DATA_DIR: Path = BASE_DIR / "training_data"
    FEEDBACK_STORE_PATH: Path = TRAINING_DATA_DIR / "feedback_store.jsonl"

    SHARED_DATA_DIR.mkdir(exist_ok=True)
    TRAINING_DATA_DIR.mkdir(exist_ok=True)

    # ── Pipeline ─────────────────────────────────────────────────
    MAX_REFINEMENT_CYCLES: int = int(os.environ.get("MAX_REFINEMENT_CYCLES", "3"))
    REFINEMENT_SCORE_THRESHOLD: int = int(os.environ.get("REFINEMENT_SCORE_THRESHOLD", "75"))
    LLM_TEMPERATURE: float = 0.2
    MAX_RETRIES: int = 3
    RETRY_WAIT_SECONDS: int = 2

    # ── Logging ──────────────────────────────────────────────────
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    LOG_AS_JSON: bool = os.environ.get("LOG_AS_JSON", "false").lower() == "true"
