#!/usr/bin/env python3
"""
Create comprehensive sample test data for the Coffee Journal application.
Includes all schema fields and realistic data for brew recommendations.
"""
import json
import os
import random
from datetime import datetime, date, timedelta
from pathlib import Path

# Create test data directory
test_data_dir = Path('test_data')
test_data_dir.mkdir(exist_ok=True)

# Enhanced sample data with all schema fields
roasters = [
    {"id": 1, "name": "Blue Bottle Coffee", "short_form": "Blue Bottle", "description": "Oakland-based specialty coffee roaster", "url": "https://bluebottlecoffee.com"},
    {"id": 2, "name": "Intelligentsia Coffee", "short_form": "Intelligentsia", "description": "Chicago-based third wave coffee pioneer", "url": "https://www.intelligentsia.com"},
    {"id": 3, "name": "Stumptown Coffee Roasters", "short_form": "Stumptown", "description": "Portland-based artisan coffee roaster", "url": "https://www.stumptowncoffee.com"},
    {"id": 4, "name": "Counter Culture Coffee", "short_form": "Counter Culture", "description": "Durham-based sustainable coffee roaster", "url": "https://counterculturecoffee.com"},
    {"id": 5, "name": "La Colombe Coffee", "short_form": "La Colombe", "description": "Philadelphia-based coffee roaster and cafe", "url": "https://www.lacolombe.com"},
    {"id": 6, "name": "Ritual Coffee Roasters", "short_form": "Ritual", "description": "San Francisco-based specialty coffee", "url": "https://www.ritualcoffee.com"},
    {"id": 7, "name": "Verve Coffee Roasters", "short_form": "Verve", "description": "Santa Cruz-based coffee roaster", "url": "https://www.vervecoffee.com"},
    {"id": 8, "name": "George Howell Coffee", "short_form": "George Howell", "description": "Boston-based coffee pioneer", "url": "https://www.georgehowellcoffee.com"}
]

bean_types = [
    {"id": 1, "name": "Arabica", "short_form": "Arabica", "description": "High-quality coffee species with complex flavors"},
    {"id": 2, "name": "Robusta", "short_form": "Robusta", "description": "Hardy coffee species with higher caffeine content"},
    {"id": 3, "name": "Liberica", "short_form": "Liberica", "description": "Rare coffee species with unique woody flavor"},
    {"id": 4, "name": "Excelsa", "short_form": "Excelsa", "description": "Coffee variety known for tart, fruity flavors"}
]

countries = [
    {"id": 1, "name": "Ethiopia", "short_form": "Ethiopia", "description": "Birthplace of coffee with diverse flavor profiles"},
    {"id": 2, "name": "Colombia", "short_form": "Colombia", "description": "High altitude growing regions producing balanced coffees"},
    {"id": 3, "name": "Brazil", "short_form": "Brazil", "description": "World's largest coffee producer with nutty, chocolatey flavors"},
    {"id": 4, "name": "Guatemala", "short_form": "Guatemala", "description": "Volcanic soil producing full-bodied coffees"},
    {"id": 5, "name": "Kenya", "short_form": "Kenya", "description": "High-grown coffees known for wine-like acidity"},
    {"id": 6, "name": "Jamaica", "short_form": "Jamaica", "description": "Blue Mountain region famous for smooth, mild coffee"},
    {"id": 7, "name": "Hawaii", "short_form": "Hawaii", "description": "Only US state growing commercial coffee"},
    {"id": 8, "name": "Costa Rica", "short_form": "Costa Rica", "description": "Bright, clean coffees from volcanic regions"},
    {"id": 9, "name": "Peru", "short_form": "Peru", "description": "Organic-focused production with balanced flavors"},
    {"id": 10, "name": "Indonesia", "short_form": "Indonesia", "description": "Earthy, full-bodied coffees from island archipelago"}
]

regions = [
    {"id": 1, "name": "Yirgacheffe", "short_form": "Yirgacheffe", "country_id": 1, "description": "Floral, tea-like Ethiopian coffees"},
    {"id": 2, "name": "Huila", "short_form": "Huila", "country_id": 2, "description": "High-altitude Colombian region"},
    {"id": 3, "name": "Cerrado", "short_form": "Cerrado", "country_id": 3, "description": "Brazilian savanna region"},
    {"id": 4, "name": "Antigua", "short_form": "Antigua", "country_id": 4, "description": "Historic Guatemalan volcanic valley"},
    {"id": 5, "name": "Nyeri", "short_form": "Nyeri", "country_id": 5, "description": "Kenyan region known for bright acidity"},
    {"id": 6, "name": "Sidama", "short_form": "Sidama", "country_id": 1, "description": "Ethiopian region with complex fruit notes"},
    {"id": 7, "name": "Nariño", "short_form": "Nariño", "country_id": 2, "description": "Colombian region near Ecuador border"}
]

