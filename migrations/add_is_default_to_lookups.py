"""
Migration to add is_default field to all lookup tables.
"""
import json
import os
from pathlib import Path


def migrate_lookup_add_is_default(data_dir: str, filename: str):
    """Add is_default field to all items in a lookup table, defaulting to False."""
    lookup_file = Path(data_dir) / filename
    
    if not lookup_file.exists():
        print(f"No {filename} file found, skipping migration")
        return
    
    # Read existing lookup items
    with open(lookup_file, 'r') as f:
        items = json.load(f)
    
    # Add is_default field to items that don't have it
    modified = False
    for item in items:
        if 'is_default' not in item:
            item['is_default'] = False
            modified = True
    
    # Write back if any changes were made
    if modified:
        with open(lookup_file, 'w') as f:
            json.dump(items, f, indent=2)
        print(f"Added is_default field to {len(items)} items in {filename}")
    else:
        print(f"All items in {filename} already have is_default field")


def migrate_all_lookups_add_is_default(data_dir: str):
    """Add is_default field to all lookup tables."""
    lookup_files = [
        'roasters.json',
        'bean_types.json', 
        'countries.json',
        'brew_methods.json',
        'recipes.json',
        'decaf_methods.json',
        'grinders.json',
        'filters.json',
        'kettles.json',
        'scales.json'
    ]
    
    for filename in lookup_files:
        migrate_lookup_add_is_default(data_dir, filename)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        data_dir = "test_data"
    
    migrate_all_lookups_add_is_default(data_dir)