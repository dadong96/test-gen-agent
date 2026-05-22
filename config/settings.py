"""Global configuration loaded from environment variables and .env file."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── API ──────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6-20250514")
MAX_TOKENS_PER_ANALYSIS = int(os.getenv("MAX_TOKENS_PER_ANALYSIS", "8192"))

# ── OpenAI compatible fallback ───────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# ── Generation settings ──────────────────────────────────────────────
COVERAGE_THRESHOLD_DEFAULT = float(os.getenv("COVERAGE_THRESHOLD_DEFAULT", "0.70"))
COVERAGE_THRESHOLD_INCREMENT = float(os.getenv("COVERAGE_THRESHOLD_INCREMENT", "0.10"))
MAX_COVERAGE_ROUNDS = int(os.getenv("MAX_COVERAGE_ROUNDS", "3"))
MAX_COMPILE_FIX_ROUNDS = int(os.getenv("MAX_COMPILE_FIX_ROUNDS", "2"))
MAX_FILES_PER_RUN = int(os.getenv("MAX_FILES_PER_RUN", "50"))
CONCURRENT_AGENTS = int(os.getenv("CONCURRENT_AGENTS", "3"))

# ── Output ───────────────────────────────────────────────────────────
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output")).resolve()

# ── Logging ──────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = Path(os.getenv("LOG_FILE", "./output/test-gen.log")).resolve()

# ── Java source extensions ───────────────────────────────────────────
JAVA_EXTENSIONS = {".java"}

# ── Directories to always skip ───────────────────────────────────────
EXCLUDE_DIRS = {
    ".git", ".svn", "node_modules", "vendor", "__pycache__",
    ".venv", "venv", "env", "dist", "build", ".idea", ".vscode",
    "target", ".mvn", ".gradle",
}


def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
