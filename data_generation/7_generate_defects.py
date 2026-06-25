import pandas as pd
import random
from pathlib import Path
from datetime import datetime, timedelta

# =====================================================
# Configuration
# =====================================================

NUM_DEFECT_RECORDS = 50000

DEFECT_TYPES = [
    "Packaging Damage",
    "Quality Failure",
    "Expired Product",
    "Label Error",
    "Transit Damage",
    "Contamination",
    "Broken Item"
]

SEVERITY_LEVELS = [
    "Low",
    "Medium",
    "High",
    "Critical"
]

SEVERITY_WEIGHTS = [
    40,  # Low
    35,  # Medium
    20,  # High
    5    # Critical
]

# =====================================================
# Load Products
# =====================================================

products_file = Path("datasets/raw/products.csv")

if not products_file.exists():
    raise FileNotFoundError(
        "products.csv not found. Run 2_generate_products.py first."
    )

products_df = pd.read_csv(products_file)

product_ids = products_df["product_id"].tolist()

# Product -> Supplier mapping
product_supplier_map = products_df.set_index(
    "product_id"
)["supplier_id"].to_dict()

# =====================================================
# Load Warehouses
# =====================================================

warehouses_file = Path("datasets/raw/warehouses.csv")

if not warehouses_file.exists():
    raise FileNotFoundError(
        "warehouses.csv not found. Run 3_generate_warehouses.py first."
    )

warehouses_df = pd.read_csv(warehouses_file)

warehouse_ids = warehouses_df["warehouse_id"].tolist()

# =====================================================
# Date Range
# =====================================================

start_date = datetime(2023, 1, 1)
end_date = datetime(2026, 6, 30)

date_range_days = (end_date - start_date).days

# =====================================================
# Generate Defects
# =====================================================

defect_records = []

for i in range(1, NUM_DEFECT_RECORDS + 1):

    product_id = random.choice(product_ids)

    supplier_id = product_supplier_map[product_id]

    warehouse_id = random.choice(warehouse_ids)

    defect_type = random.choice(DEFECT_TYPES)

    defect_count = random.randint(1, 500)

    inspection_date = (
        start_date +
        timedelta(days=random.randint(0, date_range_days))
    ).strftime("%Y-%m-%d")

    severity = random.choices(
        SEVERITY_LEVELS,
        weights=SEVERITY_WEIGHTS,
        k=1
    )[0]

    defect_records.append({
        "defect_id": f"DEF{i:06d}",
        "product_id": product_id,
        "supplier_id": supplier_id,
        "warehouse_id": warehouse_id,
        "defect_type": defect_type,
        "defect_count": defect_count,
        "inspection_date": inspection_date,
        "severity": severity
    })

# =====================================================
# Save CSV
# =====================================================

df = pd.DataFrame(defect_records)

output_dir = Path("datasets/raw")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "defects.csv"

df.to_csv(output_file, index=False)

print("=" * 50)
print(f"Generated {len(df)} defect records")
print(f"Saved to: {output_file}")
print("=" * 50)

print("\nSample Data:")
print(df.head())