import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
CACHE_DIR = BASE_DIR / "cache"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Processing settings
# (Interval-based analysis has been removed; keep only generic throttling knobs.)
MAX_CONCURRENT_REQUESTS = 10

# Cache settings
CACHE_EXPIRY_HOURS = 1
CACHE_FILE = CACHE_DIR / "video_cache.json"

# Statistics cache settings (prompt/output cache for per-component generation)
STATISTICS_CACHE_EXPIRY_HOURS = int(os.getenv("STATISTICS_CACHE_EXPIRY_HOURS", "0"))
STATISTICS_CACHE_FILE = CACHE_DIR / "statistics_cache.json"
