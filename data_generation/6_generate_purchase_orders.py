import pandas as pd
import random
from pathlib import Path
from datetime import datetime, timedelta

# =====================================================
# Configuration
# =====================================================

NUM_PURCHASE_ORDERS = 200000

STATUS_OPTIONS = [
    "Delivered",
    "In Transit",
    "Delayed",
    "Pending",
    "Cancelled"
]

STATUS_WEIGHTS = [
    60,  # Delivered
    15,  # In Transit
    10,  # Delayed
    10,  # Pending
    5    # Cancelled
]

# =====================================================
# Load Suppliers
# =====================================================

suppliers_file = Path("datasets/raw/suppliers.csv")

if not suppliers_file.exists():
    raise FileNotFoundError(
        "suppliers.csv not found. Run 1_generate_suppliers.py first."
    )

suppliers_df = pd.read_csv(suppliers_file)

supplier_ids = suppliers_df["supplier_id"].tolist()

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

# Create product -> supplier mapping
product_supplier_map = products_df.set_index(
    "product_id"
)["supplier_id"].to_dict()

# Create product -> lead time mapping
product_lead_time_map = products_df.set_index(
    "product_id"
)["lead_time_days"].to_dict()

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
# Generate Purchase Orders
# =====================================================

purchase_orders = []

for i in range(1, NUM_PURCHASE_ORDERS + 1):

    product_id = random.choice(product_ids)

    supplier_id = product_supplier_map[product_id]

    warehouse_id = random.choice(warehouse_ids)

    quantity = random.randint(100, 5000)

    order_date_obj = (
        start_date +
        timedelta(days=random.randint(0, date_range_days))
    )

    lead_time = int(product_lead_time_map[product_id])

    expected_delivery_date_obj = (
        order_date_obj +
        timedelta(days=lead_time)
    )

    status = random.choices(
        STATUS_OPTIONS,
        weights=STATUS_WEIGHTS,
        k=1
    )[0]

    if status == "Delivered":

        actual_delivery_date_obj = (
            expected_delivery_date_obj +
            timedelta(days=random.randint(-2, 3))
        )

        actual_delivery_date = actual_delivery_date_obj.strftime("%Y-%m-%d")

    elif status == "Delayed":

        actual_delivery_date_obj = (
            expected_delivery_date_obj +
            timedelta(days=random.randint(4, 15))
        )

        actual_delivery_date = actual_delivery_date_obj.strftime("%Y-%m-%d")

    else:
        actual_delivery_date = None

    purchase_orders.append({
        "po_id": f"PO{i:07d}",
        "supplier_id": supplier_id,
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "quantity": quantity,
        "order_date": order_date_obj.strftime("%Y-%m-%d"),
        "expected_delivery_date": expected_delivery_date_obj.strftime("%Y-%m-%d"),
        "actual_delivery_date": actual_delivery_date,
        "status": status
    })

# =====================================================
# Save CSV
# =====================================================

df = pd.DataFrame(purchase_orders)

output_dir = Path("datasets/raw")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "purchase_orders.csv"

df.to_csv(output_file, index=False)

print("=" * 50)
print(f"Generated {len(df)} purchase order records")
print(f"Saved to: {output_file}")
print("=" * 50)

print("\nSample Data:")
print(df.head())