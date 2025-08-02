"""
Migration from version 1.0 to 1.1.

Adds rich metadata fields to all lookup tables:
- short_form: Short identifier for display
- description: Detailed description
- notes: Additional notes
- url: Reference URL (product page, Wikipedia, etc.)
- image_url: Image URL
- icon: Icon filename
"""

import json
import os
from . import get_migration_manager

def migrate_1_0_to_1_1(data_dir: str):
    """
    Migration from version 1.0 to 1.1.
    
    Adds optional rich metadata fields to all lookup tables:
    - short_form, description, notes, url, image_url, icon
    
    These fields are added with empty/null default values.
    Users can populate them via the UI after migration.
    """
    
    lookup_tables = [
        'roasters.json', 'bean_types.json', 'countries.json',
        'brew_methods.json', 'recipes.json', 'decaf_methods.json',
        'grinders.json', 'filters.json', 'kettles.json', 'scales.json'
    ]
    
    new_fields = {
        'short_form': None,
        'description': None,
        'notes': None,
        'url': None,
        'image_url': None,
        'icon': None
    }
    
    for table_file in lookup_tables:
        file_path = os.path.join(data_dir, table_file)
        if os.path.exists(file_path):
            print(f"Migrating {table_file}...")
            
            with open(file_path, 'r') as f:
                items = json.load(f)
            
            # Add new fields to each item if they don't exist
            for item in items:
                for field_name, default_value in new_fields.items():
                    if field_name not in item:
                        item[field_name] = default_value
            
            # Write back to file
            with open(file_path, 'w') as f:
                json.dump(items, f, indent=2)
            
            print(f"  Added {len(new_fields)} new fields to {len(items)} items")
    
    print("Migration 1.0 -> 1.1 completed successfully")
    print("New fields added: short_form, description, notes, url, image_url, icon")
    print("All fields are optional and can be populated via the UI")

# Migration function is exported, registration happens in __init__.py