brew_methods = [
    {"id": 1, "name": "V60", "short_form": "V60", "description": "Hario V60 pour-over dripper with spiral ridges"},
    {"id": 2, "name": "Chemex", "short_form": "Chemex", "description": "Glass pour-over with thick paper filters"},
    {"id": 3, "name": "French Press", "short_form": "French Press", "description": "Immersion brewing with metal mesh filter"},
    {"id": 4, "name": "AeroPress", "short_form": "AeroPress", "description": "Pressure-assisted immersion brewing device"},
    {"id": 5, "name": "Espresso", "short_form": "Espresso", "description": "High-pressure brewing method"},
    {"id": 6, "name": "Pour Over", "short_form": "Pour Over", "description": "General pour-over brewing method"},
    {"id": 7, "name": "Cold Brew", "short_form": "Cold Brew", "description": "Cold water extraction over 12+ hours"},
    {"id": 8, "name": "Moka Pot", "short_form": "Moka", "description": "Stovetop espresso maker"},
    {"id": 9, "name": "Kalita Wave", "short_form": "Kalita", "description": "Flat-bottom pour-over dripper"},
    {"id": 10, "name": "Siphon", "short_form": "Siphon", "description": "Vacuum brewing method with glass chambers"}
]

recipes = [
    {"id": 1, "name": "Standard V60", "short_form": "Std V60", "description": "Classic V60 pouring technique"},
    {"id": 2, "name": "Tetsu Kasuya 4:6 Method", "short_form": "4:6 Method", "description": "Competition-winning V60 technique"},
    {"id": 3, "name": "Classic French Press", "short_form": "Classic FP", "description": "Traditional French press brewing"},
    {"id": 4, "name": "Inverted AeroPress", "short_form": "Inverted AP", "description": "Upside-down AeroPress method"},
    {"id": 5, "name": "Chemex Classic", "short_form": "Classic Chemex", "description": "Traditional Chemex technique"},
    {"id": 6, "name": "Osmotic Flow", "short_form": "Osmotic", "description": "Slow, controlled V60 pour technique"},
    {"id": 7, "name": "Rao Spin", "short_form": "Rao Spin", "description": "Scott Rao's stirring technique"},
    {"id": 8, "name": "Hoffman Method", "short_form": "Hoffman", "description": "James Hoffmann's V60 technique"}
]

decaf_methods = [
    {"id": 1, "name": "Swiss Water Process", "short_form": "Swiss Water", "description": "Chemical-free decaffeination using water"},
    {"id": 2, "name": "CO2 Process", "short_form": "CO2", "description": "Supercritical carbon dioxide decaffeination"},
    {"id": 3, "name": "Ethyl Acetate Process", "short_form": "EA", "description": "Natural decaffeination using fruit-derived EA"}
]

# Espresso Equipment
brewers = [
    {"id": 1, "name": "Breville Bambino Plus", "short_form": "Bambino+", "description": "Entry-level espresso machine with automatic milk frother", "type": "espresso", "brand": "Breville", "model": "Bambino Plus"},
    {"id": 2, "name": "Gaggia Classic Pro", "short_form": "Classic Pro", "description": "Traditional Italian espresso machine", "type": "espresso", "brand": "Gaggia", "model": "Classic Pro"},
    {"id": 3, "name": "Rancilio Silvia", "short_form": "Silvia", "description": "Semi-professional home espresso machine", "type": "espresso", "brand": "Rancilio", "model": "Silvia"},
    {"id": 4, "name": "La Marzocco Linea Mini", "short_form": "Linea Mini", "description": "Compact commercial-grade espresso machine", "type": "espresso", "brand": "La Marzocco", "model": "Linea Mini"},
    {"id": 5, "name": "Rocket Appartamento", "short_form": "Appartamento", "description": "Heat exchanger espresso machine", "type": "espresso", "brand": "Rocket", "model": "Appartamento"},
    {"id": 6, "name": "Hario V60", "short_form": "V60", "description": "Pour-over dripper", "type": "pourover", "brand": "Hario", "model": "V60-02"},
    {"id": 7, "name": "Chemex 6-cup", "short_form": "Chemex", "description": "Glass pour-over brewer", "type": "pourover", "brand": "Chemex", "model": "6-cup"}
]

