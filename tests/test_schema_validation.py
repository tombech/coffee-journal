"""
Unit tests for schema validation system.

Tests the JSON schema validation system that was implemented to catch
data corruption issues like the one discovered on 2025-08-16 where
enriched lookup data was accidentally being saved to storage files.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, mock_open

from src.coffeejournal.repositories.schemas import (
    get_schema_for_entity,
    validate_entity_data,
    SchemaValidationError,
    SCHEMAS
)
from src.coffeejournal.repositories.json_repository import JSONRepositoryBase


class TestSchemaDefinitions:
    """Test that schema definitions are properly structured."""
    
    def test_all_schemas_have_required_structure(self):
        """All schemas should have proper JSON Schema structure."""
        required_schema_keys = {'type', 'properties', 'required', 'additionalProperties'}
        
        for entity_type, schema in SCHEMAS.items():
            assert 'type' in schema, f"Schema for {entity_type} missing 'type'"
            assert schema['type'] == 'object', f"Schema for {entity_type} should be object type"
            assert 'properties' in schema, f"Schema for {entity_type} missing 'properties'"
            assert 'required' in schema, f"Schema for {entity_type} missing 'required'"
            assert 'additionalProperties' in schema, f"Schema for {entity_type} missing 'additionalProperties'"
            
    def test_get_schema_for_entity_valid(self):
        """get_schema_for_entity should return valid schemas for known entities."""
        # Test known entity types
        valid_entities = ['shots', 'shot_sessions', 'products', 'batches', 'brew_sessions']
        
        for entity_type in valid_entities:
            schema = get_schema_for_entity(entity_type)
            assert schema is not None, f"No schema found for {entity_type}"
            assert 'properties' in schema
            assert 'required' in schema
            
    def test_get_schema_for_entity_invalid(self):
        """get_schema_for_entity should handle unknown entity types gracefully."""
        schema = get_schema_for_entity('unknown_entity')
        assert schema is None
        

class TestCleanDataValidation:
    """Test that clean, properly structured data passes validation."""
    
    def test_clean_shot_data_passes_validation(self):
        """Clean shot data with only ID references should pass validation."""
        clean_shot = {
            "id": 1,
            "product_batch_id": 23,
            "product_id": 21,
            "brewer_id": 1,
            "grinder_id": 1,
            "portafilter_id": 2,
            "basket_id": 2,
            "scale_id": 1,
            "dose_grams": 18.0,
            "yield_grams": 39.0,
            "preinfusion_seconds": 8,
            "extraction_time_seconds": 29,
            "pressure_bars": 9.0,
            "water_temperature_c": 93.0,
            "grinder_setting": "6",
            "sweetness": 5,
            "acidity": 7,
            "bitterness": 3,
            "body": 5,
            "aroma": 4,
            "crema": 4,
            "flavor_profile_match": 4,
            "extraction_status": "under-extracted",
            "notes": "Test shot notes",
            "timestamp": "2025-08-13T16:38:02.285Z",
            "created_at": "2025-08-13T16:40:08.622079+00:00",
            "updated_at": "2025-08-13T16:40:08.622079+00:00",
            "ratio": "1:2.17"
        }
        
        # Should not raise any exception
        validate_entity_data('shots', clean_shot)
        
    def test_clean_shot_session_data_passes_validation(self):
        """Clean shot session data should pass validation."""
        clean_session = {
            "id": 1,
            "title": "Test Dial In Session",
            "product_id": 18,
            "product_batch_id": 19,
            "brewer_id": 1,
            "notes": "Testing dial-in process",
            "created_at": "2025-08-13T05:29:53.613134+00:00",
            "updated_at": "2025-08-13T21:37:50.772407+00:00"
        }
        
        # Should not raise any exception
        validate_entity_data('shot_sessions', clean_session)
        
    def test_clean_product_data_passes_validation(self):
        """Clean product data should pass validation."""
        clean_product = {
            "id": 1,
            "roaster_id": 1,
            "bean_type_id": [1],
            "country_id": 1,
            "region_id": [],
            "product_name": "Test Coffee",
            "roast_type": 5,
            "description": "Test description",
            "url": "https://example.com",
            "image_url": "https://example.com/image.jpg",
            "decaf": False,
            "decaf_method_id": None,
            "rating": 4.0,
            "bean_process": ["Washed (wet)"],
            "notes": "",
            "created_at": "2025-07-13T17:48:09.552777+00:00",
            "updated_at": "2025-07-13T17:48:09.552777+00:00"
        }
        
        # Should not raise any exception
        validate_entity_data('products', clean_product)


class TestCorruptedDataDetection:
    """Test that the schema validation catches corrupted data like the bug discovered today."""
    
    def test_shot_with_enriched_product_data_fails_validation(self):
        """Shot with enriched product object should fail validation."""
        corrupted_shot = {
            "id": 1,
            "product_batch_id": 23,
            "product_id": 21,
            # This is the corruption bug - enriched product object instead of just ID
            "product": {
                "id": 21,
                "product_name": "Husets Espresso",
                "roaster": {
                    "id": 1,
                    "name": "Kaffebrenneriet"
                },
                "country": {
                    "id": 1,
                    "name": "Brazil"
                }
            },
            "brewer_id": 1,
            # Another corruption example - enriched brewer object
            "brewer": {
                "id": 1,
                "name": "Gaggia Classic Pro",
                "brand": "Gaggia"
            },
            "dose_grams": 18.0,
            "yield_grams": 39.0,
            "timestamp": "2025-08-13T16:38:02.285Z"
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_entity_data('shots', corrupted_shot)
            
        error_message = str(exc_info.value)
        assert "Additional properties are not allowed" in error_message
        # Check that enriched fields are mentioned as unexpected
        assert "'product'" in error_message and "were unexpected" in error_message
        assert "'brewer'" in error_message
        
    def test_shot_session_with_enriched_data_fails_validation(self):
        """Shot session with enriched data should fail validation."""
        corrupted_session = {
            "id": 1,
            "title": "Test Session",
            "product_id": 18,
            # Corruption: enriched product object
            "product": {
                "id": 18,
                "product_name": "Koffeinfri Espresso",
                "roaster_id": 1
            },
            # Corruption: enriched shots array
            "shots": [
                {"id": 1, "dose_grams": 18},
                {"id": 2, "dose_grams": 17.9}
            ],
            # Corruption: calculated shot count
            "shot_count": 2,
            "brewer_id": 1,
            "notes": "Test notes"
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_entity_data('shot_sessions', corrupted_session)
            
        error_message = str(exc_info.value)
        assert "Additional properties are not allowed" in error_message
        # Check that enriched fields are mentioned as unexpected
        assert "'product'" in error_message and "were unexpected" in error_message
        assert "'shots'" in error_message
        assert "'shot_count'" in error_message
        
    def test_product_with_enriched_lookup_data_fails_validation(self):
        """Product with enriched lookup objects should fail validation."""
        corrupted_product = {
            "id": 1,
            "roaster_id": 1,
            # Corruption: enriched roaster object instead of just ID
            "roaster": {
                "id": 1,
                "name": "Kaffebrenneriet",
                "url": "https://www.kaffebrenneriet.no/"
            },
            "bean_type_id": [1],
            # Corruption: enriched bean type objects
            "bean_type": [
                {"id": 1, "name": "Arabica"}
            ],
            "country_id": 1,
            # Corruption: enriched country object
            "country": {
                "id": 1,
                "name": "Brazil"
            },
            "product_name": "Test Coffee"
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_entity_data('products', corrupted_product)
            
        error_message = str(exc_info.value)
        assert "Additional properties are not allowed" in error_message
        # Check that enriched fields are mentioned as unexpected
        assert "'roaster'" in error_message and "were unexpected" in error_message
        assert "'bean_type'" in error_message
        assert "'country'" in error_message


class TestSchemaDriftDetection:
    """Test schema drift detection functionality."""
    
    def test_detect_unknown_fields_in_data(self):
        """Should detect when data contains fields not in schema."""
        shot_with_new_field = {
            "id": 1,
            "product_id": 21,
            "brewer_id": 1,
            "dose_grams": 18.0,
            "yield_grams": 36.0,  # Required field
            # New field not in schema
            "new_experimental_field": "some_value",
            "timestamp": "2025-08-13T16:38:02.285Z"
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_entity_data('shots', shot_with_new_field)
            
        error_message = str(exc_info.value)
        assert "'new_experimental_field'" in error_message 
        assert ("were unexpected" in error_message or "was unexpected" in error_message)
        
    def test_detect_missing_required_fields(self):
        """Should detect when required fields are missing."""
        incomplete_shot = {
            "id": 1,
            "product_id": 21,
            # Missing required fields like brewer_id, dose_grams, etc.
            "timestamp": "2025-08-13T16:38:02.285Z"
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_entity_data('shots', incomplete_shot)
            
        error_message = str(exc_info.value)
        # Should mention missing required fields
        assert "is a required property" in error_message


class TestRepositoryIntegration:
    """Test schema validation integration with repository implementation."""
    
    def test_repository_validates_on_create(self):
        """Repository should validate data when creating entities."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a shots repository for testing
            repo = JSONRepositoryBase(temp_dir, 'shots.json')
            
            # Valid shot data should work
            valid_shot = {
                "dose_grams": 18.0,
                "yield_grams": 36.0,
                "product_id": 1,
                "timestamp": "2025-08-16T10:00:00Z"
            }
            
            # Should not raise exception
            created_shot = repo.create(valid_shot)
            assert created_shot['id'] == 1
            assert created_shot['dose_grams'] == 18.0
            
    def test_repository_validation_prevents_corrupted_create(self):
        """Repository should prevent creating entities with enriched data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = JSONRepositoryBase(temp_dir, 'shots.json')
            
            # Corrupted shot with enriched product object
            corrupted_shot = {
                "dose_grams": 18.0,
                "yield_grams": 36.0,
                "product_id": 1,
                # This enriched data should be stripped out automatically
                "product": {
                    "id": 1,
                    "product_name": "Test Coffee"
                },
                "brewer": {
                    "id": 1,
                    "name": "Test Brewer"
                }
            }
            
            # The repository should strip enriched fields before validation
            created_shot = repo.create(corrupted_shot)
            
            # Verify enriched fields were stripped
            assert 'product' not in created_shot
            assert 'brewer' not in created_shot
            assert created_shot['dose_grams'] == 18.0
            assert created_shot['product_id'] == 1
            
    def test_repository_strips_enriched_fields(self):
        """Repository should automatically strip enriched fields before saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = JSONRepositoryBase(temp_dir, 'shots.json')
            
            # Test the _strip_enriched_fields method directly
            corrupted_data = {
                "id": 1,
                "dose_grams": 18.0,
                "yield_grams": 36.0,
                "product_id": 1,
                # Enriched fields that should be removed
                "product": {"id": 1, "name": "Test"},
                "product_name": "Test Coffee",
                "brewer_name": "Test Brewer",
                "calculated_score": 4.5
            }
            
            cleaned = repo._strip_enriched_fields(corrupted_data)
            
            # Should only contain schema fields
            expected_fields = {'id', 'dose_grams', 'yield_grams', 'product_id'}
            actual_fields = set(cleaned.keys())
            
            # Check that enriched fields were removed
            assert 'product' not in cleaned
            assert 'product_name' not in cleaned
            assert 'brewer_name' not in cleaned
            assert 'calculated_score' not in cleaned
            
            # Check that valid fields remain
            assert cleaned['dose_grams'] == 18.0
            assert cleaned['product_id'] == 1


