"""
ml/feature_engineering.py

Phase 2 feature engineering pipeline — matches the ACTUAL generated dataset
columns (confirmed from datasets/raw/*.csv), not the earlier guessed schema.

Builds two model-ready datasets:
  1. datasets/processed/sales_features.csv       -> for demand forecasting
  2. datasets/processed/inventory_features.csv   -> for inventory optimization

Usage:
    python ml/feature_engineering.py
    python ml/feature_engineering.py --source db
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent / "database"))
from config import RAW_DIR, PROCESSED_DIR, EXTERNAL_DIR, DATABASE_URL  # noqa: E402


def load_table(name: str, source: str) -> pd.DataFrame:
    if source == "db":
        from sqlalchemy import create_engine
        engine = create_engine(DATABASE_URL)
        return pd.read_sql_table(name, engine)
    return pd.read_csv(RAW_DIR / f"{name}.csv")


def load_holiday_calendar():
    """
    Optional external calendar for holidays (promotion is already a real
    column in sales.csv, so we don't need one for that).
    Drop a CSV with columns [date, is_holiday] into
    datasets/external/calendar.csv to enable this feature.
    """
    calendar_path = EXTERNAL_DIR / "calendar.csv"
    if calendar_path.exists():
        return pd.read_csv(calendar_path, parse_dates=["date"])
    print("  [INFO] No datasets/external/calendar.csv found — "
          "is_holiday will default to 0. Add this file later to enrich the model.")
    return None


# ---------------------------------------------------------------------------
# Demand forecasting feature set
# ---------------------------------------------------------------------------
def build_sales_features(source: str) -> pd.DataFrame:
    sales = load_table("sales", source)
    products = load_table("products", source)

    sales["order_date"] = pd.to_datetime(sales["order_date"])
    sales["promotion_flag"] = sales["promotion_flag"].astype(bool)

    # Aggregate transaction-level sales to daily product-level sales
    daily = (
        sales.groupby(["product_id", "order_date"])
        .agg(
            sales_quantity=("quantity", "sum"),
            revenue=("revenue", "sum"),
            is_promotion=("promotion_flag", "max"),
        )
        .reset_index()
    )

    # Complete product x date grid so gaps become explicit zero-sales days
    all_dates = pd.date_range(daily["order_date"].min(), daily["order_date"].max(), freq="D")
    all_products = daily["product_id"].unique()
    grid = pd.MultiIndex.from_product(
        [all_products, all_dates], names=["product_id", "order_date"]
    ).to_frame(index=False)

    df = grid.merge(daily, on=["product_id", "order_date"], how="left")
    df["sales_quantity"] = df["sales_quantity"].fillna(0)
    df["revenue"] = df["revenue"].fillna(0)
    df["is_promotion"] = df["is_promotion"].fillna(False).astype(int)
    df = df.sort_values(["product_id", "order_date"]).reset_index(drop=True)

    # Most frequent customer_region per product
    region_mode = (
        sales.groupby("product_id")["customer_region"]
        .agg(lambda s: s.mode().iat[0] if not s.mode().empty else "Unknown")
        .rename("customer_region")
    )
    df = df.merge(region_mode, on="product_id", how="left")

    # Calendar features
    df["year"] = df["order_date"].dt.year
    df["month"] = df["order_date"].dt.month
    df["week"] = df["order_date"].dt.isocalendar().week.astype(int)
    df["day_of_week"] = df["order_date"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["quarter"] = df["order_date"].dt.quarter

    # Optional external holiday calendar
    cal = load_holiday_calendar()
    if cal is not None:
        df = df.merge(cal, left_on="order_date", right_on="date", how="left")
        df["is_holiday"] = df["is_holiday"].fillna(0).astype(int)
        df = df.drop(columns=["date"])
    else:
        df["is_holiday"] = 0

    # Lag & rolling features (per product, time-ordered)
    grouped = df.groupby("product_id")["sales_quantity"]
    for lag in (1, 7, 14, 28):
        df[f"sales_qty_lag_{lag}"] = grouped.shift(lag)
    df["rolling_mean_7"] = grouped.shift(1).rolling(7).mean().reset_index(level=0, drop=True)
    df["rolling_mean_14"] = grouped.shift(1).rolling(14).mean().reset_index(level=0, drop=True)
    df["rolling_std_7"] = grouped.shift(1).rolling(7).std().reset_index(level=0, drop=True)

    # Product attributes as features
    df = df.merge(
        products[["product_id", "category", "brand", "unit_price", "unit_cost",
                   "lead_time_days", "supplier_id"]],
        on="product_id", how="left",
    )

    # Target: next-day demand for this product
    df["future_sales"] = df.groupby("product_id")["sales_quantity"].shift(-1)

    # Drop warm-up rows (insufficient lag history) and the last day (no target yet)
    df = df.dropna(subset=["sales_qty_lag_28", "future_sales"]).reset_index(drop=True)

    return df


# ---------------------------------------------------------------------------
# Inventory optimization feature set
# ---------------------------------------------------------------------------
def build_inventory_features(source: str, sales_features: pd.DataFrame) -> pd.DataFrame:
    inventory = load_table("inventory", source)
    products = load_table("products", source)

    # IMPORTANT: keep grain at product x warehouse (do NOT sum across
    # warehouses first). Summing available_stock across every warehouse
    # before comparing to a single company-wide reorder_point/safety_stock
    # made the "need to reorder" total almost always positive-and-large at
    # real scale (many warehouses), so the clipped target collapsed to a
    # constant 0 for every product — a degenerate target that trivially
    # gives R2=1.0 (the model just repeats the same constant) with zero
    # real predictive value. Computing reorder need per warehouse is also
    # the more realistic version of this problem: a warehouse running low
    # needs restocking regardless of stock sitting idle somewhere else.
    df = inventory.merge(
        products[["product_id", "category", "brand", "unit_price", "unit_cost",
                   "lead_time_days", "supplier_id", "reorder_point", "safety_stock"]],
        on="product_id", how="left",
    )

    # Recent average daily demand per product (last 14 observed days)
    recent_demand = (
        sales_features.sort_values("order_date")
        .groupby("product_id")
        .tail(14)
        .groupby("product_id")["sales_quantity"]
        .mean()
        .rename("avg_daily_demand")
    )
    df = df.merge(recent_demand, on="product_id", how="left")
    df["avg_daily_demand"] = df["avg_daily_demand"].fillna(0)
    df["forecasted_demand"] = df["avg_daily_demand"] * df["lead_time_days"]

    # Proxy target, now computed per product-warehouse row — see note in
    # ml/inventory_optimization.py docstring for the leakage guard on the
    # features used to train against it.
    df["reorder_quantity"] = (
        (df["reorder_point"] + df["safety_stock"] - df["available_stock"]).clip(lower=0)
    )

    feature_cols = [
        "product_id", "warehouse_id", "category", "brand", "unit_price", "unit_cost",
        "lead_time_days", "supplier_id", "reorder_point", "safety_stock", "stock_on_hand",
        "stock_reserved", "available_stock", "avg_daily_demand", "forecasted_demand",
        "reorder_quantity",
    ]
    return df[feature_cols]


def main(source: str):
    print(f"Building features from source = '{source}'")

    print("Building sales/demand features ...")
    sales_features = build_sales_features(source)
    sales_out = PROCESSED_DIR / "sales_features.csv"
    sales_features.to_csv(sales_out, index=False)
    print(f"  [OK] wrote {len(sales_features)} rows -> {sales_out}")

    print("Building inventory optimization features ...")
    inventory_features = build_inventory_features(source, sales_features)
    inv_out = PROCESSED_DIR / "inventory_features.csv"
    inventory_features.to_csv(inv_out, index=False)
    print(f"  [OK] wrote {len(inventory_features)} rows -> {inv_out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Phase 2 feature sets")
    parser.add_argument("--source", choices=["csv", "db"], default="csv",
                         help="Read raw data from local CSVs (default) or PostgreSQL")
    args = parser.parse_args()
    main(args.source)