portafilters = [
    {"id": 1, "name": "Standard 58mm", "short_form": "Standard 58mm", "description": "Standard 58mm portafilter", "size": "58mm", "basket_count": 2, "material": "brass"},
    {"id": 2, "name": "Naked 58mm", "short_form": "Naked 58mm", "description": "Bottomless 58mm portafilter", "size": "58mm", "basket_count": 1, "material": "brass"},
    {"id": 3, "name": "Standard 54mm", "short_form": "Standard 54mm", "description": "Standard 54mm portafilter", "size": "54mm", "basket_count": 2, "material": "brass"},
    {"id": 4, "name": "VST 58mm", "short_form": "VST 58mm", "description": "Precision VST 58mm portafilter", "size": "58mm", "basket_count": 1, "material": "stainless steel"}
]

baskets = [
    {"id": 1, "name": "Standard 18g", "short_form": "18g", "description": "Standard double basket", "size": "58mm", "capacity": "18g", "holes": 36},
    {"id": 2, "name": "VST 18g", "short_form": "VST 18g", "description": "Precision VST 18g basket", "size": "58mm", "capacity": "18g", "holes": 37},
    {"id": 3, "name": "IMS 20g", "short_form": "IMS 20g", "description": "Competition IMS 20g basket", "size": "58mm", "capacity": "20g", "holes": 39},
    {"id": 4, "name": "Standard 15g", "short_form": "15g", "description": "Standard double basket", "size": "54mm", "capacity": "15g", "holes": 32},
    {"id": 5, "name": "Triple 21g", "short_form": "21g", "description": "Triple shot basket", "size": "58mm", "capacity": "21g", "holes": 42}
]

tampers = [
    {"id": 1, "name": "Basic 58mm", "short_form": "Basic 58mm", "description": "Standard aluminum tamper", "size": "58mm", "weight": "400g", "material": "aluminum", "base_style": "flat"},
    {"id": 2, "name": "Decent Tamper", "short_form": "Decent", "description": "Precision tamper with level base", "size": "58.5mm", "weight": "500g", "material": "stainless steel", "base_style": "convex"},
    {"id": 3, "name": "Pullman Big Step", "short_form": "Pullman", "description": "Professional competition tamper", "size": "58.55mm", "weight": "750g", "material": "stainless steel", "base_style": "flat"},
    {"id": 4, "name": "Basic 54mm", "short_form": "Basic 54mm", "description": "Standard tamper for 54mm", "size": "54mm", "weight": "350g", "material": "aluminum", "base_style": "flat"}
]

wdt_tools = [
    {"id": 1, "name": "Basic WDT", "short_form": "Basic WDT", "description": "Simple distribution tool", "needle_count": 8, "needle_diameter": 0.4, "handle_material": "wood", "brand": "Generic"},
    {"id": 2, "name": "Decent WDT", "short_form": "Decent WDT", "description": "Precision distribution tool", "needle_count": 9, "needle_diameter": 0.35, "handle_material": "aluminum", "brand": "Decent"},
    {"id": 3, "name": "Premium WDT", "short_form": "Premium WDT", "description": "High-end distribution tool", "needle_count": 10, "needle_diameter": 0.3, "handle_material": "titanium", "brand": "Levercraft"}
]

leveling_tools = [
    {"id": 1, "name": "OCD 58mm", "short_form": "OCD", "description": "Ona Coffee Distributor", "size": "58mm", "adjustment_type": "adjustable", "depth_range": "3-12mm", "brand": "Ona Coffee"},
    {"id": 2, "name": "Saint Anthony 58mm", "short_form": "Saint Anthony", "description": "Leveling and distribution tool", "size": "58mm", "adjustment_type": "adjustable", "depth_range": "2-10mm", "brand": "Saint Anthony Industries"},
    {"id": 3, "name": "Basic Leveler", "short_form": "Basic Leveler", "description": "Simple leveling tool", "size": "58mm", "adjustment_type": "fixed", "depth_range": "8mm", "brand": "Generic"}
]

