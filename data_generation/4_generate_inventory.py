import pandas as pd
import random
from pathlib import Path
from datetime import datetime, timedelta

# =====================================================
# Configuration
# =====================================================

NUM_INVENTORY_RECORDS = 100000

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
# Generate Inventory
# =====================================================

inventory_records = []

for i in range(1, NUM_INVENTORY_RECORDS + 1):

    product_id = random.choice(product_ids)

    warehouse_id = random.choice(warehouse_ids)

    stock_on_hand = random.randint(100, 10000)

    stock_reserved = random.randint(
        0,
        int(stock_on_hand * 0.4)
    )

    available_stock = stock_on_hand - stock_reserved

    last_updated = (
        datetime.now() -
        timedelta(days=random.randint(0, 365))
    ).strftime("%Y-%m-%d")

    inventory_records.append({
        "inventory_id": f"INV{i:06d}",
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "stock_on_hand": stock_on_hand,
        "stock_reserved": stock_reserved,
        "available_stock": available_stock,
        "last_updated": last_updated
    })

# =====================================================
# Save CSV
# =====================================================

df = pd.DataFrame(inventory_records)

output_dir = Path("datasets/raw")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "inventory.csv"

df.to_csv(output_file, index=False)

print("=" * 50)
print(f"Generated {len(df)} inventory records")
print(f"Saved to: {output_file}")
print("=" * 50)

print("\nSample Data:")
print(df.head())