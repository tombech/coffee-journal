#!/usr/bin/env python3
"""
Script to repair corrupted shots.json file by stripping out nested/enriched data
and keeping only the ID references.
"""

import json
import os
import sys
from datetime import datetime

def clean_shot_record(shot):
    """Remove enriched/nested data from a shot record, keeping only IDs."""
    # Define the valid fields for a shot based on schema v1.4
    valid_fields = {
        'id', 'timestamp', 'product_batch_id', 'product_id', 'shot_session_id',
        'brewer_id', 'grinder_id', 'portafilter_id', 'basket_id', 'scale_id',
        'recipe_id', 'dose_grams', 'yield_grams', 'preinfusion_seconds',
        'extraction_time_seconds', 'brew_time_seconds', 'pressure_bars',
        'water_temperature_c', 'temperature_c', 'grinder_setting',
        'sweetness', 'acidity', 'bitterness', 'body', 'aroma', 'crema',
        'flavor_profile_match', 'extraction_status', 'notes', 'score',
        'created_at', 'updated_at', 'ratio'
    }
    
    # Create cleaned record with only valid fields
    cleaned = {}
    for field in valid_fields:
        if field in shot:
            cleaned[field] = shot[field]
    
    # Handle some field name variations we might see
    if 'extraction_time_seconds' in shot and 'brew_time_seconds' not in cleaned:
        cleaned['brew_time_seconds'] = shot['extraction_time_seconds']
    if 'water_temperature_c' in shot and 'temperature_c' not in cleaned:
        cleaned['temperature_c'] = shot['water_temperature_c']
    
    return cleaned

def repair_shots_file(input_file, output_file=None):
    """Repair a corrupted shots.json file."""
    if output_file is None:
        # Create backup and use same filename
        backup_file = input_file + f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        os.rename(input_file, backup_file)
        output_file = input_file
        print(f"Created backup: {backup_file}")
    
    # Read the corrupted file
    with open(input_file if output_file != input_file else backup_file, 'r') as f:
        shots = json.load(f)
    
    if not isinstance(shots, list):
        print("Error: shots.json should contain a list")
        return False
    
    print(f"Processing {len(shots)} shot records...")
    
    # Clean each shot
    cleaned_shots = []
    fields_removed = set()
    
    for i, shot in enumerate(shots):
        # Track what fields we're removing
        for field in shot:
            if field not in ['id', 'timestamp', 'product_batch_id', 'product_id', 
                           'shot_session_id', 'brewer_id', 'grinder_id', 
                           'portafilter_id', 'basket_id', 'scale_id', 'recipe_id',
                           'dose_grams', 'yield_grams', 'preinfusion_seconds',
                           'extraction_time_seconds', 'brew_time_seconds', 
                           'pressure_bars', 'water_temperature_c', 'temperature_c',
                           'grinder_setting', 'sweetness', 'acidity', 'bitterness',
                           'body', 'aroma', 'crema', 'flavor_profile_match',
                           'extraction_status', 'notes', 'score', 'created_at',
                           'updated_at', 'ratio']:
                fields_removed.add(field)
        
        cleaned = clean_shot_record(shot)
        cleaned_shots.append(cleaned)
    
    # Write the cleaned data
    with open(output_file, 'w') as f:
        json.dump(cleaned_shots, f, indent=2)
    
    print(f"Cleaned {len(cleaned_shots)} shot records")
    print(f"Removed enriched fields: {', '.join(sorted(fields_removed))}")
    print(f"Output written to: {output_file}")
    
    # Verify the cleaned file
    with open(output_file, 'r') as f:
        verified = json.load(f)
    
    # Check that no shot has nested objects
    has_nested = False
    for shot in verified:
        for key, value in shot.items():
            if isinstance(value, dict):
                print(f"Warning: Shot {shot.get('id', '?')} still has nested object in field '{key}'")
                has_nested = True
    
    if not has_nested:
        print("✅ Verification passed: No nested objects found")
    else:
        print("⚠️ Warning: Some nested objects may still exist")
    
    return not has_nested

def main():
    if len(sys.argv) < 2:
        print("Usage: python repair_shots.py <path_to_shots.json> [output_file]")
        print("Example: python repair_shots.py ./temp/shots.json")
        print("         python repair_shots.py ./temp/shots.json ./temp/shots_cleaned.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found")
        sys.exit(1)
    
    success = repair_shots_file(input_file, output_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()