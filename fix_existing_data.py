#!/usr/bin/env python3
"""
Fix existing data files to the new ID-only format.
This script handles any existing data that might have mixed ID/name storage.
"""
import json
import os
import glob

def backup_data_files():
    """Create backups of existing data files"""
    backup_dir = "test_data_backup"
    os.makedirs(backup_dir, exist_ok=True)
    
    data_files = glob.glob("test_data/*.json")
    for file_path in data_files:
        filename = os.path.basename(file_path)
        backup_path = os.path.join(backup_dir, filename)
        with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
    
    print(f"✅ Backed up {len(data_files)} data files to {backup_dir}/")

def fix_products_data():
    """Fix products.json to store only IDs"""
    products_file = 'test_data/products.json'
    
    if not os.path.exists(products_file):
        print(f"⚠️  {products_file} not found, skipping")
        return
    
    with open(products_file, 'r') as f:
        products = json.load(f)
    
    fixed_products = []
    for product in products:
        # Start with the core ID-based structure
        fixed_product = {
            "id": product.get("id"),
            "roaster_id": product.get("roaster_id"),
            "bean_type_id": [],
            "country_id": product.get("country_id"),
            "region_id": [],
            "product_name": product.get("product_name", ""),
            "roast_type": product.get("roast_type"),
            "description": product.get("description", ""),
            "url": product.get("url", ""),
            "image_url": product.get("image_url"),
            "decaf": product.get("decaf", False),
            "decaf_method_id": product.get("decaf_method_id"),
            "rating": product.get("rating"),
            "bean_process": product.get("bean_process", ""),
            "notes": product.get("notes", "")
        }
        
        # Handle bean_type_id - could be int, list, or missing
        if "bean_type_id" in product:
            bean_type_id = product["bean_type_id"]
            if isinstance(bean_type_id, list):
                fixed_product["bean_type_id"] = [id for id in bean_type_id if id is not None]
            elif bean_type_id is not None:
                fixed_product["bean_type_id"] = [bean_type_id]
        
        # Handle region_id - could be int, list, or missing
        if "region_id" in product:
            region_id = product["region_id"]
            if isinstance(region_id, list):
                fixed_product["region_id"] = [id for id in region_id if id is not None]
            elif region_id is not None:
                fixed_product["region_id"] = [region_id]
        
        # Remove None values and empty lists/strings where appropriate
        fixed_product = {
            k: v for k, v in fixed_product.items() 
            if v is not None and v != "" and v != []
        }
        
        # Ensure required fields exist
        if "bean_type_id" not in fixed_product:
            fixed_product["bean_type_id"] = []
        if "region_id" not in fixed_product:
            fixed_product["region_id"] = []
            
        fixed_products.append(fixed_product)
    
    with open(products_file, 'w') as f:
        json.dump(fixed_products, f, indent=2)
    
    print(f"✅ Fixed {products_file} - normalized to ID-only format")

def fix_batches_data():
    """Fix batches.json to store only IDs"""
    batches_file = 'test_data/batches.json'
    
    if not os.path.exists(batches_file):
        print(f"⚠️  {batches_file} not found, skipping")
        return
    
    with open(batches_file, 'r') as f:
        batches = json.load(f)
    
    fixed_batches = []
    for batch in batches:
        fixed_batch = {
            "id": batch.get("id"),
            "product_id": batch.get("product_id"),
            "roast_date": batch.get("roast_date"),
            "purchase_date": batch.get("purchase_date"),
            "amount_grams": batch.get("amount_grams"),
            "price": batch.get("price"),
            "seller": batch.get("seller", ""),
            "rating": batch.get("rating"),
            "notes": batch.get("notes", "")
        }
        
        # Remove None values and empty strings where appropriate
        fixed_batch = {
            k: v for k, v in fixed_batch.items() 
            if v is not None and v != ""
        }
        
        fixed_batches.append(fixed_batch)
    
    with open(batches_file, 'w') as f:
        json.dump(fixed_batches, f, indent=2)
    
    print(f"✅ Fixed {batches_file} - normalized to ID-only format")

