import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM API Keys ──────────────────────────────────────────────────────────────
GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY", "")

# ── Model Names ───────────────────────────────────────────────────────────────
AGENT1_MODEL  = "gemini-2.5-pro-preview-03-25"   # Parsing & Screening
AGENT2_MODEL  = "claude-opus-4-5"                 # CV Fixing
AGENT3_MODEL  = "claude-opus-4-5"                 # Probability Calculator

# ── Temperatures ──────────────────────────────────────────────────────────────
AGENT1_TEMPERATURE = 0.2   # Low: precise extraction
AGENT2_TEMPERATURE = 0.4   # Medium: creative but controlled rewriting
AGENT3_TEMPERATURE = 0.1   # Very low: analytical reasoning

# ── Paths ─────────────────────────────────────────────────────────────────────
SESSION_DB_PATH     = "memory/sessions.db"
CHROMA_DB_PATH      = "memory/chroma_db"
TRAINING_DATA_PATH  = "training/data/"

# ── Web Search ────────────────────────────────────────────────────────────────
MAX_BENCHMARK_RESULTS   = 5
MAX_JOB_MARKET_RESULTS  = 10
JOB_MARKET_SOURCES = [
    "linkedin.com",
    "glassdoor.com",
    "indeed.com",
    "jobstreet.com",
    "seek.com",
]

# ── Error Messages ────────────────────────────────────────────────────────────
ERROR_UNSUPPORTED_FORMAT = (
    "Unable to process this file. "
    "Supported formats are: PDF, DOCX, TXT. "
    "Please try uploading your CV in one of these formats."
)
ERROR_EMPTY_FILE = (
    "The uploaded file appears to be empty or unreadable. "
    "Please check the file and try again."
)
ERROR_LLM_FAILURE = (
    "The AI model encountered an issue processing your request. "
    "Please try again. If the issue persists, contact support."
)
