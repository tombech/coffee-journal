"""
Migration from schema v1.2 to v1.3

Changes:
- Separate regions into own lookup table with country_id parent reference
- Fix lookup update_references functions to use ID fields instead of names
- Remove denormalized name fields from products (schema compliance)
- Add inline region management in country edit pages
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any


def migrate_1_2_to_1_3(data_dir: str):
    """Migrate data from v1.2 to v1.3"""
    try:
        print("Starting migration from v1.2 to v1.3...")
        
        # Check if migration has already been applied
        regions_file = os.path.join(data_dir, 'regions.json')
        if os.path.exists(regions_file):
            print("Migration already applied: regions.json exists")
            # Ensure schema compliance by checking product structure
            products = load_json_file(data_dir, 'products.json')
            needs_product_update = False
            for product in products:
                if any(field in product for field in ['roaster', 'bean_type', 'country', 'region', 'decaf_method']):
                    needs_product_update = True
                    break
            
            if needs_product_update:
                print("Cleaning up remaining denormalized fields...")
                update_products_schema_compliance(data_dir, products, {})
            else:
                print("Products already schema compliant")
            return
        
        # Load required data
        products = load_json_file(data_dir, 'products.json')
        countries = load_json_file(data_dir, 'countries.json')

        # Skip migration if no data exists (fresh environment)
        if not products and not countries:
            print("Migration v1.2 -> v1.3 skipped - no data files found (fresh environment)")
            return

        # Extract unique regions from products
        regions, region_name_to_id = extract_regions_from_products(products, countries)

        # Create regions.json file
        create_regions_file(data_dir, regions)

        # Update products to use region_id arrays and remove denormalized fields
        update_products_schema_compliance(data_dir, products, region_name_to_id)
        
        print("Migration v1.2 -> v1.3 completed successfully")
        print("New features: separate regions table, schema compliance, inline region management")
        
    except Exception as e:
        print(f"Migration v1.2 -> v1.3 failed with error: {e}")
        print("This might indicate mixed data states or corrupted data files")
        
        # Try to provide helpful debugging info
        try:
            products = load_json_file(data_dir, 'products.json')
            print(f"Found {len(products)} products in data")
            if products:
                sample_product = products[0]
                print(f"Sample product keys: {list(sample_product.keys())}")
                if 'region' in sample_product:
                    print(f"Region field type: {type(sample_product['region'])}")
                if 'region_id' in sample_product:
                    print(f"Region_id field type: {type(sample_product['region_id'])}")
        except Exception as debug_err:
            print(f"Could not load debug info: {debug_err}")
        
        raise e


def load_json_file(data_dir: str, filename: str) -> Any:
    """Load JSON data from file."""
    file_path = os.path.join(data_dir, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return empty list for missing files in fresh environments
        return []
    except Exception as e:
        raise Exception(f"Failed to load {filename}: {e}")


def save_json_file(data_dir: str, filename: str, data: Any) -> None:
    """Save JSON data to file."""
    file_path = os.path.join(data_dir, filename)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise Exception(f"Failed to save {filename}: {e}")


def extract_regions_from_products(products: List[Dict], countries: List[Dict]) -> tuple[List[Dict], Dict[str, int]]:
    """Extract unique region data from products and create mapping."""
    print(f"Extracting regions from {len(products)} products...")
    
    # Create country name to ID mapping
    country_map = {country['name']: country['id'] for country in countries}
    print(f"Found {len(countries)} countries in mapping")
    
    # Collect unique regions with their country associations
    region_data = {}  # region_name -> {country_id, country_name}
    products_with_regions = 0
    products_already_v13 = 0
    products_without_regions = 0
    
    for i, product in enumerate(products):
        region_name = product.get('region')
        country_name = product.get('country')
        country_id = product.get('country_id')
        
        if i < 3:  # Log first 3 products for debugging
            print(f"Product {i+1}: region={region_name} (type: {type(region_name)}), country_id={country_id}")
        
        # Handle both string and list region data (mixed migration state)
        if region_name:
            if isinstance(region_name, str) and region_name.strip() and country_id:
                if region_name not in region_data:
                    region_data[region_name] = {
                        'country_id': country_id,
                        'country_name': country_name
                    }
                    products_with_regions += 1
            elif isinstance(region_name, list):
                # Data is already in v1.3 format, skip this product
                products_already_v13 += 1
                continue
        else:
            products_without_regions += 1
    
    print(f"Region extraction summary:")
    print(f"  Products with string regions (v1.2): {products_with_regions}")
    print(f"  Products with array regions (v1.3): {products_already_v13}")
    print(f"  Products without regions: {products_without_regions}")
    print(f"  Unique regions found: {len(region_data)}")
    
    # Convert to regions list with auto-incrementing IDs
    regions = []
    region_name_to_id = {}
    timestamp = datetime.now(timezone.utc).isoformat()
    
    for idx, (region_name, info) in enumerate(sorted(region_data.items()), 1):
        region = {
            'id': idx,
            'name': region_name,
            'country_id': info['country_id'],
            'is_default': False,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        regions.append(region)
        region_name_to_id[region_name] = idx
    
    return regions, region_name_to_id


def create_regions_file(data_dir: str, regions: List[Dict]) -> None:
    """Create the new regions.json file."""
    regions_file = os.path.join(data_dir, 'regions.json')
    
    if os.path.exists(regions_file):
        print(f"WARNING: regions.json already exists. Backing up to regions.json.bak")
        backup_file = regions_file + '.bak'
        with open(regions_file, 'r') as src, open(backup_file, 'w') as dst:
            dst.write(src.read())
    
    save_json_file(data_dir, 'regions.json', regions)
    print(f"✓ Created regions.json with {len(regions)} regions")


def update_products_schema_compliance(data_dir: str, products: List[Dict], region_name_to_id: Dict[str, int]) -> None:
    """Update products to use region_id arrays and remove denormalized name fields."""
    updated_count = 0
    
    for product in products:
        region_name = product.get('region')
        
        # Handle region_id conversion
        if region_name and isinstance(region_name, str) and region_name.strip() and region_name in region_name_to_id:
            product['region_id'] = [region_name_to_id[region_name]]
            updated_count += 1
        else:
            # Standardize region_id to always be an array (empty if no regions)
            existing_region_id = product.get('region_id')
            if existing_region_id is None:
                product['region_id'] = []
            elif isinstance(existing_region_id, int):
                product['region_id'] = [existing_region_id]
            elif not isinstance(existing_region_id, list):
                product['region_id'] = []
        
        # Standardize bean_type_id to always be an array
        existing_bean_type_id = product.get('bean_type_id')
        if existing_bean_type_id is None:
            product['bean_type_id'] = []
        elif isinstance(existing_bean_type_id, int):
            product['bean_type_id'] = [existing_bean_type_id]
        elif not isinstance(existing_bean_type_id, list):
            product['bean_type_id'] = []
        
        # Remove denormalized name fields (schema compliance)
        denormalized_fields = ['roaster', 'bean_type', 'country', 'region', 'decaf_method']
        for field in denormalized_fields:
            if field in product:
                del product[field]
    
    save_json_file(data_dir, 'products.json', products)
    print(f"✓ Updated {updated_count} products with region_id arrays")
    print("✓ Standardized bean_type_id and region_id to always be arrays")
    print("✓ Removed denormalized name fields for schema compliance")