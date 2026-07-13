"""
database/etl_load.py

Phase 2 ETL: reads validated raw CSVs from datasets/raw/, cleans them, and
loads them into PostgreSQL in FK-safe order using an idempotent upsert
(safe to re-run — existing rows are updated, not duplicated).

Usage:
    python database/etl_load.py
    python database/etl_load.py --tables suppliers products   # load a subset

Requires: sqlalchemy, psycopg2-binary, pandas, python-dotenv
Prerequisite: run `psql -f database/schema.sql` once to create the tables.
"""

import argparse
import sys
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine

from config import DATABASE_URL, RAW_DIR, TABLE_LOAD_ORDER, PRIMARY_KEYS

DATE_COLUMNS = {
    "sales": ["order_date"],
    "purchase_orders": ["order_date", "delivery_date"],
    "defects": ["inspection_date"],
    "inventory": ["last_updated"],
}

REQUIRED_NON_NULL = {
    "products": ["product_id", "supplier_id"],
    "sales": ["order_id", "product_id", "quantity"],
    "inventory": ["inventory_id", "product_id", "warehouse_id"],
    "suppliers": ["supplier_id"],
    "purchase_orders": ["po_id", "supplier_id", "product_id"],
    "warehouses": ["warehouse_id"],
    "defects": ["defect_id", "product_id"],
}


def read_and_clean(table_name: str) -> pd.DataFrame:
    """Load a raw CSV, parse dates, and drop rows missing critical keys."""
    path = RAW_DIR / f"{table_name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Expected raw file not found: {path}")

    df = pd.read_csv(path)

    for col in DATE_COLUMNS.get(table_name, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    required = REQUIRED_NON_NULL.get(table_name, [])
    before = len(df)
    df = df.dropna(subset=[c for c in required if c in df.columns])
    dropped = before - len(df)
    if dropped:
        print(f"  [WARN] {table_name}: dropped {dropped} row(s) missing required fields {required}")

    df = df.drop_duplicates(subset=[PRIMARY_KEYS[table_name]], keep="last")
    return df


def upsert_dataframe(engine: Engine, table_name: str, df: pd.DataFrame) -> None:
    """Insert rows, updating on primary-key conflict (idempotent load)."""
    if df.empty:
        print(f"  [SKIP] {table_name}: no rows to load")
        return

    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)
    pk_col = PRIMARY_KEYS[table_name]

    records = df.where(pd.notnull(df), None).to_dict(orient="records")

    with engine.begin() as conn:
        # Chunk to keep statement size reasonable on large tables (e.g. sales)
        chunk_size = 2000
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            stmt = pg_insert(table).values(chunk)
            update_cols = {c.name: stmt.excluded[c.name] for c in table.columns if c.name != pk_col}
            stmt = stmt.on_conflict_do_update(index_elements=[pk_col], set_=update_cols)
            conn.execute(stmt)

    print(f"  [OK] {table_name}: upserted {len(records)} row(s)")


def run(tables=None):
    engine = create_engine(DATABASE_URL)
    tables_to_load = tables or TABLE_LOAD_ORDER

    # Always respect FK order even if a subset is requested
    tables_to_load = [t for t in TABLE_LOAD_ORDER if t in tables_to_load]

    print(f"Connecting to: {engine.url.render_as_string(hide_password=True)}")
    for table_name in tables_to_load:
        print(f"Loading {table_name} ...")
        df = read_and_clean(table_name)
        upsert_dataframe(engine, table_name, df)

    print("\nETL load complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load raw CSVs into PostgreSQL")
    parser.add_argument("--tables", nargs="*", help="Optional subset of tables to load")
    args = parser.parse_args()

    try:
        run(args.tables)
    except Exception as e:
        print(f"[ERROR] ETL load failed: {e}", file=sys.stderr)
        sys.exit(1)
