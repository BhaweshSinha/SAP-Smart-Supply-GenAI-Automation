import pandas as pd
import random
from pathlib import Path
from datetime import datetime, timedelta

# =====================================================
# Configuration
# =====================================================

NUM_PRODUCTS = 10000

CATEGORIES = {
    "Beverages": [
        "Green Tea", "Black Tea", "Coffee", "Orange Juice", "Apple Juice",
        "Energy Drink", "Mineral Water", "Soft Drink", "Lemonade", "Milk Shake"
    ],
    "Dairy": [
        "Milk", "Cheese", "Butter", "Yogurt", "Cream",
        "Paneer", "Curd", "Flavored Milk", "Ice Cream", "Greek Yogurt"
    ],
    "Snacks": [
        "Potato Chips", "Nachos", "Popcorn", "Cookies", "Crackers",
        "Chocolate Bar", "Trail Mix", "Pretzels", "Protein Bar", "Peanuts"
    ],
    "Bakery": [
        "Bread", "Croissant", "Muffin", "Cake", "Donut",
        "Bun", "Bagel", "Brownie", "Cupcake", "Pastry"
    ],
    "Frozen Foods": [
        "Frozen Pizza", "Frozen Fries", "Frozen Vegetables", "Frozen Nuggets",
        "Frozen Burger Patty", "Frozen Fish", "Frozen Chicken", "Frozen Peas",
        "Frozen Corn", "Frozen Dessert"
    ],
    "Personal Care": [
        "Shampoo", "Conditioner", "Toothpaste", "Soap", "Face Wash",
        "Body Lotion", "Hand Wash", "Deodorant", "Hair Oil", "Moisturizer"
    ],
    "Household": [
        "Aluminum Foil", "Tissue Paper", "Trash Bags", "Storage Box",
        "Kitchen Towels", "Plastic Wrap", "Batteries", "Light Bulb",
        "Air Freshener", "Paper Napkins"
    ],
    "Fruits & Vegetables": [
        "Apple", "Banana", "Orange", "Tomato", "Potato",
        "Onion", "Carrot", "Cucumber", "Spinach", "Mango"
    ],
    "Packaged Foods": [
        "Instant Noodles", "Pasta", "Rice", "Breakfast Cereal",
        "Soup Mix", "Oats", "Flour", "Sugar", "Salt", "Spices"
    ],
    "Cleaning Supplies": [
        "Dishwashing Liquid", "Laundry Detergent", "Floor Cleaner",
        "Glass Cleaner", "Toilet Cleaner", "Bleach",
        "Surface Cleaner", "Disinfectant Spray",
        "Cleaning Wipes", "Fabric Softener"
    ]
}

BRANDS = [
    "FreshMart",
    "DailyChoice",
    "PureLife",
    "GreenHarvest",
    "QuickBite",
    "HomeEssentials",
    "PrimeFoods",
    "NaturePlus",
    "SmartChoice",
    "UrbanFresh",
    "GoldenHarvest",
    "EcoLiving",
    "HealthySelect",
    "MegaStore",
    "ValuePlus",
    "PureHarvest",
    "FamilyChoice",
    "SuperFresh",
    "HappyHome",
    "PremiumSelect"
]

PRODUCT_SIZES = [
    "100g",
    "200g",
    "250g",
    "500g",
    "750g",
    "1kg",
    "250ml",
    "500ml",
    "750ml",
    "1L",
    "Pack",
    "Box"
]

# =====================================================
# Load Suppliers
# =====================================================

suppliers_file = Path("datasets/raw/suppliers.csv")

if not suppliers_file.exists():
    raise FileNotFoundError(
        "suppliers.csv not found. Please run 1_generate_suppliers.py first."
    )

suppliers_df = pd.read_csv(suppliers_file)

supplier_ids = suppliers_df["supplier_id"].tolist()

# =====================================================
# Generate Products
# =====================================================

products = []

start_date = datetime(2021, 1, 1)
end_date = datetime(2026, 1, 1)

date_range_days = (end_date - start_date).days

for i in range(1, NUM_PRODUCTS + 1):

    category = random.choice(list(CATEGORIES.keys()))

    base_product = random.choice(CATEGORIES[category])

    product_name = (
        f"{base_product} "
        f"{random.choice(PRODUCT_SIZES)}"
    )

    brand = random.choice(BRANDS)

    unit_cost = round(random.uniform(20, 500), 2)

    markup = random.uniform(1.15, 1.60)

    unit_price = round(unit_cost * markup, 2)

    supplier_id = random.choice(supplier_ids)

    lead_time_days = random.randint(2, 30)

    reorder_point = random.randint(20, 300)

    safety_stock = random.randint(5, 100)

    created_at = (
        start_date +
        timedelta(days=random.randint(0, date_range_days))
    ).strftime("%Y-%m-%d")

    products.append({
        "product_id": f"PRD{i:05d}",
        "product_name": product_name,
        "category": category,
        "brand": brand,
        "unit_cost": unit_cost,
        "unit_price": unit_price,
        "supplier_id": supplier_id,
        "lead_time_days": lead_time_days,
        "reorder_point": reorder_point,
        "safety_stock": safety_stock,
        "created_at": created_at
    })

# =====================================================
# Save CSV
# =====================================================

df = pd.DataFrame(products)

output_dir = Path("datasets/raw")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "products.csv"

df.to_csv(output_file, index=False)

print("=" * 60)
print(f"Generated {len(df)} product records successfully")
print(f"Saved to: {output_file}")
print("=" * 60)

print("\nSample Data:")
print(df.head())