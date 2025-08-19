#!/usr/bin/env python3
"""Script to clean corrupted data by stripping enriched fields."""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Schema definitions for each file type
SCHEMAS = {
    'brew_sessions.json': {
        'properties': {
            'id': {},
            'timestamp': {},
            'product_batch_id': {},
            'product_id': {},
            'brew_method_id': {},
            'recipe_id': {},
            'grinder_id': {},
            'grinder_setting': {},
            'filter_id': {},
            'kettle_id': {},
            'scale_id': {},
            'amount_coffee_grams': {},
            'amount_water_grams': {},
            'brew_temperature_c': {},
            'bloom_time_seconds': {},
            'brew_time_seconds': {},
            'sweetness': {},
            'acidity': {},
            'bitterness': {},
            'body': {},
            'aroma': {},
            'flavor_profile_match': {},
            'score': {},
            'notes': {},
            'created_at': {},
            'updated_at': {}
        }
    },
    'shots.json': {
        'properties': {
            'id': {},
            'product_batch_id': {},
            'product_id': {},
            'brewer_id': {},
            'grinder_id': {},
            'portafilter_id': {},
            'basket_id': {},
            'scale_id': {},
            'tamper_id': {},
            'leveling_tool_id': {},
            'wdt_tool_id': {},
            'dose_grams': {},
            'yield_grams': {},
            'preinfusion_seconds': {},
            'extraction_time_seconds': {},
            'pressure_bars': {},
            'water_temperature_c': {},
            'grinder_setting': {},
            'sweetness': {},
            'acidity': {},
            'bitterness': {},
            'body': {},
            'aroma': {},
            'crema': {},
            'flavor_profile_match': {},
            'extraction_status': {},
            'notes': {},
            'timestamp': {},
            'created_at': {},
            'updated_at': {},
            'ratio': {},
            'shot_session_id': {},
            'shot_number': {}
        }
    },
    'shot_sessions.json': {
        'properties': {
            'id': {},
            'title': {},
            'session_name': {},
            'product_id': {},
            'product_batch_id': {},
            'brewer_id': {},
            'notes': {},
            'created_at': {},
            'updated_at': {}
        }
    }
}

def strip_enriched_fields(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """Strip any fields not in the schema."""
    if 'properties' not in schema:
        return data
    
    allowed_fields = set(schema['properties'].keys())
    cleaned = {}
    for key, value in data.items():
        if key in allowed_fields:
            cleaned[key] = value
    
    return cleaned

def clean_file(filepath: Path) -> bool:
    """Clean a single JSON file by removing enriched fields."""
    filename = filepath.name
    
    # Skip if we don't have a schema for this file
    if filename not in SCHEMAS:
        print(f"  ⚠️  No schema defined for {filename}, skipping")
        return False
    
    schema = SCHEMAS[filename]
    
    try:
        # Read the file
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"  ⚠️  {filename} is not a list, skipping")
            return False
        
        # Track if we made any changes
        changed = False
        cleaned_data = []
        
        for item in data:
            cleaned_item = strip_enriched_fields(item, schema)
            if len(cleaned_item) != len(item):
                changed = True
                removed_fields = set(item.keys()) - set(cleaned_item.keys())
                print(f"  ✓ Removed fields from item {item.get('id', '?')}: {removed_fields}")
            cleaned_data.append(cleaned_item)
        
        if changed:
            # Backup original file
            backup_path = filepath.with_suffix('.json.corrupted')
            filepath.rename(backup_path)
            print(f"  📦 Backed up original to {backup_path.name}")
            
            # Write cleaned data
            with open(filepath, 'w') as f:
                json.dump(cleaned_data, f, indent=2)
            
            print(f"  ✅ Cleaned {filename} - removed enriched fields from {sum(1 for i, item in enumerate(data) if len(strip_enriched_fields(item, schema)) != len(item))} items")
            return True
        else:
            print(f"  ✓ {filename} is already clean")
            return False
            
    except Exception as e:
        print(f"  ❌ Error cleaning {filename}: {e}")
        return False

def main():
    """Main function to clean corrupted data."""
    if len(sys.argv) < 2:
        print("Usage: python clean_corrupted_data.py <directory>")
        print("Example: python clean_corrupted_data.py ./temp")
        sys.exit(1)
    
    directory = Path(sys.argv[1])
    if not directory.exists():
        print(f"❌ Directory {directory} does not exist")
        sys.exit(1)
    
    print(f"🧹 Cleaning corrupted data in {directory}")
    print("-" * 50)
    
    files_to_clean = ['brew_sessions.json', 'shots.json', 'shot_sessions.json']
    cleaned_count = 0
    
    for filename in files_to_clean:
        filepath = directory / filename
        if filepath.exists():
            print(f"\n📄 Processing {filename}...")
            if clean_file(filepath):
                cleaned_count += 1
        else:
            print(f"\n⚠️  {filename} not found in {directory}")
    
    print("\n" + "=" * 50)
    print(f"✅ Cleaned {cleaned_count} files")
    
    # Also clean any backup directories
    backup_dirs = list(directory.glob('backup_*'))
    if backup_dirs:
        print(f"\n📁 Found {len(backup_dirs)} backup directories")
        for backup_dir in backup_dirs:
            print(f"\n  Processing {backup_dir.name}...")
            for filename in files_to_clean:
                filepath = backup_dir / filename
                if filepath.exists():
                    clean_file(filepath)

if __name__ == "__main__":
    main()