class TestRealWorldCorruptionScenarios:
    """Test real-world corruption scenarios based on the production bug."""
    
    def test_massive_shots_corruption_scenario(self):
        """Test the exact corruption pattern found in production shots.json."""
        # This is a simplified version of what was found in the 2.4MB corrupted file
        massive_corrupted_shot = {
            "id": 1,
            "product_batch_id": 23,
            "product_id": 21,
            "brewer_id": 1,
            "dose_grams": 18.0,
            "yield_grams": 39.0,
            # All these fields were enriched data that got saved accidentally
            "product": {
                "id": 21,
                "product_name": "Husets Espresso",
                "roaster": {
                    "id": 1,
                    "name": "Kaffebrenneriet",
                    "url": "https://www.kaffebrenneriet.no/",
                    "image_url": "https://www.kaffebrenneriet.no/Files/Images/logo%20(1).png"
                },
                "bean_type": [{"id": 1, "name": "Arabica"}],
                "country": {"id": 1, "name": "Brazil"},
                "region": [],
                "decaf_method": None
            },
            "brewer": {
                "id": 1,
                "name": "Gaggia Classic Pro",
                "brand": "Gaggia",
                "model": "Classic Pro"
            },
            "grinder": {
                "id": 3,
                "name": "J-Ultra",
                "brand": "Eureka",
                "grinder_type": "Flat Burr"
            },
            "basket": {
                "id": 2,
                "name": "IMS Precision 18g",
                "basket_type": "Precision",
                "hole_count": 798
            },
            "scale": {
                "id": 1,
                "name": "Hario Polaris",
                "brand": "Hario"
            },
            # Even more enriched data
            "product_name": "Husets Espresso",
            "brewer_name": "Gaggia Classic Pro",
            "grinder_name": "J-Ultra",
            "basket_name": "IMS Precision 18g",
            "scale_name": "Hario Polaris",
            "coffee_age": "242 weeks",
            "calculated_score": 4.5,
            "dose_yield_ratio": "1:2.17"
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_entity_data('shots', massive_corrupted_shot)
            
        error_message = str(exc_info.value)
        
        # Should catch all the enriched objects  
        enriched_objects = ['product', 'brewer', 'grinder', 'basket', 'scale']
        for obj in enriched_objects:
            assert f"'{obj}'" in error_message
        assert "were unexpected" in error_message
            
        # Should catch all the enriched name fields
        enriched_names = ['product_name', 'brewer_name', 'grinder_name', 'basket_name', 'scale_name']
        for name_field in enriched_names:
            assert f"'{name_field}'" in error_message
            
        # Should catch calculated fields
        calculated_fields = ['coffee_age', 'calculated_score', 'dose_yield_ratio']
        for calc_field in calculated_fields:
            assert f"'{calc_field}'" in error_message
            
    def test_brew_sessions_corruption_scenario(self):
        """Test brew sessions corruption pattern found in production."""
        corrupted_brew_session = {
            "id": 2,
            "product_batch_id": 1,
            "product_id": 1,
            "brew_method_id": 1,
            # Enriched data that should not be saved
            "brew_method": {
                "id": 1,
                "name": "V60",
                "description": "Pour over method"
            },
            "product_details": {
                "roast_date": "2024-12-15",
                "amount_grams": 250
            },
            "product_name": "Yirgacheffe Single Origin",
            "coffee_age": "35 weeks",
            "calculated_score": 4.2,
            # Regular fields that should be allowed
            "amount_coffee_grams": 20.0,
            "amount_water_grams": 320.0,
            "brew_temperature_c": 93.0,
            "timestamp": "2025-01-15T10:30:00Z"
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_entity_data('brew_sessions', corrupted_brew_session)
            
        error_message = str(exc_info.value)
        
        # Should catch enriched objects and calculated fields
        problematic_fields = ['brew_method', 'product_details', 'product_name', 'coffee_age', 'calculated_score']
        for field in problematic_fields:
            assert f"'{field}'" in error_message
        assert "were unexpected" in error_message


if __name__ == '__main__':
    pytest.main([__file__, '-v'])