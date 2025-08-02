#!/usr/bin/env python3
"""
Create sample test data for the Coffee Journal application.
"""
import json
import os
from datetime import datetime, date
from pathlib import Path

# Create test data directory
test_data_dir = Path('test_data')
test_data_dir.mkdir(exist_ok=True)

# Sample data
roasters = [
    {"id": 1, "name": "Blue Bottle Coffee"},
    {"id": 2, "name": "Intelligentsia Coffee"},
    {"id": 3, "name": "Stumptown Coffee Roasters"},
    {"id": 4, "name": "Counter Culture Coffee"},
    {"id": 5, "name": "La Colombe Coffee"}
]

bean_types = [
    {"id": 1, "name": "Arabica"},
    {"id": 2, "name": "Robusta"},
    {"id": 3, "name": "Liberica"},
    {"id": 4, "name": "Excelsa"}
]

countries = [
    {"id": 1, "name": "Ethiopia"},
    {"id": 2, "name": "Colombia"},
    {"id": 3, "name": "Brazil"},
    {"id": 4, "name": "Guatemala"},
    {"id": 5, "name": "Kenya"},
    {"id": 6, "name": "Jamaica"},
    {"id": 7, "name": "Hawaii"},
    {"id": 8, "name": "Costa Rica"},
    {"id": 9, "name": "Peru"},
    {"id": 10, "name": "Indonesia"}
]

regions = [
    {"id": 1, "name": "Yirgacheffe", "country_id": 1},
    {"id": 2, "name": "Huila", "country_id": 2},
    {"id": 3, "name": "Cerrado", "country_id": 3},
    {"id": 4, "name": "Antigua", "country_id": 4},
    {"id": 5, "name": "Nyeri", "country_id": 5}
]

brew_methods = [
    {"id": 1, "name": "V60"},
    {"id": 2, "name": "Chemex"},
    {"id": 3, "name": "French Press"},
    {"id": 4, "name": "AeroPress"},
    {"id": 5, "name": "Espresso"},
    {"id": 6, "name": "Pour Over"},
    {"id": 7, "name": "Cold Brew"},
    {"id": 8, "name": "Moka Pot"}
]

recipes = [
    {"id": 1, "name": "Standard V60"},
    {"id": 2, "name": "Tetsu Kasuya 4:6 Method"},
    {"id": 3, "name": "Classic French Press"},
    {"id": 4, "name": "Inverted AeroPress"},
    {"id": 5, "name": "Chemex Classic"}
]

decaf_methods = [
    {"id": 1, "name": "Swiss Water Process"},
    {"id": 2, "name": "CO2 Process"},
    {"id": 3, "name": "Ethyl Acetate Process"}
]

grinders = [
    {"id": 1, "name": "Hario Mini Mill"},
    {"id": 2, "name": "Baratza Encore"},
    {"id": 3, "name": "Fellow Ode"}
]

filters = [
    {"id": 1, "name": "V60 Paper Filter"},
    {"id": 2, "name": "Chemex Filter"},
    {"id": 3, "name": "Metal Filter"}
]

kettles = [
    {"id": 1, "name": "Hario V60 Buono"},
    {"id": 2, "name": "Fellow Stagg EKG"},
    {"id": 3, "name": "Bonavita Variable Temperature"}
]

scales = [
    {"id": 1, "name": "Hario V60 Scale"},
    {"id": 2, "name": "Acaia Pearl"},
    {"id": 3, "name": "Brewista Smart Scale"}
]