grinders = [
    {"id": 1, "name": "Hario Mini Mill", "short_form": "Mini Mill", "description": "Compact ceramic burr hand grinder"},
    {"id": 2, "name": "Baratza Encore", "short_form": "Encore", "description": "Entry-level electric burr grinder"},
    {"id": 3, "name": "Fellow Ode", "short_form": "Ode", "description": "Flat burr grinder optimized for filter coffee"},
    {"id": 4, "name": "Comandante C40", "short_form": "C40", "description": "Premium conical burr hand grinder"},
    {"id": 5, "name": "Wilfa Uniform", "short_form": "Uniform", "description": "Nordic-designed electric grinder"},
    {"id": 6, "name": "Timemore Chestnut C2", "short_form": "C2", "description": "Portable hand grinder with steel burrs"},
    {"id": 7, "name": "Baratza Virtuoso+", "short_form": "Virtuoso+", "description": "Mid-range conical burr grinder"}
]

filters = [
    {"id": 1, "name": "Hario V60 Paper Filter", "short_form": "V60-02", "description": "Standard V60 size 02 paper filters"},
    {"id": 2, "name": "Chemex Paper Filter", "short_form": "Chemex", "description": "Thick bonded paper filters for Chemex"},
    {"id": 3, "name": "Metal Filter", "short_form": "Metal", "description": "Reusable stainless steel filter"},
    {"id": 4, "name": "Cafec Abaca+ Filter", "short_form": "Abaca+", "description": "Premium abaca fiber V60 filters"},
    {"id": 5, "name": "Cafec T-90 Filter", "short_form": "T-90", "description": "Fast-flow V60 paper filters"},
    {"id": 6, "name": "Kalita Wave Filter", "short_form": "Wave", "description": "Flat-bottom Kalita Wave filters"},
    {"id": 7, "name": "AeroPress Paper Filter", "short_form": "AP Paper", "description": "Round AeroPress paper filters"}
]

kettles = [
    {"id": 1, "name": "Hario V60 Buono", "short_form": "Buono", "description": "Classic gooseneck kettle for pour-over"},
    {"id": 2, "name": "Fellow Stagg EKG", "short_form": "Stagg EKG", "description": "Electric gooseneck with temperature control"},
    {"id": 3, "name": "Bonavita Variable Temperature", "short_form": "Bonavita", "description": "Electric kettle with precise temperature"},
    {"id": 4, "name": "Brewista Artisan", "short_form": "Artisan", "description": "Gooseneck kettle with built-in timer"},
    {"id": 5, "name": "Timemore Fish Kettle", "short_form": "Fish", "description": "Minimalist gooseneck kettle"}
]

scales = [
    {"id": 1, "name": "Hario V60 Scale", "short_form": "V60 Scale", "description": "Basic brewing scale with timer"},
    {"id": 2, "name": "Acaia Pearl", "short_form": "Pearl", "description": "Professional coffee scale with app connectivity"},
    {"id": 3, "name": "Brewista Smart Scale", "short_form": "Smart Scale", "description": "Fast-response brewing scale"},
    {"id": 4, "name": "Timemore Black Mirror", "short_form": "Black Mirror", "description": "Precise scale with flow rate indicator"},
    {"id": 5, "name": "Fellow Atmos", "short_form": "Atmos", "description": "Vacuum-sealed scale for freshness"}
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
        "image_url": "https://via.placeholder.com/300x300/8D6E63/FFFFFF?text=Yirgacheffe+Single+Origin",
        "decaf": False
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
        "image_url": "https://via.placeholder.com/300x300/6D4C41/FFFFFF?text=El+Diablo",
        "decaf": False
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
        "image_url": "https://via.placeholder.com/300x300/795548/FFFFFF?text=Guatemala+Antigua",
        "decaf": False
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
        "image_url": "https://via.placeholder.com/300x300/8D6E63/FFFFFF?text=Hologram",
        "decaf": False
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
        "image_url": "https://via.placeholder.com/300x300/5D4037/FFFFFF?text=Corsica",
        "decaf": False
    },
    {
        "id": 6,
        "roaster_id": 6,
        "bean_type_id": [1],
        "country_id": 1,
        "region_id": [6],
        "product_name": "Ethiopia Sidama",
        "roast_type": 2,
        "description": "Light roasted Ethiopian with complex fruit notes",
        "url": "https://www.ritualcoffee.com/products/ethiopia-sidama",
        "image_url": "https://via.placeholder.com/300x300/A1887F/FFFFFF?text=Ethiopia+Sidama",
        "decaf": False
    },
    {
        "id": 7,
        "roaster_id": 7,
        "bean_type_id": [1],
        "country_id": 8,
        "region_id": [],
        "product_name": "Costa Rica Decaf",
        "roast_type": 3,
        "description": "Swiss water processed Costa Rican coffee",
        "url": "https://www.vervecoffee.com/products/decaf",
        "image_url": "https://via.placeholder.com/300x300/8D6E63/FFFFFF?text=Costa+Rica+Decaf",
        "decaf": True,
        "decaf_method_id": 1
    }
]