def fix_brew_sessions_data():
    """Fix brew_sessions.json to store only IDs"""
    sessions_file = 'test_data/brew_sessions.json'
    
    if not os.path.exists(sessions_file):
        print(f"⚠️  {sessions_file} not found, skipping")
        return
    
    with open(sessions_file, 'r') as f:
        sessions = json.load(f)
    
    fixed_sessions = []
    for session in sessions:
        fixed_session = {
            "id": session.get("id"),
            "timestamp": session.get("timestamp"),
            "product_batch_id": session.get("product_batch_id"),
            "product_id": session.get("product_id"),
            "brew_method_id": session.get("brew_method_id"),
            "recipe_id": session.get("recipe_id"),
            "grinder_id": session.get("grinder_id"),
            "grinder_setting": session.get("grinder_setting", ""),
            "filter_id": session.get("filter_id"),
            "kettle_id": session.get("kettle_id"),
            "scale_id": session.get("scale_id"),
            "amount_coffee_grams": session.get("amount_coffee_grams"),
            "amount_water_grams": session.get("amount_water_grams"),
            "brew_temperature_c": session.get("brew_temperature_c"),
            "bloom_time_seconds": session.get("bloom_time_seconds"),
            "brew_time_seconds": session.get("brew_time_seconds"),
            "sweetness": session.get("sweetness"),
            "acidity": session.get("acidity"),
            "bitterness": session.get("bitterness"),
            "body": session.get("body"),
            "aroma": session.get("aroma"),
            "flavor_profile_match": session.get("flavor_profile_match"),
            "score": session.get("score"),
            "notes": session.get("notes", "")
        }
        
        # Remove None values and empty strings where appropriate
        fixed_session = {
            k: v for k, v in fixed_session.items() 
            if v is not None and v != ""
        }
        
        fixed_sessions.append(fixed_session)
    
    with open(sessions_file, 'w') as f:
        json.dump(fixed_sessions, f, indent=2)
    
    print(f"✅ Fixed {sessions_file} - normalized to ID-only format")

def verify_data_integrity():
    """Verify that all required lookup files exist"""
    required_lookup_files = [
        'test_data/roasters.json',
        'test_data/bean_types.json', 
        'test_data/countries.json',
        'test_data/brew_methods.json',
        'test_data/recipes.json',
        'test_data/grinders.json',
        'test_data/filters.json',
        'test_data/kettles.json',
        'test_data/scales.json',
        'test_data/decaf_methods.json'
    ]
    
    missing_files = []
    for file_path in required_lookup_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"⚠️  Missing lookup files: {missing_files}")
        print("   Run 'uv run python3 create_test_data.py' to create them")
        return False
    
    print("✅ All required lookup files exist")
    return True

def show_data_summary():
    """Show summary of fixed data"""
    files_info = []
    
    data_files = {
        'products.json': 'products',
        'batches.json': 'batches', 
        'brew_sessions.json': 'brew sessions',
        'roasters.json': 'roasters',
        'bean_types.json': 'bean types',
        'countries.json': 'countries',
        'brew_methods.json': 'brew methods',
        'recipes.json': 'recipes'
    }
    
    for filename, description in data_files.items():
        file_path = f'test_data/{filename}'
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                files_info.append(f"  - {len(data)} {description}")
    
    print("\n📊 Data Summary:")
    for info in files_info:
        print(info)

def main():
    print("🔧 Fixing existing data to new ID-only format...")
    print("=" * 60)
    
    # Create backups first
    backup_data_files()
    print()
    
    # Fix each data file type
    fix_products_data()
    fix_batches_data() 
    fix_brew_sessions_data()
    print()
    
    # Verify integrity
    verify_data_integrity()
    print()
    
    # Show summary
    show_data_summary()
    
    print("\n✅ Data migration complete!")
    print("\nChanges made:")
    print("  - Products: Store only roaster_id, bean_type_id[], country_id, region_id[]")
    print("  - Batches: Store only product_id and core batch data")
    print("  - Brew Sessions: Store only lookup IDs (brew_method_id, recipe_id, etc.)")
    print("  - Backend will resolve IDs to full objects when serving API responses")
    print("\nBackups created in test_data_backup/ directory")

if __name__ == "__main__":
    main()