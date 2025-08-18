#!/usr/bin/env python3
"""
Comprehensive repair script for all corrupted production data files.
Removes enriched data corruption from multiple entity files.
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import schemas directly without loading the full app
import importlib.util
spec = importlib.util.spec_from_file_location(
    "schemas", 
    os.path.join(os.path.dirname(__file__), "src/coffeejournal/repositories/schemas.py")
)
schemas_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schemas_module)

get_schema_for_entity = schemas_module.get_schema_for_entity


def load_json_file(filepath: Path):
    """Load JSON data from file."""
    if not filepath.exists():
        return []
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(data, dict):
        return [data]
    return data


def clean_entity_data(data, entity_name):
    """Clean enriched data from entity records based on schema."""
    schema = get_schema_for_entity(entity_name)
    if not schema or 'properties' not in schema:
        print(f"  Warning: No schema found for {entity_name}, skipping cleaning")
        return data
    
    allowed_fields = set(schema['properties'].keys())
    cleaned_data = []
    
    for record in data:
        cleaned_record = {}
        enriched_fields_removed = []
        
        for key, value in record.items():
            if key in allowed_fields:
                cleaned_record[key] = value
            else:
                enriched_fields_removed.append(key)
        
        if enriched_fields_removed:
            print(f"    Record {record.get('id', '?')}: Removed {enriched_fields_removed}")
        
        cleaned_data.append(cleaned_record)
    
    return cleaned_data


def repair_data_file(filepath: Path, dry_run=False):
    """Repair a single corrupted data file."""
    filename = filepath.name
    entity_name = filename[:-5] if filename.endswith('.json') else filename
    
    print(f"\n📁 Processing {filename}...")
    
    # Skip non-entity files
    skip_files = ['data_version.json', 'schema_version.json', 'shots_repaired.json']
    if filename in skip_files:
        print(f"  Skipping {filename}")
        return {'skipped': True}
    
    # Load original data
    try:
        original_data = load_json_file(filepath)
        original_count = len(original_data)
        print(f"  Loaded {original_count} records")
    except Exception as e:
        print(f"  ❌ Error loading file: {e}")
        return {'error': f"Failed to load: {e}"}
    
    if not original_data:
        print(f"  Empty file, skipping")
        return {'skipped': True}
    
    # Clean the data
    try:
        cleaned_data = clean_entity_data(original_data, entity_name)
        cleaned_count = len(cleaned_data)
        print(f"  Cleaned to {cleaned_count} records")
    except Exception as e:
        print(f"  ❌ Error cleaning data: {e}")
        return {'error': f"Failed to clean: {e}"}
    
    # Check if any changes were made
    original_json = json.dumps(original_data, sort_keys=True)
    cleaned_json = json.dumps(cleaned_data, sort_keys=True)
    
    if original_json == cleaned_json:
        print(f"  ✅ No changes needed")
        return {'no_changes': True}
    
    if dry_run:
        print(f"  🔍 [DRY RUN] Would clean and save changes")
        return {'would_change': True}
    
    # Create backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = filepath.with_suffix(f'.backup_{timestamp}.json')
    shutil.copy2(filepath, backup_path)
    print(f"  💾 Created backup: {backup_path.name}")
    
    # Save cleaned data
    try:
        with open(filepath, 'w') as f:
            json.dump(cleaned_data, f, indent=2)
        print(f"  ✅ Saved cleaned data")
        return {'repaired': True, 'backup': backup_path.name}
    except Exception as e:
        print(f"  ❌ Error saving cleaned data: {e}")
        # Restore backup
        shutil.copy2(backup_path, filepath)
        print(f"  🔄 Restored from backup")
        return {'error': f"Failed to save: {e}"}


def repair_all_files(data_dir, dry_run=False):
    """Repair all corrupted files in a directory."""
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"❌ Error: Data directory {data_dir} does not exist")
        return
    
    print(f"🔧 COMPREHENSIVE DATA REPAIR {'(DRY RUN)' if dry_run else ''}")
    print(f"📁 Directory: {data_dir}")
    print("=" * 70)
    
    # Find all JSON files
    json_files = sorted([f for f in data_path.glob('*.json') 
                        if f.name not in ['data_version.json', 'schema_version.json']])
    
    print(f"Found {len(json_files)} data files to process")
    
    results = {}
    
    # Process each file
    for filepath in json_files:
        result = repair_data_file(filepath, dry_run)
        results[filepath.name] = result
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 REPAIR SUMMARY")
    print("=" * 70)
    
    categories = {
        'repaired': '✅ Repaired',
        'no_changes': '✅ Already clean',
        'skipped': '⏩ Skipped',
        'would_change': '🔍 Would repair (dry run)',
        'error': '❌ Error'
    }
    
    for category, label in categories.items():
        files = [filename for filename, result in results.items() if category in result]
        if files:
            print(f"\n{label}: {len(files)} files")
            for filename in files:
                if category == 'repaired':
                    backup = results[filename].get('backup', '')
                    print(f"  • {filename} (backup: {backup})")
                elif category == 'error':
                    error = results[filename].get('error', '')
                    print(f"  • {filename}: {error}")
                else:
                    print(f"  • {filename}")
    
    total_repaired = len([r for r in results.values() if 'repaired' in r])
    total_errors = len([r for r in results.values() if 'error' in r])
    
    if not dry_run:
        print(f"\n🎉 Repair complete: {total_repaired} files repaired, {total_errors} errors")
        if total_errors == 0:
            print("✅ All files processed successfully!")
        else:
            print("⚠️  Some files had errors - check logs above")
    else:
        would_change = len([r for r in results.values() if 'would_change' in r])
        print(f"\n🔍 Dry run complete: {would_change} files would be repaired")
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Repair all corrupted production data files')
    parser.add_argument('data_dir', nargs='?', default='./temp',
                       help='Path to data directory (default: ./temp)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--file', type=str,
                       help='Repair only specific file (filename only)')
    
    args = parser.parse_args()
    
    if args.file:
        # Repair single file
        filepath = Path(args.data_dir) / args.file
        if not filepath.exists():
            print(f"❌ Error: File {filepath} does not exist")
            sys.exit(1)
        
        print(f"🔧 SINGLE FILE REPAIR {'(DRY RUN)' if args.dry_run else ''}")
        print("=" * 50)
        result = repair_data_file(filepath, args.dry_run)
        
        if 'error' in result:
            print(f"\n❌ Failed to repair {args.file}")
            sys.exit(1)
        elif 'repaired' in result:
            print(f"\n✅ Successfully repaired {args.file}")
        else:
            print(f"\n✅ {args.file} processed")
    else:
        # Repair all files
        results = repair_all_files(args.data_dir, args.dry_run)
        
        # Exit with error if any files failed
        if any('error' in result for result in results.values()):
            sys.exit(1)


if __name__ == "__main__":
    main()