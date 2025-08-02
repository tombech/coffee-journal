"""
Migration from schema v1.1 to v1.2

Changes:
- Add audit timestamps (created_at, updated_at) to all entities
- Add is_active flag to batches
- Add is_default flag to all lookup tables
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone


def migrate_1_1_to_1_2(data_dir: str):
    """Migrate data from v1.1 to v1.2"""
    print("Starting migration from v1.1 to v1.2...")
    
    # Add audit timestamps to all JSON files
    add_audit_timestamps_to_all_files(data_dir)
    
    # Add is_active to batches
    add_is_active_to_batches(data_dir)
    
    # Add is_default to all lookup tables
    add_is_default_to_lookups(data_dir)
    
    print("Migration v1.1 -> v1.2 completed successfully")
    print("New features: audit timestamps, batch active flags, default lookup system")


def add_audit_timestamps_to_all_files(data_dir: str):
    """Add created_at and updated_at to all JSON files"""
    data_path = Path(data_dir)
    
    # Default timestamp for existing data
    default_timestamp = datetime.now(timezone.utc).isoformat()
    
    # Files to update
    json_files = [
        'products.json', 'batches.json', 'brew_sessions.json',
        'roasters.json', 'bean_types.json', 'countries.json', 
        'brew_methods.json', 'recipes.json', 'decaf_methods.json',
        'grinders.json', 'filters.json', 'kettles.json', 'scales.json'
    ]
    
    for filename in json_files:
        file_path = data_path / filename
        if file_path.exists():
            add_audit_timestamps_to_file(file_path, default_timestamp)


def add_audit_timestamps_to_file(file_path: Path, default_timestamp: str):
    """Add audit timestamps to a specific JSON file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    modified = False
    for item in data:
        if 'created_at' not in item:
            item['created_at'] = default_timestamp
            modified = True
        if 'updated_at' not in item:
            item['updated_at'] = default_timestamp
            modified = True
    
    if modified:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Added audit timestamps to {file_path.name}")


def add_is_active_to_batches(data_dir: str):
    """Add is_active field to batches"""
    batches_file = Path(data_dir) / 'batches.json'
    
    if not batches_file.exists():
        return
    
    with open(batches_file, 'r') as f:
        batches = json.load(f)
    
    modified = False
    for batch in batches:
        if 'is_active' not in batch:
            batch['is_active'] = True
            modified = True
    
    if modified:
        with open(batches_file, 'w') as f:
            json.dump(batches, f, indent=2)
        print(f"Added is_active field to {len(batches)} batches")


def add_is_default_to_lookups(data_dir: str):
    """Add is_default field to all lookup tables"""
    lookup_files = [
        'roasters.json', 'bean_types.json', 'countries.json',
        'brew_methods.json', 'recipes.json', 'decaf_methods.json',
        'grinders.json', 'filters.json', 'kettles.json', 'scales.json'
    ]
    
    for filename in lookup_files:
        file_path = Path(data_dir) / filename
        if file_path.exists():
            add_is_default_to_lookup_file(file_path)


def add_is_default_to_lookup_file(file_path: Path):
    """Add is_default field to a specific lookup file"""
    with open(file_path, 'r') as f:
        items = json.load(f)
    
    modified = False
    for item in items:
        if 'is_default' not in item:
            item['is_default'] = False
            modified = True
    
    if modified:
        with open(file_path, 'w') as f:
            json.dump(items, f, indent=2)
        print(f"Added is_default field to {len(items)} items in {file_path.name}")


# Register this migration
def register_migration(migration_manager):
    """Register this migration with the migration manager"""
    migration_manager.migrations["1.1->1.2"] = migrate_1_1_to_1_2