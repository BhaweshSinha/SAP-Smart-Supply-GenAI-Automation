import pandas as pd
import random
from pathlib import Path

# =====================================================
# Configuration
# =====================================================

NUM_WAREHOUSES = 50

WAREHOUSE_LOCATIONS = {
    "Maharashtra": ["Mumbai", "Pune", "Nagpur"],
    "Delhi": ["New Delhi"],
    "Karnataka": ["Bangalore", "Mysore"],
    "Tamil Nadu": ["Chennai", "Coimbatore"],
    "Telangana": ["Hyderabad"],
    "West Bengal": ["Kolkata"],
    "Gujarat": ["Ahmedabad", "Surat"],
    "Rajasthan": ["Jaipur"],
    "Uttar Pradesh": ["Lucknow", "Noida"],
    "Punjab": ["Ludhiana"],
    "Haryana": ["Gurugram"],
    "Bihar": ["Patna"],
    "Odisha": ["Bhubaneswar"],
    "Kerala": ["Kochi"],
    "Madhya Pradesh": ["Indore"]
}

FIRST_NAMES = [
    "Amit", "Rahul", "Vikram", "Arjun", "Sanjay",
    "Rohit", "Karan", "Deepak", "Ankit", "Manish",
    "Priya", "Neha", "Pooja", "Sneha", "Ritika"
]

LAST_NAMES = [
    "Sharma", "Verma", "Singh", "Gupta", "Yadav",
    "Patel", "Kumar", "Sinha", "Mishra", "Agarwal"
]

# =====================================================
# Generate Warehouses
# =====================================================

warehouses = []

for i in range(1, NUM_WAREHOUSES + 1):

    state = random.choice(list(WAREHOUSE_LOCATIONS.keys()))
    city = random.choice(WAREHOUSE_LOCATIONS[state])

    capacity = random.randint(50000, 500000)

    utilized_capacity = int(
        capacity * random.uniform(0.40, 0.95)
    )

    manager_name = (
        f"{random.choice(FIRST_NAMES)} "
        f"{random.choice(LAST_NAMES)}"
    )

    warehouses.append({
        "warehouse_id": f"WH{i:03d}",
        "warehouse_name": f"{city} Distribution Center",
        "city": city,
        "state": state,
        "capacity": capacity,
        "utilized_capacity": utilized_capacity,
        "manager_name": manager_name
    })

# =====================================================
# Save CSV
# =====================================================

df = pd.DataFrame(warehouses)

output_dir = Path("datasets/raw")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "warehouses.csv"

df.to_csv(output_file, index=False)

print(f"Generated {len(df)} warehouse records")
print(f"Saved to: {output_file}")