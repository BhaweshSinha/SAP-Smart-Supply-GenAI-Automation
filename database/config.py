"""
database/config.py

Central configuration for Phase 2 (Data Engineering & Forecasting).
Reads DB credentials from environment variables (via .env) and exposes
shared file paths used by the ETL, feature engineering, and modeling scripts.

Never hard-code real credentials here — this file only reads them.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load variables from a .env file placed at the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# PostgreSQL connection settings
# ---------------------------------------------------------------------------
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "sap_smartsupply")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")



DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ---------------------------------------------------------------------------
# Dataset paths
# ---------------------------------------------------------------------------
DATASETS_DIR = PROJECT_ROOT / "datasets"
RAW_DIR = DATASETS_DIR / "raw"
PROCESSED_DIR = DATASETS_DIR / "processed"
EXTERNAL_DIR = DATASETS_DIR / "external"

# Ensure processed dir exists (raw/external are expected to already exist)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Table load order (respects foreign-key dependencies)
# ---------------------------------------------------------------------------
TABLE_LOAD_ORDER = [
    "suppliers",
    "products",
    "warehouses",
    "inventory",
    "sales",
    "purchase_orders",
    "defects",
]

# Primary key column per table — used by the ETL upsert logic
PRIMARY_KEYS = {
    "suppliers": "supplier_id",
    "products": "product_id",
    "warehouses": "warehouse_id",
    "inventory": "inventory_id",
    "sales": "order_id",
    "purchase_orders": "po_id",
    "defects": "defect_id",
}

# Model artifact output directory
MODELS_DIR = PROJECT_ROOT / "ml" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
