import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
UPLOAD_DIR = BASE_DIR / "uploads"
SAMPLE_DATA_DIR = APP_DIR / "sample_data"

# Create directories if they do not exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_FILE_SIZE_MB = 25