batches = [
    {"id": 1, "product_id": 1, "roast_date": "2024-12-15", "purchase_date": "2024-12-20", "amount_grams": 340.0, "price": 18.50, "seller": "Blue Bottle Coffee Store", "notes": "Fresh roast, excellent quality"},
    {"id": 2, "product_id": 2, "roast_date": "2024-12-18", "purchase_date": "2024-12-22", "amount_grams": 454.0, "price": 22.00, "seller": "Intelligentsia Online", "notes": "Holiday special blend"},
    {"id": 3, "product_id": 3, "roast_date": "2024-12-10", "purchase_date": "2024-12-25", "amount_grams": 340.0, "price": 19.75, "seller": "Local Coffee Shop", "notes": "Christmas gift"},
    {"id": 4, "product_id": 4, "roast_date": "2024-12-20", "purchase_date": "2024-12-28", "amount_grams": 250.0, "price": 16.00, "seller": "Counter Culture Direct", "notes": "Limited edition batch"},
    {"id": 5, "product_id": 1, "roast_date": "2025-01-02", "purchase_date": "2025-01-05", "amount_grams": 340.0, "price": 18.50, "seller": "Blue Bottle Coffee Store", "notes": "New year restock"},
    {"id": 6, "product_id": 5, "roast_date": "2024-12-28", "purchase_date": "2025-01-03", "amount_grams": 454.0, "price": 24.00, "seller": "La Colombe Cafe", "notes": "Dark roast for espresso"},
    {"id": 7, "product_id": 6, "roast_date": "2025-01-10", "purchase_date": "2025-01-15", "amount_grams": 250.0, "price": 20.00, "seller": "Ritual Coffee", "notes": "Light roast, very fruity"},
    {"id": 8, "product_id": 7, "roast_date": "2025-01-08", "purchase_date": "2025-01-12", "amount_grams": 340.0, "price": 19.50, "seller": "Verve Coffee", "notes": "Decaf for evening brews"}
]