products = [
    {
        "id": 1,
        "roaster_id": 1,
        "bean_type_id": [1],
        "country_id": 1,
        "region_id": [1],
        "product_name": "Yirgacheffe Single Origin",
        "roast_type": 3,
        "description": "Bright, floral coffee with citrus notes",
        "url": "https://bluebottlecoffee.com/coffee/yirgacheffe",
        "image_url": None,
        "decaf": False,
        "decaf_method_id": None
    },
    {
        "id": 2,
        "roaster_id": 2,
        "bean_type_id": [1],
        "country_id": 2,
        "region_id": [2],
        "product_name": "El Diablo",
        "roast_type": 5,
        "description": "Rich Colombian coffee with chocolate and caramel notes",
        "url": "https://www.intelligentsia.com/coffee/el-diablo",
        "image_url": None,
        "decaf": False,
        "decaf_method_id": None
    },
    {
        "id": 3,
        "roaster_id": 3,
        "bean_type_id": [1],
        "country_id": 4,
        "region_id": [4],
        "product_name": "Guatemala Antigua",
        "roast_type": 4,
        "description": "Full-bodied Guatemalan coffee with spicy undertones",
        "url": "https://www.stumptowncoffee.com/products/guatemala-antigua",
        "image_url": None,
        "decaf": False,
        "decaf_method_id": None
    },
    {
        "id": 4,
        "roaster_id": 4,
        "bean_type_id": [1],
        "country_id": 5,
        "region_id": [5],
        "product_name": "Hologram",
        "roast_type": 3,
        "description": "Kenyan coffee with bright acidity and wine-like characteristics",
        "url": "https://counterculturecoffee.com/coffee/hologram",
        "image_url": None,
        "decaf": False,
        "decaf_method_id": None
    },
    {
        "id": 5,
        "roaster_id": 5,
        "bean_type_id": [1],
        "country_id": 3,
        "region_id": [3],
        "product_name": "Corsica",
        "roast_type": 6,
        "description": "Dark roasted Brazilian blend with nutty and chocolate notes",
        "url": "https://www.lacolombe.com/products/corsica",
        "image_url": None,
        "decaf": False,
        "decaf_method_id": None
    }
]

batches = [
    {
        "id": 1,
        "product_id": 1,
        "roast_date": "2024-12-15",
        "purchase_date": "2024-12-20",
        "amount_grams": 340.0,
        "price": 18.50,
        "seller": "Blue Bottle Coffee Store",
        "notes": "Fresh roast, excellent quality"
    },
    {
        "id": 2,
        "product_id": 2,
        "roast_date": "2024-12-18",
        "purchase_date": "2024-12-22",
        "amount_grams": 454.0,
        "price": 22.00,
        "seller": "Intelligentsia Online",
        "notes": "Holiday special blend"
    },
    {
        "id": 3,
        "product_id": 3,
        "roast_date": "2024-12-10",
        "purchase_date": "2024-12-25",
        "amount_grams": 340.0,
        "price": 19.75,
        "seller": "Local Coffee Shop",
        "notes": "Christmas gift"
    },
    {
        "id": 4,
        "product_id": 4,
        "roast_date": "2024-12-20",
        "purchase_date": "2024-12-28",
        "amount_grams": 250.0,
        "price": 16.00,
        "seller": "Counter Culture Direct",
        "notes": "Limited edition batch"
    },
    {
        "id": 5,
        "product_id": 1,
        "roast_date": "2025-01-02",
        "purchase_date": "2025-01-05",
        "amount_grams": 340.0,
        "price": 18.50,
        "seller": "Blue Bottle Coffee Store",
        "notes": "New year restock"
    },
    {
        "id": 6,
        "product_id": 5,
        "roast_date": "2024-12-28",
        "purchase_date": "2025-01-03",
        "amount_grams": 454.0,
        "price": 24.00,
        "seller": "La Colombe Cafe",
        "notes": "Dark roast for espresso"
    }
]

