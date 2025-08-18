"""
Migration from schema version 1.4 to 1.5 - Schema Validation Updates
"""

import os
import json
from datetime import datetime


def migrate_v1_4_to_v1_5(data_dir):
    """
    Migrate from schema version 1.4 to 1.5.
    
    This migration updates schema validation rules:
    - Taste note properties (sweetness, acidity, etc.): integers 1-10  
    - Overall score field (brew_sessions.score, shots.score): float 1.0-10.0
    - Product/batch rating field: float 0.0-5.0 in 0.5 intervals
    - Added missing shot equipment fields: tamper_id, wdt_tool_id, leveling_tool_id, overall_score
    
    No data migration needed - only schema validation updates.
    
    Args:
        data_dir (str): Path to the data directory
    """
    print("🔄 Migrating from schema v1.4 to v1.5 (Schema Validation Updates)")
    
    changes_made = 0
    
    # Update data version file
    version_file = os.path.join(data_dir, 'data_version.json')
    try:
        version_data = {
            'version': '1.5',
            'migrated_at': datetime.utcnow().isoformat(),
            'migration_notes': 'Updated schema validation rules for scores and added missing shot equipment fields'
        }
        
        with open(version_file, 'w') as f:
            json.dump(version_data, f, indent=2)
        print(f"  ✅ Updated data_version.json to v1.5")
        changes_made += 1
    except Exception as e:
        print(f"  ❌ Failed to update version file: {e}")
        raise
    
    if changes_made > 0:
        print(f"✅ Migration v1.4→v1.5 completed successfully ({changes_made} changes)")
    else:
        print("ℹ️  Migration v1.4→v1.5 completed (no changes needed)")
    
    return True


# Migration metadata
MIGRATION_INFO = {
    'from_version': '1.4',
    'to_version': '1.5', 
    'description': 'Update schema validation rules for scores and add missing shot equipment fields',
    'requires_backup': False,  # Safe migration that only updates validation rules
    'migrate_function': migrate_v1_4_to_v1_5
}