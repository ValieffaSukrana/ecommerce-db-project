"""Layihə üzrə ümumi parametrlər və yollar."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
SQL_DIR = BASE_DIR / "sql"
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

for _d in (RAW_DIR, PROCESSED_DIR, REPORTS_DIR, FIGURES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

DB_USER = os.getenv("POSTGRES_USER", "ecommerce")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ecommerce123")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5434")
DB_NAME = os.getenv("POSTGRES_DB", "ecommerce_db")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

RANDOM_SEED = 42
