"""
Tests for audit timestamp functionality.
"""
import pytest
from datetime import datetime
from coffeejournal import create_app


class TestAuditTimestamps:
    """Test class for verifying audit timestamps."""
    
    @pytest.fixture
    def app(self, tmp_path):
        """Create test app with temporary data directory."""
        test_config = {
            'TESTING': True,
            'DATA_DIR': str(tmp_path)
        }
        app = create_app(test_config=test_config)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_create_entity_adds_timestamps(self, client):
        """Test that creating entities automatically adds created_at and updated_at."""
        # Create a roaster
        roaster_data = {'name': 'Test Roaster'}
        response = client.post('/api/roasters', json=roaster_data)
        
        assert response.status_code == 201
        roaster = response.get_json()
        
        # Verify timestamps were added
        assert 'created_at' in roaster
        assert 'updated_at' in roaster
        assert roaster['created_at'] == roaster['updated_at']  # Should be same on creation
        
        # Verify timestamp format (ISO format)
        created_at = datetime.fromisoformat(roaster['created_at'].replace('Z', '+00:00'))
        assert isinstance(created_at, datetime)
    
    def test_update_entity_preserves_created_updates_modified(self, client):
        """Test that updating entities preserves created_at but updates updated_at."""
        # Create a roaster
        roaster_data = {'name': 'Test Roaster'}
        create_response = client.post('/api/roasters', json=roaster_data)
        assert create_response.status_code == 201
        roaster = create_response.get_json()
        
        original_created_at = roaster['created_at']
        original_updated_at = roaster['updated_at']
        
        # Wait a tiny bit to ensure different timestamp
        import time
        time.sleep(0.001)
        
        # Update the roaster
        update_data = {'name': 'Updated Roaster', 'description': 'A great roaster'}
        update_response = client.put(f'/api/roasters/{roaster["id"]}', json=update_data)
        assert update_response.status_code == 200
        updated_roaster = update_response.get_json()
        
        # Verify created_at is preserved, updated_at is newer
        assert updated_roaster['created_at'] == original_created_at
        assert updated_roaster['updated_at'] != original_updated_at
        assert updated_roaster['updated_at'] > original_updated_at
    
    def test_timestamps_work_for_all_entity_types(self, client):
        """Test that timestamps work for different entity types."""
        # Test with different entity types
        entities_to_test = [
            ('/api/roasters', {'name': 'Test Roaster'}),
            ('/api/bean_types', {'name': 'Test Bean Type'}),
            ('/api/countries', {'name': 'Test Country'}),
            ('/api/brew_methods', {'name': 'Test Brew Method'}),
            ('/api/grinders', {'name': 'Test Grinder'}),
            ('/api/filters', {'name': 'Test Filter'}),
            ('/api/kettles', {'name': 'Test Kettle'}),
            ('/api/scales', {'name': 'Test Scale'}),
        ]
        
        for endpoint, data in entities_to_test:
            response = client.post(endpoint, json=data)
            assert response.status_code == 201, f"Failed to create {endpoint} entity"
            
            entity = response.get_json()
            assert 'created_at' in entity, f"Missing created_at in {endpoint}"
            assert 'updated_at' in entity, f"Missing updated_at in {endpoint}"
    
    def test_complex_entity_timestamps(self, client):
        """Test timestamps with more complex entities like products and batches."""
        # Create dependencies first
        roaster_response = client.post('/api/roasters', json={'name': 'Test Roaster'})
        roaster = roaster_response.get_json()
        
        bean_type_response = client.post('/api/bean_types', json={'name': 'Arabica'})
        bean_type = bean_type_response.get_json()
        
        country_response = client.post('/api/countries', json={'name': 'Ethiopia'})
        country = country_response.get_json()
        
        # Create product
        product_data = {
            'name': 'Test Coffee',
            'roaster_id': roaster['id'],
            'bean_type_ids': [bean_type['id']],
            'country_id': country['id']
        }
        product_response = client.post('/api/products', json=product_data)
        assert product_response.status_code == 201
        product = product_response.get_json()
        
        assert 'created_at' in product
        assert 'updated_at' in product
        
        # Create batch
        batch_data = {
            'roast_date': '2024-01-01',
            'purchase_date': '2024-01-02',
            'amount_grams': 500
        }
        batch_response = client.post(f'/api/products/{product["id"]}/batches', json=batch_data)
        assert batch_response.status_code == 201
        batch = batch_response.get_json()
        
        assert 'created_at' in batch
        assert 'updated_at' in batch
        
        # Create brew session
        brew_data = {
            'amount_coffee_grams': 25.0,
            'amount_water_grams': 400.0,
            'brew_temperature_c': 93.5
        }
        brew_response = client.post(f'/api/batches/{batch["id"]}/brew_sessions', json=brew_data)
        assert brew_response.status_code == 201
        brew_session = brew_response.get_json()
        
        assert 'created_at' in brew_session
        assert 'updated_at' in brew_session