brew_sessions = [
    {
        "id": 1,
        "timestamp": "2024-12-21T08:30:00",
        "product_batch_id": 1,
        "product_id": 1,
        "brew_method_id": 1,
        "recipe_id": 1,
        "amount_coffee_grams": 20.0,
        "amount_water_grams": 320.0,
        "brew_temperature_c": 93.0,
        "bloom_time_seconds": 30,
        "brew_time_seconds": 180,
        "sweetness": 8,
        "acidity": 9,
        "bitterness": 3,
        "body": 6,
        "aroma": 9,
        "flavor_profile_match": 8,
        "notes": "Excellent floral notes, very bright and clean"
    },
    {
        "id": 2,
        "timestamp": "2024-12-23T09:15:00",
        "product_batch_id": 2,
        "product_id": 2,
        "brew_method_id": 2,
        "recipe_id": 5,
        "amount_coffee_grams": 30.0,
        "amount_water_grams": 480.0,
        "brew_temperature_c": 95.0,
        "bloom_time_seconds": 45,
        "brew_time_seconds": 240,
        "sweetness": 7,
        "acidity": 5,
        "bitterness": 4,
        "body": 8,
        "aroma": 7,
        "flavor_profile_match": 8,
        "notes": "Rich chocolate notes, great body with Chemex"
    },
    {
        "id": 3,
        "timestamp": "2024-12-26T10:00:00",
        "product_batch_id": 3,
        "product_id": 3,
        "brew_method_id": 3,
        "recipe_id": 3,
        "amount_coffee_grams": 25.0,
        "amount_water_grams": 400.0,
        "brew_temperature_c": 96.0,
        "bloom_time_seconds": None,
        "brew_time_seconds": 240,
        "sweetness": 6,
        "acidity": 4,
        "bitterness": 6,
        "body": 9,
        "aroma": 6,
        "flavor_profile_match": 7,
        "notes": "Full-bodied with French press, some sediment"
    },
    {
        "id": 4,
        "timestamp": "2024-12-29T07:45:00",
        "product_batch_id": 4,
        "product_id": 4,
        "brew_method_id": 4,
        "recipe_id": 4,
        "amount_coffee_grams": 18.0,
        "amount_water_grams": 270.0,
        "brew_temperature_c": 85.0,
        "bloom_time_seconds": 30,
        "brew_time_seconds": 90,
        "sweetness": 8,
        "acidity": 8,
        "bitterness": 2,
        "body": 7,
        "aroma": 8,
        "flavor_profile_match": 9,
        "notes": "AeroPress brings out the wine-like characteristics perfectly"
    },
    {
        "id": 5,
        "timestamp": "2025-01-06T08:00:00",
        "product_batch_id": 5,
        "product_id": 1,
        "brew_method_id": 1,
        "recipe_id": 2,
        "amount_coffee_grams": 20.0,
        "amount_water_grams": 300.0,
        "brew_temperature_c": 92.0,
        "bloom_time_seconds": 45,
        "brew_time_seconds": 210,
        "sweetness": 9,
        "acidity": 8,
        "bitterness": 2,
        "body": 7,
        "aroma": 9,
        "flavor_profile_match": 9,
        "notes": "4:6 method enhanced the sweetness dramatically"
    },
    {
        "id": 6,
        "timestamp": "2025-01-04T14:30:00",
        "product_batch_id": 6,
        "product_id": 5,
        "brew_method_id": 5,
        "recipe_id": None,
        "amount_coffee_grams": 18.0,
        "amount_water_grams": 36.0,
        "brew_temperature_c": 94.0,
        "bloom_time_seconds": None,
        "brew_time_seconds": 25,
        "sweetness": 5,
        "acidity": 3,
        "bitterness": 7,
        "body": 9,
        "aroma": 7,
        "flavor_profile_match": 8,
        "notes": "Perfect for espresso, rich crema and balanced bitterness"
    }
]

# Write JSON files
files_to_create = [
    ('roasters.json', roasters),
    ('bean_types.json', bean_types),
    ('countries.json', countries),
    ('regions.json', regions),
    ('brew_methods.json', brew_methods),
    ('recipes.json', recipes),
    ('decaf_methods.json', decaf_methods),
    ('grinders.json', grinders),
    ('filters.json', filters),
    ('kettles.json', kettles),
    ('scales.json', scales),
    ('products.json', products),
    ('batches.json', batches),
    ('brew_sessions.json', brew_sessions)
]

for filename, data in files_to_create:
    filepath = test_data_dir / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Created {filepath} with {len(data)} records")

print(f"\n✅ Test data created successfully in {test_data_dir}/")
print("\nData summary:")
print(f"  - {len(roasters)} roasters")
print(f"  - {len(bean_types)} bean types")
print(f"  - {len(countries)} countries")
print(f"  - {len(regions)} regions")
print(f"  - {len(brew_methods)} brew methods")
print(f"  - {len(recipes)} recipes")
print(f"  - {len(decaf_methods)} decaf methods")
print(f"  - {len(grinders)} grinders")
print(f"  - {len(filters)} filters")
print(f"  - {len(kettles)} kettles")
print(f"  - {len(scales)} scales")
print(f"  - {len(products)} products")
print(f"  - {len(batches)} batches")
print(f"  - {len(brew_sessions)} brew sessions")