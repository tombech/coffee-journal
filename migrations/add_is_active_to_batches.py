"""
Migration to add is_active field to existing batches.
"""
import json
import os
from pathlib import Path


def migrate_batches_add_is_active(data_dir: str):
    """Add is_active field to all existing batches, defaulting to True."""
    batches_file = Path(data_dir) / 'batches.json'
    
    if not batches_file.exists():
        print("No batches.json file found, skipping migration")
        return
    
    # Read existing batches
    with open(batches_file, 'r') as f:
        batches = json.load(f)
    
    # Add is_active field to batches that don't have it
    modified = False
    for batch in batches:
        if 'is_active' not in batch:
            batch['is_active'] = True
            modified = True
    
    # Write back if any changes were made
    if modified:
        with open(batches_file, 'w') as f:
            json.dump(batches, f, indent=2)
        print(f"Added is_active field to {len([b for b in batches if b.get('is_active') is True])} batches")
    else:
        print("All batches already have is_active field")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        data_dir = "test_data"
    
    migrate_batches_add_is_active(data_dir)