# Generate comprehensive brew sessions with equipment and varied parameters
def generate_brew_sessions():
    sessions = []
    session_id = 1
    base_date = datetime(2024, 12, 21)
    
    # Define parameter variations for different products and methods
    session_templates = [
        # Product 1 (Yirgacheffe) - V60 sessions with variations
        *[{
            "product_id": 1, "product_batch_id": 1, "brew_method_id": 1, "recipe_id": random.choice([1, 2, 6]),
            "grinder_id": 5, "filter_id": random.choice([1, 4, 5]), "kettle_id": 2, "scale_id": 2,
            "amount_coffee_grams": round(random.uniform(17, 21), 1), "amount_water_grams": round(random.uniform(270, 340), 0),
            "brew_temperature_c": random.randint(88, 94), "bloom_time_seconds": random.randint(30, 60),
            "brew_time_seconds": random.randint(150, 210), "grinder_setting": str(random.randint(20, 24)),
            "sweetness": random.randint(7, 9), "acidity": random.randint(8, 10), "bitterness": random.randint(2, 4),
            "body": random.randint(5, 7), "aroma": random.randint(8, 10), "flavor_profile_match": random.randint(7, 9),
            "notes": random.choice(["Bright floral notes", "Excellent clarity", "Tea-like qualities", "Perfect balance"])
        } for _ in range(8)],
        
        # Product 1 - Chemex sessions
        *[{
            "product_id": 1, "product_batch_id": 1, "brew_method_id": 2, "recipe_id": 5,
            "grinder_id": 5, "filter_id": 2, "kettle_id": 2, "scale_id": 2,
            "amount_coffee_grams": round(random.uniform(25, 35), 1), "amount_water_grams": round(random.uniform(400, 560), 0),
            "brew_temperature_c": random.randint(92, 96), "bloom_time_seconds": random.randint(45, 75),
            "brew_time_seconds": random.randint(300, 420), "grinder_setting": str(random.randint(22, 26)),
            "sweetness": random.randint(6, 8), "acidity": random.randint(7, 9), "bitterness": random.randint(2, 4),
            "body": random.randint(6, 8), "aroma": random.randint(7, 9), "flavor_profile_match": random.randint(6, 8),
            "notes": random.choice(["Clean cup", "Smooth finish", "Well-balanced", "Bright and clean"])
        } for _ in range(4)],
        
        # Product 2 (El Diablo) - V60 and Chemex
        *[{
            "product_id": 2, "product_batch_id": 2, "brew_method_id": random.choice([1, 2]), 
            "recipe_id": random.choice([1, 2, 5]), "grinder_id": random.choice([2, 5, 7]),
            "filter_id": random.choice([1, 2, 4]), "kettle_id": random.choice([1, 2]), "scale_id": random.choice([1, 2, 3]),
            "amount_coffee_grams": round(random.uniform(18, 32), 1), "amount_water_grams": round(random.uniform(290, 500), 0),
            "brew_temperature_c": random.randint(90, 96), "bloom_time_seconds": random.randint(30, 60),
            "brew_time_seconds": random.randint(180, 360), "grinder_setting": random.choice(["18", "19", "20", "medium-fine", "medium"]),
            "sweetness": random.randint(6, 8), "acidity": random.randint(4, 6), "bitterness": random.randint(3, 5),
            "body": random.randint(7, 9), "aroma": random.randint(6, 8), "flavor_profile_match": random.randint(7, 9),
            "notes": random.choice(["Rich chocolate notes", "Caramel sweetness", "Full body", "Smooth chocolate finish"])
        } for _ in range(6)],
        
        # Product 4 (Hologram - Kenyan) - Multiple methods
        *[{
            "product_id": 4, "product_batch_id": 4, "brew_method_id": random.choice([1, 4, 9]),
            "recipe_id": random.choice([1, 4, 6]), "grinder_id": random.choice([4, 5, 6]),
            "filter_id": random.choice([1, 4, 6, 7]), "kettle_id": random.choice([1, 2, 4]), "scale_id": random.choice([2, 4]),
            "amount_coffee_grams": round(random.uniform(16, 22), 1), "amount_water_grams": round(random.uniform(250, 350), 0),
            "brew_temperature_c": random.randint(85, 91), "bloom_time_seconds": random.randint(25, 45),
            "brew_time_seconds": random.randint(120, 240), "grinder_setting": random.choice(["fine", "medium-fine", "16", "18", "20"]),
            "sweetness": random.randint(7, 9), "acidity": random.randint(8, 10), "bitterness": random.randint(1, 3),
            "body": random.randint(6, 8), "aroma": random.randint(7, 9), "flavor_profile_match": random.randint(8, 10),
            "notes": random.choice(["Wine-like acidity", "Bright and complex", "Fruity characteristics", "Kenyan brightness"])
        } for _ in range(7)],
        
        # Additional sessions for other products
        *[{
            "product_id": random.choice([3, 5, 6]), "product_batch_id": random.choice([3, 6, 7]),
            "brew_method_id": random.choice([1, 2, 3, 4]), "recipe_id": random.choice([1, 2, 3, 4, 5]),
            "grinder_id": random.choice([1, 2, 3, 4, 5, 6, 7]), "filter_id": random.choice([1, 2, 3, 4, 5]),
            "kettle_id": random.choice([1, 2, 3, 4, 5]), "scale_id": random.choice([1, 2, 3, 4, 5]),
            "amount_coffee_grams": round(random.uniform(15, 35), 1), "amount_water_grams": round(random.uniform(240, 560), 0),
            "brew_temperature_c": random.randint(85, 98), "bloom_time_seconds": random.randint(20, 90),
            "brew_time_seconds": random.randint(90, 420), "grinder_setting": random.choice(["fine", "medium-fine", "medium", "coarse", "14", "16", "18", "20", "22", "24"]),
            "sweetness": random.randint(4, 9), "acidity": random.randint(3, 8), "bitterness": random.randint(2, 7),
            "body": random.randint(5, 9), "aroma": random.randint(5, 9), "flavor_profile_match": random.randint(5, 9),
            "notes": random.choice(["Good extraction", "Nice balance", "Could be better", "Solid cup", "Pleasant brew", "Well-executed"])
        } for _ in range(10)]
    ]
    
    for i, template in enumerate(session_templates):
        session = template.copy()
        session["id"] = session_id
        session["timestamp"] = (base_date + timedelta(days=i)).strftime("%Y-%m-%dT%H:%M:%S")
        sessions.append(session)
        session_id += 1
    
    return sessions

