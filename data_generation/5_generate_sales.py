import pandas as pd
import random
from pathlib import Path
from datetime import datetime, timedelta

# =====================================================
# Configuration
# =====================================================

NUM_SALES_RECORDS = 500000

CUSTOMER_REGIONS = [
    "North India",
    "South India",
    "East India",
    "West India",
    "Central India",
    "North-East India"
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

# Product lookup
product_lookup = products_df.set_index("product_id")["unit_price"].to_dict()

product_ids = products_df["product_id"].tolist()

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
# Generate Sales
# =====================================================

sales_records = []

for i in range(1, NUM_SALES_RECORDS + 1):

    product_id = random.choice(product_ids)

    warehouse_id = random.choice(warehouse_ids)

    order_date = (
        start_date +
        timedelta(days=random.randint(0, date_range_days))
    ).strftime("%Y-%m-%d")

    customer_region = random.choice(CUSTOMER_REGIONS)

    quantity = random.randint(1, 100)

    unit_price = round(
        float(product_lookup[product_id]),
        2
    )

    revenue = round(
        quantity * unit_price,
        2
    )

    promotion_flag = random.choices(
        [True, False],
        weights=[20, 80],
        k=1
    )[0]

    sales_records.append({
        "order_id": f"ORD{i:07d}",
        "order_date": order_date,
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "customer_region": customer_region,
        "quantity": quantity,
        "unit_price": unit_price,
        "revenue": revenue,
        "promotion_flag": promotion_flag
    })

# =====================================================
# Save CSV
# =====================================================

df = pd.DataFrame(sales_records)

output_dir = Path("datasets/raw")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "sales.csv"

df.to_csv(output_file, index=False)

print("=" * 50)
print(f"Generated {len(df)} sales records")
print(f"Saved to: {output_file}")
print("=" * 50)

print("\nSample Data:")
print(df.head())