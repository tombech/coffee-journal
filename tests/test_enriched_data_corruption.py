"""Test to ensure enriched data is never written to disk."""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch
from coffeejournal.repositories.json_repository import JSONRepositoryBase


class TestEnrichedDataCorruption:
    """Test that enriched/nested data is stripped before writing to disk."""
    
    def test_update_strips_enriched_fields_before_saving(self):
        """Test that update method strips enriched fields before saving to disk."""
        # Create a temporary directory for test data
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, 'test_data.json')
            
            # Initial data with just IDs (clean)
            initial_data = [{
                'id': 1,
                'product_id': 1,
                'brew_method_id': 1,
                'score': 4.5,
                'created_at': '2025-01-01T00:00:00Z',
                'updated_at': '2025-01-01T00:00:00Z'
            }]
            
            # Write initial clean data
            with open(test_file, 'w') as f:
                json.dump(initial_data, f)
            
            # Create repository instance (pass the file path, not directory)
            repo = JSONRepositoryBase('test_data', temp_dir)
            repo.filepath = Path(test_file)  # Override the filepath to point to our test file
            
            # Mock the schema to define allowed fields
            def mock_get_schema():
                return {
                    'properties': {
                        'id': {'type': 'integer'},
                        'product_id': {'type': 'integer'},
                        'brew_method_id': {'type': 'integer'},
                        'score': {'type': 'number'},
                        'created_at': {'type': 'string'},
                        'updated_at': {'type': 'string'}
                    }
                }
            
            repo._get_schema = mock_get_schema
            
            # Update with enriched data (simulating what happens in the API)
            enriched_update = {
                'score': 4.8,
                'product_details': {  # This should NOT be saved
                    'roaster': {
                        'id': 1,
                        'name': 'Test Roaster',
                        'url': 'http://example.com'
                    },
                    'bean_type': ['Arabica'],
                    'country': {'id': 1, 'name': 'Ethiopia'}
                },
                'brew_method': {  # This should NOT be saved
                    'id': 1,
                    'name': 'V60',
                    'description': 'Pour over method'
                },
                'calculated_score': 4.7  # This should NOT be saved
            }
            
            # Perform the update
            repo.update(1, enriched_update)
            
            # Read the file directly to check what was actually written
            with open(test_file, 'r') as f:
                saved_data = json.load(f)
            
            # Assertions
            assert len(saved_data) == 1
            saved_item = saved_data[0]
            
            # Check that clean fields were updated
            assert saved_item['score'] == 4.8
            assert saved_item['id'] == 1
            assert saved_item['product_id'] == 1
            assert saved_item['brew_method_id'] == 1
            
            # Check that enriched fields were NOT saved
            assert 'product_details' not in saved_item, "Enriched 'product_details' should not be saved to disk"
            assert 'brew_method' not in saved_item, "Enriched 'brew_method' should not be saved to disk"
            assert 'calculated_score' not in saved_item, "Calculated field should not be saved to disk"
            
            # Check that only allowed fields are present
            allowed_fields = {'id', 'product_id', 'brew_method_id', 'score', 'created_at', 'updated_at'}
            actual_fields = set(saved_item.keys())
            unexpected_fields = actual_fields - allowed_fields
            assert not unexpected_fields, f"Unexpected fields found in saved data: {unexpected_fields}"
    
    def test_existing_enriched_data_gets_stripped_on_update(self):
        """Test that if data already has enriched fields, they get stripped on update."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, 'test_data.json')
            
            # Start with corrupted data that already has enriched fields
            corrupted_data = [{
                'id': 1,
                'product_id': 1,
                'brew_method_id': 1,
                'score': 4.5,
                'created_at': '2025-01-01T00:00:00Z',
                'updated_at': '2025-01-01T00:00:00Z',
                'product_details': {  # This corruption exists in the file
                    'roaster': {'id': 1, 'name': 'Old Roaster'}
                },
                'brew_method': {  # This corruption exists in the file
                    'id': 1,
                    'name': 'V60'
                }
            }]
            
            # Write corrupted data
            with open(test_file, 'w') as f:
                json.dump(corrupted_data, f)
            
            # Create repository instance (pass the file path, not directory)
            repo = JSONRepositoryBase('test_data', temp_dir)
            repo.filepath = Path(test_file)  # Override the filepath to point to our test file
            
            # Mock the schema
            def mock_get_schema():
                return {
                    'properties': {
                        'id': {'type': 'integer'},
                        'product_id': {'type': 'integer'},
                        'brew_method_id': {'type': 'integer'},
                        'score': {'type': 'number'},
                        'created_at': {'type': 'string'},
                        'updated_at': {'type': 'string'}
                    }
                }
            
            repo._get_schema = mock_get_schema
            
            # Simple update
            repo.update(1, {'score': 4.9})
            
            # Read the file directly
            with open(test_file, 'r') as f:
                saved_data = json.load(f)
            
            saved_item = saved_data[0]
            
            # The enriched fields should be gone after update
            assert 'product_details' not in saved_item, "Existing enriched data should be stripped on update"
            assert 'brew_method' not in saved_item, "Existing enriched data should be stripped on update"
            assert saved_item['score'] == 4.9
            
            # Check that only allowed fields remain
            allowed_fields = {'id', 'product_id', 'brew_method_id', 'score', 'created_at', 'updated_at'}
            actual_fields = set(saved_item.keys())
            unexpected_fields = actual_fields - allowed_fields
            assert not unexpected_fields, f"Unexpected fields found after update: {unexpected_fields}"