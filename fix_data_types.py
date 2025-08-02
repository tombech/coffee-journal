#!/usr/bin/env python3
"""
Data Type Conversion Script for Coffee Journal

This script converts string values to proper numeric types in JSON data files.
Run this script in a data directory containing the JSON files.

Usage: python fix_data_types.py [data_directory]
"""

import json
import os
import sys
from pathlib import Path


def safe_float(value):
    """Safely convert a value to float, returning None if conversion fails."""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_int(value):
    """Safely convert a value to int, returning None if conversion fails."""
    if value is None or value == '':
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def clamp_tasting_score(value):
    """Clamp tasting scores to 1-10 range."""
    if value is None:
        return None
    return max(1, min(10, value))


def clamp_overall_score(value):
    """Clamp overall scores to 1.0-10.0 range."""
    if value is None:
        return None
    return max(1.0, min(10.0, value))


def fix_brew_session_data(session):
    """Fix numeric types in a brew session object."""
    # Convert numeric fields
    session['amount_coffee_grams'] = safe_float(session.get('amount_coffee_grams'))
    session['amount_water_grams'] = safe_float(session.get('amount_water_grams'))
    session['brew_temperature_c'] = safe_int(session.get('brew_temperature_c'))
    session['bloom_time_seconds'] = safe_int(session.get('bloom_time_seconds'))
    session['brew_time_seconds'] = safe_int(session.get('brew_time_seconds'))
    
    # Convert and clamp tasting scores (1-10 range)
    tasting_fields = ['sweetness', 'acidity', 'bitterness', 'body', 'aroma', 'flavor_profile_match']
    for field in tasting_fields:
        value = safe_int(session.get(field))
        if value is not None:
            session[field] = clamp_tasting_score(value)
    
    # Convert and clamp overall score (1.0-10.0 range)
    score = safe_float(session.get('score'))
    if score is not None:
        session[field] = clamp_overall_score(score)
    else:
        # Handle empty string case
        score_val = session.get('score')
        if score_val == '':
            session['score'] = None
    
    return session


def fix_batch_data(batch):
    """Fix numeric types in a batch object."""
    batch['amount_grams'] = safe_float(batch.get('amount_grams'))
    batch['price'] = safe_float(batch.get('price'))
    batch['rating'] = safe_int(batch.get('rating'))
    
    return batch


def fix_product_data(product):
    """Fix numeric types in a product object."""
    product['roast_type'] = safe_int(product.get('roast_type'))
    product['rating'] = safe_int(product.get('rating'))
    
    return product


def process_json_file(file_path):
    """Process a JSON file and fix data types."""
    print(f"Processing {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Backup original file
        backup_path = f"{file_path}.backup"
        if not os.path.exists(backup_path):
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  Created backup: {backup_path}")
        
        changes_made = 0
        
        # Determine file type and process accordingly
        if 'brew_sessions.json' in str(file_path):
            for session in data:
                original = json.dumps(session, sort_keys=True)
                fix_brew_session_data(session)
                if json.dumps(session, sort_keys=True) != original:
                    changes_made += 1
                    
        elif 'batches.json' in str(file_path):
            for batch in data:
                original = json.dumps(batch, sort_keys=True)
                fix_batch_data(batch)
                if json.dumps(batch, sort_keys=True) != original:
                    changes_made += 1
                    
        elif 'products.json' in str(file_path):
            for product in data:
                original = json.dumps(product, sort_keys=True)
                fix_product_data(product)
                if json.dumps(product, sort_keys=True) != original:
                    changes_made += 1
        
        # Write back the fixed data
        if changes_made > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  Fixed {changes_made} records")
        else:
            print(f"  No changes needed")
            
        return changes_made
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return 0


def main():
    """Main function."""
    # Get data directory from command line or use current directory
    if len(sys.argv) > 1:
        data_dir = Path(sys.argv[1])
    else:
        data_dir = Path('.')
    
    if not data_dir.exists():
        print(f"ERROR: Directory {data_dir} does not exist")
        sys.exit(1)
    
    print(f"Fixing data types in JSON files in: {data_dir.absolute()}")
    print()
    
    # Find JSON files to process
    json_files = [
        'brew_sessions.json',
        'batches.json', 
        'products.json'
    ]
    
    total_changes = 0
    
    for filename in json_files:
        file_path = data_dir / filename
        if file_path.exists():
            changes = process_json_file(file_path)
            total_changes += changes
        else:
            print(f"Skipping {filename} (not found)")
    
    print()
    print(f"Data type conversion complete!")
    print(f"Total records modified: {total_changes}")
    
    if total_changes > 0:
        print()
        print("IMPORTANT:")
        print("- Backup files (.backup) have been created")
        print("- Numeric fields have been converted to proper types")
        print("- Tasting scores have been clamped to 1-10 range")
        print("- Overall scores have been clamped to 1.0-10.0 range")
        print("- Empty string scores have been converted to null")


if __name__ == '__main__':
    main()