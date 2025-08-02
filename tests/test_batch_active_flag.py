"""
Tests for batch is_active flag functionality.
"""
import pytest
from coffeejournal import create_app


class TestBatchActiveFlag:
    """Test class for verifying batch is_active flag."""
    
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
    
    @pytest.fixture
    def setup_product(self, client):
        """Set up a test product for batch creation."""
        # Create dependencies
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
        return product_response.get_json()
    
    def test_create_batch_defaults_to_active(self, client, setup_product):
        """Test that creating a batch without is_active defaults to True."""
        product = setup_product
        
        batch_data = {
            'roast_date': '2024-01-01',
            'purchase_date': '2024-01-02',
            'amount_grams': 500
        }
        
        response = client.post(f'/api/products/{product["id"]}/batches', json=batch_data)
        assert response.status_code == 201
        
        batch = response.get_json()
        assert batch['is_active'] is True  # Should default to active
    
    def test_create_batch_with_explicit_active_flag(self, client, setup_product):
        """Test creating a batch with explicit is_active value."""
        product = setup_product
        
        # Test creating active batch
        active_batch_data = {
            'roast_date': '2024-01-01',
            'purchase_date': '2024-01-02',
            'amount_grams': 500,
            'is_active': True
        }
        
        response = client.post(f'/api/products/{product["id"]}/batches', json=active_batch_data)
        assert response.status_code == 201
        
        batch = response.get_json()
        assert batch['is_active'] is True
        
        # Test creating inactive batch
        inactive_batch_data = {
            'roast_date': '2024-02-01',
            'purchase_date': '2024-02-02',
            'amount_grams': 250,
            'is_active': False
        }
        
        response = client.post(f'/api/products/{product["id"]}/batches', json=inactive_batch_data)
        assert response.status_code == 201
        
        batch = response.get_json()
        assert batch['is_active'] is False
    
    def test_update_batch_active_flag(self, client, setup_product):
        """Test updating a batch's is_active flag."""
        product = setup_product
        
        # Create a batch
        batch_data = {
            'roast_date': '2024-01-01',
            'purchase_date': '2024-01-02',
            'amount_grams': 500
        }
        
        create_response = client.post(f'/api/products/{product["id"]}/batches', json=batch_data)
        assert create_response.status_code == 201
        batch = create_response.get_json()
        
        # Verify it's active by default
        assert batch['is_active'] is True
        
        # Update to inactive
        update_data = {'is_active': False}
        update_response = client.put(f'/api/batches/{batch["id"]}', json=update_data)
        assert update_response.status_code == 200
        
        updated_batch = update_response.get_json()
        assert updated_batch['is_active'] is False
        
        # Update back to active
        update_data = {'is_active': True}
        update_response = client.put(f'/api/batches/{batch["id"]}', json=update_data)
        assert update_response.status_code == 200
        
        updated_batch = update_response.get_json()
        assert updated_batch['is_active'] is True
    
    def test_update_batch_preserves_active_flag_when_not_specified(self, client, setup_product):
        """Test that updating other fields preserves the is_active flag."""
        product = setup_product
        
        # Create an inactive batch
        batch_data = {
            'roast_date': '2024-01-01',
            'purchase_date': '2024-01-02',
            'amount_grams': 500,
            'is_active': False
        }
        
        create_response = client.post(f'/api/products/{product["id"]}/batches', json=batch_data)
        assert create_response.status_code == 201
        batch = create_response.get_json()
        
        # Update other fields without specifying is_active
        update_data = {
            'notes': 'Updated notes',
            'rating': 5
        }
        update_response = client.put(f'/api/batches/{batch["id"]}', json=update_data)
        assert update_response.status_code == 200
        
        updated_batch = update_response.get_json()
        assert updated_batch['is_active'] is False  # Should preserve the False value
        assert updated_batch['notes'] == 'Updated notes'
        assert updated_batch['rating'] == 5
    
    def test_get_batches_includes_active_flag(self, client, setup_product):
        """Test that retrieving batches includes the is_active flag."""
        product = setup_product
        
        # Create active and inactive batches
        active_batch_data = {
            'roast_date': '2024-01-01',
            'purchase_date': '2024-01-02',
            'amount_grams': 500,
            'is_active': True
        }
        
        inactive_batch_data = {
            'roast_date': '2024-02-01',
            'purchase_date': '2024-02-02',
            'amount_grams': 250,
            'is_active': False
        }
        
        # Create both batches
        client.post(f'/api/products/{product["id"]}/batches', json=active_batch_data)
        client.post(f'/api/products/{product["id"]}/batches', json=inactive_batch_data)
        
        # Get all batches for the product
        response = client.get(f'/api/products/{product["id"]}/batches')
        assert response.status_code == 200
        
        batches = response.get_json()
        assert len(batches) == 2
        
        # Check that both batches have the is_active flag
        active_batches = [b for b in batches if b['is_active']]
        inactive_batches = [b for b in batches if not b['is_active']]
        
        assert len(active_batches) == 1
        assert len(inactive_batches) == 1
    
    def test_batch_timestamps_with_active_flag(self, client, setup_product):
        """Test that audit timestamps work correctly with is_active flag."""
        product = setup_product
        
        batch_data = {
            'roast_date': '2024-01-01',
            'purchase_date': '2024-01-02',
            'amount_grams': 500,
            'is_active': False
        }
        
        response = client.post(f'/api/products/{product["id"]}/batches', json=batch_data)
        assert response.status_code == 201
        
        batch = response.get_json()
        assert 'created_at' in batch
        assert 'updated_at' in batch
        assert batch['is_active'] is False