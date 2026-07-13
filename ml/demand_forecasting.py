"""
ml/demand_forecasting.py

Phase 2 — Demand Forecasting MVP.
Trains a HistGradientBoostingRegressor (sklearn) to predict `future_sales`
(next-day demand per product) from datasets/processed/sales_features.csv.

Why HistGradientBoosting instead of RandomForest as the default:
Large product catalogs (10k+ products x multi-year daily grid = millions of
rows) make a deep RandomForest with hundreds of trees impractically slow on
a laptop. HistGradientBoostingRegressor is built for exactly this scale —
it trains in seconds even on 1M+ rows. RandomForest is still available as
an optional comparison for smaller datasets (see --compare-rf), and
XGBoost is used automatically if installed.

Run ml/feature_engineering.py first to generate the input file.

Usage:
    python ml/demand_forecasting.py
    python ml/demand_forecasting.py --compare-rf     # also train RandomForest (small data only)
    python ml/demand_forecasting.py --sample-frac 0.3  # train on a random 30% subsample
"""

import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OrdinalEncoder

sys.path.append(str(Path(__file__).resolve().parent.parent / "database"))
from config import PROCESSED_DIR, MODELS_DIR  # noqa: E402

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("[INFO] xgboost not installed — skipping XGBoost comparison. "
          "Install with: pip install xgboost")

TARGET = "future_sales"
CATEGORICAL_FEATURES = ["product_id", "category", "brand", "supplier_id", "customer_region"]
DROP_COLS = ["order_date", TARGET]

# Above this row count, RandomForest is skipped by default (too slow) unless
# --compare-rf is explicitly passed.
RF_ROW_LIMIT = 200_000


def load_data(sample_frac: float) -> pd.DataFrame:
    path = PROCESSED_DIR / "sales_features.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `python ml/feature_engineering.py` first."
        )
    df = pd.read_csv(path, parse_dates=["order_date"])

    if sample_frac < 1.0:
        # Sample per-product so every product keeps some representation
        # rather than randomly losing entire products.
        before = len(df)
        df = df.groupby("product_id", group_keys=False).sample(frac=sample_frac, random_state=42)
        print(f"  [INFO] Subsampled {before} -> {len(df)} rows (--sample-frac {sample_frac})")

    return df


def time_based_split(df: pd.DataFrame, test_frac: float = 0.2):
    df = df.sort_values("order_date")
    cutoff_idx = int(len(df) * (1 - test_frac))
    cutoff_date = df.iloc[cutoff_idx]["order_date"]
    train = df[df["order_date"] < cutoff_date]
    test = df[df["order_date"] >= cutoff_date]
    return train, test


def encode_categoricals(train: pd.DataFrame, test: pd.DataFrame):
    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    train_enc = train.copy()
    test_enc = test.copy()
    train_enc[CATEGORICAL_FEATURES] = encoder.fit_transform(train[CATEGORICAL_FEATURES])
    test_enc[CATEGORICAL_FEATURES] = encoder.transform(test[CATEGORICAL_FEATURES])
    return train_enc, test_enc, encoder


def evaluate(y_true, y_pred, label: str):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    print(f"  {label:<18} RMSE={rmse:8.3f}  MAE={mae:8.3f}  R2={r2:6.3f}")
    return {"model": label, "rmse": rmse, "mae": mae, "r2": r2}


def main(compare_rf: bool, sample_frac: float):
    print("Loading feature set ...")
    df = load_data(sample_frac)

    train_df, test_df = time_based_split(df)
    print(f"Train rows: {len(train_df)} | Test rows: {len(test_df)} "
          f"(split at {test_df['order_date'].min().date()})")

    train_enc, test_enc, encoder = encode_categoricals(train_df, test_df)

    feature_cols = [c for c in df.columns if c not in DROP_COLS]
    X_train, y_train = train_enc[feature_cols], train_enc[TARGET]
    X_test, y_test = test_enc[feature_cols], test_enc[TARGET]

    results = []

    print("\nTraining HistGradientBoostingRegressor (primary model) ...")
    hgb = HistGradientBoostingRegressor(
        max_iter=300, max_depth=8, learning_rate=0.05, random_state=42,
    )
    hgb.fit(X_train, y_train)
    hgb_pred = hgb.predict(X_test)
    results.append(evaluate(y_test, hgb_pred, "HistGradBoost"))
    best_model, best_name = hgb, "hist_gradient_boosting"

    if HAS_XGBOOST:
        print("Training XGBRegressor ...")
        xgb = XGBRegressor(
            n_estimators=400, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, tree_method="hist",
            random_state=42, n_jobs=-1,
        )
        xgb.fit(X_train, y_train)
        xgb_pred = xgb.predict(X_test)
        xgb_result = evaluate(y_test, xgb_pred, "XGBoost")
        results.append(xgb_result)
        if xgb_result["rmse"] < results[0]["rmse"]:
            best_model, best_name = xgb, "xgboost"

    if compare_rf:
        if len(X_train) > RF_ROW_LIMIT:
            print(f"\n[WARN] Skipping RandomForest comparison: {len(X_train)} training rows "
                  f"exceeds the {RF_ROW_LIMIT} safety limit (would be very slow). "
                  f"Use --sample-frac to shrink the dataset if you still want to compare it.")
        else:
            print("Training RandomForestRegressor (comparison) ...")
            rf = RandomForestRegressor(
                n_estimators=200, max_depth=12, min_samples_leaf=3,
                random_state=42, n_jobs=-1,
            )
            rf.fit(X_train, y_train)
            rf_pred = rf.predict(X_test)
            rf_result = evaluate(y_test, rf_pred, "RandomForest")
            results.append(rf_result)
            if rf_result["rmse"] < min(r["rmse"] for r in results if r["model"] != "RandomForest"):
                best_model, best_name = rf, "random_forest"
    elif len(X_train) <= RF_ROW_LIMIT:
        print(f"\n[TIP] Dataset is small enough ({len(X_train)} rows) to also compare "
              f"RandomForest — rerun with --compare-rf if you'd like to see it.")

    print(f"\nBest model by RMSE: {best_name}")

    importances = pd.Series(
        getattr(hgb, "feature_importances_", None) or [np.nan] * len(feature_cols),
        index=feature_cols,
    )
    if hasattr(hgb, "feature_importances_"):
        print("\nTop 10 feature importances (HistGradientBoosting):")
        print(importances.sort_values(ascending=False).head(10).to_string())

    artifact = {
        "model": best_model,
        "model_name": best_name,
        "encoder": encoder,
        "categorical_features": CATEGORICAL_FEATURES,
        "feature_columns": feature_cols,
    }
    out_path = MODELS_DIR / "demand_forecast_model.pkl"
    joblib.dump(artifact, out_path)
    print(f"\nSaved best model artifact -> {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the Phase 2 demand forecasting model")
    parser.add_argument("--compare-rf", action="store_true",
                         help="Also train RandomForest for comparison (skipped automatically on large data)")
    parser.add_argument("--sample-frac", type=float, default=1.0,
                         help="Fraction of rows to train on (0-1], stratified per product. Default: 1.0 (all rows)")
    args = parser.parse_args()
    main(args.compare_rf, args.sample_frac)