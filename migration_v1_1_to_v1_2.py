#!/usr/bin/env python3
"""
Migration script from schema v1.1 to v1.2

Adds:
- manually_ground_grams field to grinders (defaults to 0)
- Ensures all lookup items have is_default field (defaults to False)
- Ensures all batches have is_active field (defaults to True)
- Ensures all entities have audit timestamps
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def migrate_grinders(data_dir: Path):
    """Add manually_ground_grams field to grinders."""
    grinders_file = data_dir / 'grinders.json'
    if not grinders_file.exists():
        print("No grinders.json file found, skipping grinder migration")
        return
    
    with open(grinders_file, 'r') as f:
        grinders = json.load(f)
    
    modified = False
    for grinder in grinders:
        if 'manually_ground_grams' not in grinder:
            grinder['manually_ground_grams'] = 0
            modified = True
            print(f"Added manually_ground_grams field to grinder: {grinder.get('name', grinder.get('id'))}")
    
    if modified:
        with open(grinders_file, 'w') as f:
            json.dump(grinders, f, indent=2)
        print(f"Updated {len(grinders)} grinder(s)")
    else:
        print("All grinders already have manually_ground_grams field")


def migrate_lookup_defaults(data_dir: Path):
    """Ensure all lookup items have is_default field."""
    lookup_files = [
        'roasters.json', 'bean_types.json', 'countries.json', 'brew_methods.json',
        'recipes.json', 'decaf_methods.json', 'grinders.json', 'filters.json',
        'kettles.json', 'scales.json'
    ]
    
    for filename in lookup_files:
        file_path = data_dir / filename
        if not file_path.exists():
            print(f"No {filename} file found, skipping")
            continue
        
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
            print(f"Updated {len(items)} item(s) in {filename}")


def migrate_batch_active(data_dir: Path):
    """Ensure all batches have is_active field."""
    batches_file = data_dir / 'batches.json'
    if not batches_file.exists():
        print("No batches.json file found, skipping batch migration")
        return
    
    with open(batches_file, 'r') as f:
        batches = json.load(f)
    
    modified = False
    for batch in batches:
        if 'is_active' not in batch:
            batch['is_active'] = True
            modified = True
            print(f"Added is_active field to batch: {batch.get('id')}")
    
    if modified:
        with open(batches_file, 'w') as f:
            json.dump(batches, f, indent=2)
        print(f"Updated {len(batches)} batch(es)")
    else:
        print("All batches already have is_active field")


def migrate_audit_timestamps(data_dir: Path):
    """Ensure all entities have audit timestamps."""
    all_files = [
        'roasters.json', 'bean_types.json', 'countries.json', 'brew_methods.json',
        'recipes.json', 'decaf_methods.json', 'grinders.json', 'filters.json',
        'kettles.json', 'scales.json', 'products.json', 'batches.json', 'brew_sessions.json'
    ]
    
    default_timestamp = datetime.now(timezone.utc).isoformat()
    
    for filename in all_files:
        file_path = data_dir / filename
        if not file_path.exists():
            print(f"No {filename} file found, skipping")
            continue
        
        with open(file_path, 'r') as f:
            items = json.load(f)
        
        modified = False
        for item in items:
            if 'created_at' not in item:
                item['created_at'] = default_timestamp
                modified = True
            if 'updated_at' not in item:
                item['updated_at'] = default_timestamp
                modified = True
        
        if modified:
            with open(file_path, 'w') as f:
                json.dump(items, f, indent=2)
            print(f"Updated audit timestamps in {filename}")


def update_schema_version(data_dir: Path):
    """Update schema version to 1.2."""
    schema_file = data_dir / 'data_version.json'
    if schema_file.exists():
        with open(schema_file, 'r') as f:
            schema_data = json.load(f)
    else:
        schema_data = {}
    
    schema_data.update({
        "schema_version": "1.2",
        "migration_date": datetime.now(timezone.utc).isoformat(),
        "description": "Added audit timestamps, batch active flags, grinder tracking, and default/favorite lookup system"
    })
    
    with open(schema_file, 'w') as f:
        json.dump(schema_data, f, indent=2)
    
    print(f"Updated schema version to 1.2 in {schema_file}")


def main():
    """Run the migration."""
    # Get data directory from environment or use default
    data_dir = Path(os.getenv('DATA_DIR', 'test_data'))
    
    if not data_dir.exists():
        print(f"Data directory {data_dir} does not exist!")
        return
    
    print(f"Migrating data in {data_dir} from schema v1.1 to v1.2...")
    print()
    
    # Run all migrations
    migrate_audit_timestamps(data_dir)
    migrate_lookup_defaults(data_dir)
    migrate_batch_active(data_dir)
    migrate_grinders(data_dir)
    update_schema_version(data_dir)
    
    print()
    print("Migration completed successfully!")


if __name__ == '__main__':
    main()