brew_sessions = generate_brew_sessions()

def generate_shots():
    """Generate realistic espresso shot data with proper ratios and extraction status"""
    shots = []
    
    # Use products 1, 3, 4 (good espresso products) and batches 1, 3, 4
    espresso_setups = [
        {"product_id": 1, "product_batch_id": 1, "brewer_id": 2},  # Gaggia Classic Pro
        {"product_id": 3, "product_batch_id": 3, "brewer_id": 3},  # Rancilio Silvia 
        {"product_id": 4, "product_batch_id": 4, "brewer_id": 1},  # Breville Bambino
    ]
    
    extraction_statuses = ["perfect", "under-extracted", "over-extracted", "channeling"]
    
    shot_id = 1
    for i in range(20):  # Generate 20 shots
        setup = random.choice(espresso_setups)
        
        # Realistic espresso parameters
        dose_grams = round(random.uniform(17.0, 21.0), 1)
        yield_grams = round(random.uniform(30.0, 45.0), 1)
        dose_yield_ratio = round(yield_grams / dose_grams, 1)
        
        # Extraction time typically 25-35 seconds
        extraction_time = random.randint(22, 38)
        
        # Water temperature for espresso
        water_temp = random.randint(88, 94)
        
        # Equipment selection
        portafilter_id = random.choice([1, 2, 4])  # 58mm portafilters
        basket_id = random.choice([1, 2, 3]) if dose_grams >= 18 else 1
        tamper_id = random.choice([1, 2, 3])
        wdt_tool_id = random.choice([1, 2, None])
        leveling_tool_id = random.choice([1, 2, None])
        grinder_id = random.choice([2, 3, 4, 5, 7])  # Better grinders for espresso
        
        # Extraction status - bias toward good shots
        extraction_status = random.choices(
            extraction_statuses, 
            weights=[50, 20, 20, 10]  # 50% perfect, 20% under/over, 10% channeling
        )[0]
        
        # Tasting scores based on extraction status
        if extraction_status == "perfect":
            sweetness = random.randint(8, 10)
            acidity = random.randint(6, 9)
            body = random.randint(8, 10)
            aroma = random.randint(7, 10)
            bitterness = random.randint(1, 3)
            overall_score = random.randint(8, 10)
        elif extraction_status == "under-extracted":
            sweetness = random.randint(4, 6)
            acidity = random.randint(7, 10)
            body = random.randint(3, 6)
            aroma = random.randint(5, 7)
            bitterness = random.randint(1, 2)
            overall_score = random.randint(4, 6)
        elif extraction_status == "over-extracted":
            sweetness = random.randint(2, 5)
            acidity = random.randint(2, 5)
            body = random.randint(7, 9)
            aroma = random.randint(4, 7)
            bitterness = random.randint(7, 10)
            overall_score = random.randint(3, 6)
        else:  # channeling
            sweetness = random.randint(3, 6)
            acidity = random.randint(4, 8)
            body = random.randint(2, 5)
            aroma = random.randint(3, 6)
            bitterness = random.randint(4, 8)
            overall_score = random.randint(2, 5)
        
        # Random timestamp within last 30 days
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        
        shot = {
            "id": shot_id,
            "product_id": setup["product_id"],
            "product_batch_id": setup["product_batch_id"],
            "brewer_id": setup["brewer_id"],
            "shot_session_id": None,  # Will be assigned when sessions are created
            "dose_grams": dose_grams,
            "yield_grams": yield_grams,
            "dose_yield_ratio": dose_yield_ratio,
            "extraction_time_seconds": extraction_time,
            "water_temperature_c": water_temp,
            "portafilter_id": portafilter_id,
            "basket_id": basket_id,
            "tamper_id": tamper_id,
            "wdt_tool_id": wdt_tool_id,
            "leveling_tool_id": leveling_tool_id,
            "grinder_id": grinder_id,
            "grinder_setting": random.choice(["fine", "extra fine", "1", "2", "3", "4", "5"]),
            "extraction_status": extraction_status,
            "sweetness": sweetness,
            "acidity": acidity,
            "body": body,
            "aroma": aroma,
            "bitterness": bitterness,
            "overall_score": overall_score,
            "notes": random.choice([
                "Good crema formation",
                "Nice chocolate notes",
                "Bright citrus finish",
                "Smooth and balanced",
                "Rich body with caramel sweetness",
                "Clean finish",
                "Slightly sour - adjust grind finer",
                "Too bitter - try coarser grind",
                "Perfect extraction today",
                "Channeling visible in naked portafilter",
                ""
            ]),
            "timestamp": timestamp.isoformat()
        }
        shots.append(shot)
        shot_id += 1
    
    return shots

