"""
Migration from schema version 1.3 to 1.4 - Espresso Support
"""

import os
import json
from datetime import datetime


def migrate_v1_3_to_v1_4(data_dir):
    """
    Migrate from schema version 1.3 to 1.4.
    
    This migration adds espresso support by creating empty files for new entity types:
    - shots.json
    - shot_sessions.json  
    - New equipment lookup files (brewers, portafilters, baskets, tampers, wdt_tools, leveling_tools)
    
    Args:
        data_dir (str): Path to the data directory
    """
    print("🔄 Migrating from schema v1.3 to v1.4 (Espresso Support)")
    
    # New files to create for espresso support
    new_files = {
        'shots.json': [],
        'shot_sessions.json': [],
        'brewers.json': [],
        'portafilters.json': [],
        'baskets.json': [],
        'tampers.json': [],
        'wdt_tools.json': [],
        'leveling_tools.json': []
    }
    
    changes_made = 0
    
    for filename, default_content in new_files.items():
        file_path = os.path.join(data_dir, filename)
        
        # Only create if file doesn't exist
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w') as f:
                    json.dump(default_content, f, indent=2)
                print(f"  ✅ Created {filename}")
                changes_made += 1
            except Exception as e:
                print(f"  ❌ Failed to create {filename}: {e}")
                raise
        else:
            print(f"  ℹ️  {filename} already exists, skipping")
    
    # Update data version file
    version_file = os.path.join(data_dir, 'data_version.json')
    try:
        version_data = {
            'version': '1.4',
            'migrated_at': datetime.utcnow().isoformat(),
            'migration_notes': 'Added espresso support - shots, shot sessions, and espresso equipment'
        }
        
        with open(version_file, 'w') as f:
            json.dump(version_data, f, indent=2)
        print(f"  ✅ Updated data_version.json to v1.4")
        changes_made += 1
    except Exception as e:
        print(f"  ❌ Failed to update version file: {e}")
        raise
    
    if changes_made > 0:
        print(f"✅ Migration v1.3→v1.4 completed successfully ({changes_made} changes)")
    else:
        print("ℹ️  Migration v1.3→v1.4 completed (no changes needed)")
    
    return True


# Migration metadata
MIGRATION_INFO = {
    'from_version': '1.3',
    'to_version': '1.4', 
    'description': 'Add espresso support with shots, shot sessions, and espresso equipment',
    'requires_backup': False,  # Safe migration that only adds files
    'migrate_function': migrate_v1_3_to_v1_4
}