"""
run_phase2_pipeline.py  (place at project root, next to requirements.txt)

Runs the full Phase 2 pipeline end to end:
  1. Load raw CSVs into PostgreSQL        (database/etl_load.py)
  2. Build model-ready feature sets       (ml/feature_engineering.py)
  3. Train the demand forecasting model   (ml/demand_forecasting.py)
  4. Train the inventory optimization model (ml/inventory_optimization.py)

Usage:
    python run_phase2_pipeline.py                # full run, features from CSV
    python run_phase2_pipeline.py --skip-etl      # skip the DB load step
    python run_phase2_pipeline.py --feature-source db   # build features from Postgres instead of CSV
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_step(description: str, cmd: list[str]):
    print(f"\n{'=' * 70}\n{description}\n{'=' * 70}")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"[FAILED] Step exited with code {result.returncode}: {' '.join(cmd)}")
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description="Run the Phase 2 pipeline")
    parser.add_argument("--skip-etl", action="store_true", help="Skip loading CSVs into PostgreSQL")
    parser.add_argument("--feature-source", choices=["csv", "db"], default="csv",
                         help="Where feature engineering reads raw data from")
    args = parser.parse_args()

    if not args.skip_etl:
        run_step("STEP 1/4: Loading raw CSVs into PostgreSQL",
                  [sys.executable, "database/etl_load.py"])
    else:
        print("Skipping ETL load step (--skip-etl).")

    run_step("STEP 2/4: Building feature sets",
              [sys.executable, "ml/feature_engineering.py", "--source", args.feature_source])

    run_step("STEP 3/4: Training demand forecasting model",
              [sys.executable, "ml/demand_forecasting.py"])

    run_step("STEP 4/4: Training inventory optimization model",
              [sys.executable, "ml/inventory_optimization.py"])

    print("\nPhase 2 pipeline complete. Models saved under ml/models/.")


if __name__ == "__main__":
    main()
