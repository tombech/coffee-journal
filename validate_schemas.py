#!/usr/bin/env python3
"""
Validate all repository data files against their schemas and detect drift.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add src to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import schemas directly without loading the full app
import importlib.util
spec = importlib.util.spec_from_file_location(
    "schemas", 
    os.path.join(os.path.dirname(__file__), "src/coffeejournal/repositories/schemas.py")
)
schemas_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schemas_module)

SCHEMAS = schemas_module.SCHEMAS
get_schema_for_entity = schemas_module.get_schema_for_entity

from jsonschema import validate, ValidationError, Draft7Validator


def load_json_file(filepath: Path) -> List[Dict[str, Any]]:
    """Load JSON data from file."""
    if not filepath.exists():
        return []
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Handle both list and dict formats
    if isinstance(data, dict):
        return [data]
    return data


def validate_file(filepath: Path, verbose: bool = False) -> Dict[str, Any]:
    """Validate a single data file against its schema."""
    filename = filepath.name
    entity_name = filename[:-5] if filename.endswith('.json') else filename
    
    result = {
        'file': str(filepath),
        'entity': entity_name,
        'records': 0,
        'errors': [],
        'warnings': [],
        'unknown_fields': set(),
        'missing_fields': set()
    }
    
    # Get schema
    schema = get_schema_for_entity(entity_name)
    if not schema:
        result['warnings'].append(f"No schema defined for entity '{entity_name}'")
        return result
    
    # Load data
    try:
        data = load_json_file(filepath)
        result['records'] = len(data)
    except Exception as e:
        result['errors'].append(f"Failed to load file: {e}")
        return result
    
    # Get expected fields from schema
    expected_fields = set(schema.get('properties', {}).keys())
    required_fields = set(schema.get('required', []))
    
    # Validate each record
    validator = Draft7Validator(schema)
    
    for i, record in enumerate(data):
        # Check for validation errors
        errors = list(validator.iter_errors(record))
        for error in errors:
            result['errors'].append(f"Record {i} (ID: {record.get('id', '?')}): {error.message}")
        
        # Check for unknown fields (potential enriched data)
        record_fields = set(record.keys())
        unknown = record_fields - expected_fields
        if unknown:
            result['unknown_fields'].update(unknown)
            if verbose:
                result['warnings'].append(f"Record {i} has unknown fields: {unknown}")
        
        # Check for missing required fields
        missing = required_fields - record_fields
        if missing:
            result['missing_fields'].update(missing)
            if verbose:
                result['warnings'].append(f"Record {i} missing required fields: {missing}")
    
    return result


def check_schema_drift(data_dir: str, verbose: bool = False) -> Dict[str, Any]:
    """Check all data files for schema drift."""
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"Error: Data directory {data_dir} does not exist")
        return {}
    
    results = {}
    total_errors = 0
    total_warnings = 0
    
    # Check each JSON file
    for filepath in sorted(data_path.glob('*.json')):
        # Skip version files
        if filepath.name in ['data_version.json', 'schema_version.json']:
            continue
        
        result = validate_file(filepath, verbose)
        results[filepath.name] = result
        
        total_errors += len(result['errors'])
        total_warnings += len(result['warnings'])
    
    # Summary
    print("\n" + "=" * 70)
    print("SCHEMA VALIDATION REPORT")
    print("=" * 70)
    print(f"Data directory: {data_dir}")
    print(f"Files checked: {len(results)}")
    print(f"Total errors: {total_errors}")
    print(f"Total warnings: {total_warnings}")
    print()
    
    # Detailed results
    for filename, result in results.items():
        if result['errors'] or result['unknown_fields'] or (verbose and result['warnings']):
            print(f"\n📁 {filename}")
            print(f"   Records: {result['records']}")
            
            if result['errors']:
                print(f"   ❌ Errors: {len(result['errors'])}")
                for error in result['errors'][:5]:  # Show first 5 errors
                    print(f"      - {error}")
                if len(result['errors']) > 5:
                    print(f"      ... and {len(result['errors']) - 5} more")
            
            if result['unknown_fields']:
                print(f"   ⚠️  Unknown fields (possible enriched data): {result['unknown_fields']}")
            
            if result['missing_fields']:
                print(f"   ⚠️  Missing required fields: {result['missing_fields']}")
            
            if verbose and result['warnings']:
                print(f"   ⚠️  Warnings: {len(result['warnings'])}")
                for warning in result['warnings'][:3]:
                    print(f"      - {warning}")
    
    # Check for schema drift
    drift_detected = False
    for filename, result in results.items():
        if result['unknown_fields']:
            drift_detected = True
            break
    
    if drift_detected:
        print("\n" + "=" * 70)
        print("⚠️  SCHEMA DRIFT DETECTED")
        print("=" * 70)
        print("Some data files contain fields not defined in the schema.")
        print("This could indicate:")
        print("1. Enriched data being accidentally saved (like in shots.json)")
        print("2. New fields added without updating the schema")
        print("3. Schema version mismatch")
        print("\nRecommended actions:")
        print("1. Run repair scripts for corrupted files")
        print("2. Update schema_version.json if new fields are intentional")
        print("3. Clean data files to match schema")
    else:
        print("\n✅ No schema drift detected - all files match their schemas")
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate repository data against schemas')
    parser.add_argument('data_dir', nargs='?', default='./test_data',
                       help='Path to data directory (default: ./test_data)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed warnings')
    parser.add_argument('--fix', action='store_true',
                       help='Attempt to fix issues by removing unknown fields')
    
    args = parser.parse_args()
    
    results = check_schema_drift(args.data_dir, args.verbose)
    
    if args.fix:
        print("\n" + "=" * 70)
        print("ATTEMPTING FIXES")
        print("=" * 70)
        
        for filename, result in results.items():
            if result['unknown_fields']:
                filepath = Path(args.data_dir) / filename
                print(f"\nFixing {filename}...")
                
                # Load data
                data = load_json_file(filepath)
                
                # Get schema
                entity_name = filename[:-5] if filename.endswith('.json') else filename
                schema = get_schema_for_entity(entity_name)
                if not schema:
                    print(f"  ⚠️  No schema found, skipping")
                    continue
                
                # Clean each record
                expected_fields = set(schema.get('properties', {}).keys())
                cleaned_data = []
                for record in data:
                    cleaned_record = {k: v for k, v in record.items() if k in expected_fields}
                    cleaned_data.append(cleaned_record)
                
                # Backup and save
                backup_path = filepath.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                filepath.rename(backup_path)
                print(f"  Created backup: {backup_path}")
                
                with open(filepath, 'w') as f:
                    json.dump(cleaned_data, f, indent=2)
                print(f"  ✅ Removed fields: {result['unknown_fields']}")
    
    # Exit with error code if validation errors found
    sys.exit(1 if any(r['errors'] for r in results.values()) else 0)


if __name__ == "__main__":
    main()