import pandas as pd
import random
from pathlib import Path

# =====================================================
# Configuration
# =====================================================

NUM_SUPPLIERS = 1000

COUNTRIES_CITIES = {
    "India": [
        "Mumbai",
        "Delhi",
        "Bangalore",
        "Pune",
        "Ahmedabad",
        "Hyderabad"
    ],
    "China": [
        "Shanghai",
        "Beijing",
        "Shenzhen",
        "Guangzhou"
    ],
    "Vietnam": [
        "Hanoi",
        "Ho Chi Minh City",
        "Da Nang"
    ],
    "Thailand": [
        "Bangkok",
        "Chiang Mai"
    ],
    "Bangladesh": [
        "Dhaka",
        "Chittagong"
    ],
    "Japan": [
        "Tokyo",
        "Osaka",
        "Nagoya"
    ],
    "South Korea": [
        "Seoul",
        "Busan"
    ],
    "Germany": [
        "Berlin",
        "Hamburg",
        "Munich"
    ],
    "USA": [
        "New York",
        "Chicago",
        "Dallas",
        "Los Angeles"
    ],
    "Mexico": [
        "Mexico City",
        "Monterrey"
    ],
    "Indonesia": [
        "Jakarta",
        "Surabaya"
    ],
    "Malaysia": [
        "Kuala Lumpur",
        "Penang"
    ],
    "Singapore": [
        "Singapore"
    ]
}

SUPPLIER_CATEGORIES = [
    "Raw Materials",
    "Packaging",
    "Electronics",
    "Food & Grocery",
    "Chemicals",
    "Textiles",
    "Logistics"
]

COMPANY_PREFIXES = [
    "Global",
    "Prime",
    "Elite",
    "National",
    "Reliable",
    "Smart",
    "Future",
    "Premium",
    "United",
    "Rapid",
    "Advanced",
    "Modern",
    "Strategic",
    "Dynamic",
    "NextGen"
]

COMPANY_SUFFIXES = [
    "Supplies",
    "Distributors",
    "Logistics",
    "Trading",
    "Industries",
    "Exports",
    "Wholesale",
    "Partners",
    "Corporation",
    "Solutions"
]

# =====================================================
# Generate Supplier Records
# =====================================================

suppliers = []

for i in range(1, NUM_SUPPLIERS + 1):

    supplier_id = f"SUP{i:04d}"

    country = random.choice(list(COUNTRIES_CITIES.keys()))
    city = random.choice(COUNTRIES_CITIES[country])

    supplier_name = (
        f"{random.choice(COMPANY_PREFIXES)} "
        f"{random.choice(COMPANY_SUFFIXES)} "
        f"{i:04d}"
    )

    supplier_category = random.choice(SUPPLIER_CATEGORIES)

    lead_time_days = random.randint(2, 30)

    defect_rate = round(random.uniform(0.5, 5.0), 2)

    on_time_delivery_rate = round(random.uniform(85.0, 99.5), 2)

    supplier_rating = round(random.uniform(3.0, 5.0), 1)

    risk_score = round(random.uniform(5.0, 95.0), 2)

    suppliers.append({
        "supplier_id": supplier_id,
        "supplier_name": supplier_name,
        "supplier_category": supplier_category,
        "country": country,
        "city": city,
        "lead_time_days": lead_time_days,
        "defect_rate": defect_rate,
        "on_time_delivery_rate": on_time_delivery_rate,
        "supplier_rating": supplier_rating,
        "risk_score": risk_score
    })

# =====================================================
# Save CSV
# =====================================================

df = pd.DataFrame(suppliers)

output_dir = Path("datasets/raw")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "suppliers.csv"

df.to_csv(output_file, index=False)

print("=" * 50)
print(f"Generated {len(df)} supplier records successfully")
print(f"Saved to: {output_file}")
print("=" * 50)

print("\nSample Data:")
print(df.head())