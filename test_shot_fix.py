#!/usr/bin/env python3
"""
Test that the shot storage fix prevents enriched data from being saved.
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from coffeejournal.repositories.factory import get_repository_factory, init_repository_factory


def test_shot_storage_fix():
    """Test that enriched shot data is not saved to the repository."""
    
    # Create a temporary test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Testing in temporary directory: {temp_dir}")
        
        # Initialize repository factory with test directory
        init_repository_factory(storage_type='json', data_dir=temp_dir)
        factory = get_repository_factory()
        
        # Get shot repository
        shot_repo = factory.get_shot_repository()
        
        # Create a shot with both valid fields and enriched fields (simulating what the API might send)
        shot_data = {
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'product_id': 1,
            'brewer_id': 1,
            'grinder_id': 1,
            'basket_id': 1,
            'portafilter_id': 1,
            'extraction_time_seconds': 28,
            'pressure_bars': 9,
            'water_temperature_c': 93,
            'grinder_setting': '15',
            'sweetness': 7,
            'acidity': 6,
            'body': 5,
            'crema': 4,
            'notes': 'Test shot',
            # These enriched fields should NOT be saved
            'product': {'id': 1, 'product_name': 'Test Product', 'roaster': {'id': 1, 'name': 'Test Roaster'}},
            'brewer': {'id': 1, 'name': 'Test Brewer'},
            'grinder': {'id': 1, 'name': 'Test Grinder'},
            'basket': {'id': 1, 'name': 'Test Basket'},
            'portafilter': {'id': 1, 'name': 'Test Portafilter'},
            'product_name': 'Test Product',
            'brewer_name': 'Test Brewer',
            'grinder_name': 'Test Grinder',
            'basket_name': 'Test Basket',
            'portafilter_name': 'Test Portafilter',
            'calculated_score': 5.5,
            'coffee_age': '2 weeks',
            'dose_yield_ratio': 2.0
        }
        
        print("\n1. Creating shot with enriched data...")
        created_shot = shot_repo.create(shot_data)
        print(f"   Created shot ID: {created_shot['id']}")
        
        # Read the raw JSON file to verify enriched data was not saved
        shots_file = Path(temp_dir) / 'shots.json'
        with open(shots_file, 'r') as f:
            saved_shots = json.load(f)
        
        assert len(saved_shots) == 1, "Should have exactly one shot"
        saved_shot = saved_shots[0]
        
        print("\n2. Verifying saved data...")
        
        # Check that enriched fields were NOT saved
        enriched_fields = ['product', 'brewer', 'grinder', 'basket', 'portafilter',
                          'product_name', 'brewer_name', 'grinder_name', 'basket_name',
                          'portafilter_name', 'calculated_score', 'coffee_age', 'dose_yield_ratio']
        
        for field in enriched_fields:
            assert field not in saved_shot, f"Enriched field '{field}' should not be saved!"
        
        print("   ✅ No enriched fields found in saved data")
        
        # Check that valid fields WERE saved
        valid_fields = ['dose_grams', 'yield_grams', 'product_id', 'brewer_id', 
                       'grinder_id', 'basket_id', 'portafilter_id']
        
        for field in valid_fields:
            assert field in saved_shot, f"Valid field '{field}' should be saved!"
            assert saved_shot[field] == shot_data[field], f"Field '{field}' value mismatch"
        
        print("   ✅ All valid fields preserved correctly")
        
        # Test update with enriched data
        print("\n3. Testing update with enriched data...")
        
        update_data = {
            'dose_grams': 19.0,
            'notes': 'Updated test shot',
            # These should be stripped
            'product': {'id': 1, 'product_name': 'Updated Product'},
            'calculated_score': 6.0
        }
        
        updated_shot = shot_repo.update(created_shot['id'], update_data)
        
        # Read raw JSON again
        with open(shots_file, 'r') as f:
            saved_shots = json.load(f)
        
        saved_shot = saved_shots[0]
        
        # Verify update worked but enriched fields weren't saved
        assert saved_shot['dose_grams'] == 19.0, "Dose should be updated"
        assert saved_shot['notes'] == 'Updated test shot', "Notes should be updated"
        assert 'product' not in saved_shot, "Product object should not be saved"
        assert 'calculated_score' not in saved_shot, "Calculated score should not be saved"
        
        print("   ✅ Update preserved valid fields, stripped enriched fields")
        
        print("\n✅ All tests passed! The fix prevents enriched data from being saved.")
        return True


if __name__ == "__main__":
    try:
        success = test_shot_storage_fix()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)