def generate_shot_sessions(shots):
    """Generate shot sessions and assign shots to them"""
    sessions = []
    session_id = 1
    
    # Create 4 shot sessions with varying numbers of shots
    session_configs = [
        {"name": "Morning Dialing Session", "product_id": 1, "product_batch_id": 1, "brewer_id": 2, "shots_count": 5},
        {"name": "Weekend Practice", "product_id": 3, "product_batch_id": 3, "brewer_id": 3, "shots_count": 4},
        {"name": "New Bean Exploration", "product_id": 4, "product_batch_id": 4, "brewer_id": 1, "shots_count": 3},
        {"name": "Dialing Competition Shot", "product_id": 1, "product_batch_id": 1, "brewer_id": 4, "shots_count": 6}
    ]
    
    shot_index = 0
    
    for config in session_configs:
        # Create session
        days_ago = random.randint(1, 15)
        created_at = datetime.now() - timedelta(days=days_ago)
        
        session = {
            "id": session_id,
            "session_name": config["name"],
            "product_id": config["product_id"],
            "product_batch_id": config["product_batch_id"],
            "brewer_id": config["brewer_id"],
            "notes": random.choice([
                "Working on dialing in this new batch",
                "Experimenting with different dose ratios",
                "Trying to reduce channeling issues",
                "Perfecting extraction timing",
                "Testing new tamping technique",
                "Comparing different baskets"
            ]),
            "created_at": created_at.isoformat()
        }
        sessions.append(session)
        
        # Assign shots to this session
        shots_to_assign = min(config["shots_count"], len(shots) - shot_index)
        for i in range(shots_to_assign):
            if shot_index < len(shots):
                shots[shot_index]["shot_session_id"] = session_id
                # Update shot timestamp to be within the session timeframe
                shot_time = created_at + timedelta(minutes=random.randint(5, 120))
                shots[shot_index]["timestamp"] = shot_time.isoformat()
                shot_index += 1
        
        session_id += 1
    
    return sessions

# Generate espresso data
shots = generate_shots()
shot_sessions = generate_shot_sessions(shots)

# Write JSON files
files_to_create = [
    ('roasters.json', roasters),
    ('bean_types.json', bean_types),
    ('countries.json', countries),
    ('regions.json', regions),
    ('brew_methods.json', brew_methods),
    ('recipes.json', recipes),
    ('decaf_methods.json', decaf_methods),
    ('brewers.json', brewers),
    ('portafilters.json', portafilters),
    ('baskets.json', baskets),
    ('tampers.json', tampers),
    ('wdt_tools.json', wdt_tools),
    ('leveling_tools.json', leveling_tools),
    ('grinders.json', grinders),
    ('filters.json', filters),
    ('kettles.json', kettles),
    ('scales.json', scales),
    ('products.json', products),
    ('batches.json', batches),
    ('brew_sessions.json', brew_sessions),
    ('shots.json', shots),
    ('shot_sessions.json', shot_sessions)
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
print(f"  - {len(brewers)} brewers (espresso machines & pour-over)")
print(f"  - {len(portafilters)} portafilters")
print(f"  - {len(baskets)} baskets")
print(f"  - {len(tampers)} tampers")
print(f"  - {len(wdt_tools)} WDT tools")
print(f"  - {len(leveling_tools)} leveling tools")
print(f"  - {len(grinders)} grinders")
print(f"  - {len(filters)} filters")
print(f"  - {len(kettles)} kettles")
print(f"  - {len(scales)} scales")
print(f"  - {len(products)} products")
print(f"  - {len(batches)} batches")
print(f"  - {len(brew_sessions)} brew sessions")
print(f"  - {len(shots)} shots (espresso)")
print(f"  - {len(shot_sessions)} shot sessions")