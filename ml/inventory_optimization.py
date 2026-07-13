"""
ml/inventory_optimization.py

Phase 2 — Inventory Optimization engine.
Trains a Random Forest regressor to predict `reorder_quantity` from
datasets/processed/inventory_features.csv.

IMPORTANT: the raw dataset has no historical "units actually reordered"
field, so `reorder_quantity` is a synthetically-derived proxy target
computed in ml/feature_engineering.py as:
    max(0, reorder_point + safety_stock - available_stock)
This lets the model learn the *policy* your business rules already encode
(useful as an MVP and as a sanity baseline). Swap in a real historical
target as soon as one exists (e.g. logged from purchase_orders.csv once POs
are tied back to the inventory event that triggered them).

DATA LEAKAGE GUARD: `reorder_point`, `safety_stock`, `stock_on_hand`,
`stock_reserved`, and `available_stock` are the exact ingredients of the
target formula above. If they're included as model inputs, the model just
re-derives the arithmetic (R2=1.0, RMSE=0.0, zero real feature importance)
instead of learning anything about demand-driven reordering. They are
therefore EXCLUDED from the training features below — the model instead
has to predict reorder_quantity from product attributes and forecasted
demand alone, which is the actually useful (and honest) version of this task.

Run ml/feature_engineering.py first to generate the input file.

Usage:
    python ml/inventory_optimization.py
"""

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder

sys.path.append(str(Path(__file__).resolve().parent.parent / "database"))
from config import PROCESSED_DIR, MODELS_DIR  # noqa: E402

TARGET = "reorder_quantity"
CATEGORICAL_FEATURES = ["category", "brand", "supplier_id", "warehouse_id"]

# Excluded because they are the literal components of the target formula
# (see DATA LEAKAGE GUARD above) — keeping them out of X is what makes the
# R2 score below meaningful instead of trivially perfect.
LEAKAGE_COLS = ["reorder_point", "safety_stock", "stock_on_hand",
                "stock_reserved", "available_stock"]
DROP_COLS = ["product_id", TARGET] + LEAKAGE_COLS


def load_data() -> pd.DataFrame:
    path = PROCESSED_DIR / "inventory_features.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `python ml/feature_engineering.py` first."
        )
    return pd.read_csv(path)


def main():
    print("Loading inventory feature set ...")
    df = load_data()

    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    df_enc = df.copy()
    df_enc[CATEGORICAL_FEATURES] = encoder.fit_transform(df[CATEGORICAL_FEATURES])

    feature_cols = [c for c in df_enc.columns if c not in DROP_COLS]
    X, y = df_enc[feature_cols], df_enc[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"Train rows: {len(X_train)} | Test rows: {len(X_test)}")

    print("\nTraining RandomForestRegressor ...")
    model = RandomForestRegressor(
        n_estimators=300, max_depth=10, min_samples_leaf=2,
        random_state=42, n_jobs=-1,
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    rmse = np.sqrt(mean_squared_error(y_test, pred))
    mae = mean_absolute_error(y_test, pred)
    r2 = r2_score(y_test, pred)
    print(f"  RandomForest       RMSE={rmse:8.3f}  MAE={mae:8.3f}  R2={r2:6.3f}")

    importances = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
    print("\nFeature importances:")
    print(importances.to_string())

    artifact = {
        "model": model,
        "encoder": encoder,
        "categorical_features": CATEGORICAL_FEATURES,
        "feature_columns": feature_cols,
    }
    out_path = MODELS_DIR / "inventory_optimization_model.pkl"
    joblib.dump(artifact, out_path)
    print(f"\nSaved model artifact -> {out_path}")


if __name__ == "__main__":
    main()