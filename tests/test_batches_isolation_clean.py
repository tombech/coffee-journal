"""
Clean test for batches isolation.
"""

import pytest
import tempfile
from coffeejournal import create_app


class TestBatchesIsolationClean:
    """Test batches isolation with clean setup."""
    
    @pytest.fixture
    def app(self):
        """Create app with test configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            app = create_app({
                'TESTING': True,
                'DATA_DIR': temp_dir
            })
            with app.app_context():
                yield app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_batches_are_properly_isolated(self, client):
        """Verify batches are isolated between users."""
        
        # Create required lookup data for user1
        roaster_response = client.post('/api/roasters?user_id=user1', json={'name': 'Test Roaster'})
        assert roaster_response.status_code == 201
        roaster_id = roaster_response.get_json()['id']
        
        bean_type_response = client.post('/api/bean_types?user_id=user1', json={'name': 'Test Bean Type'})
        assert bean_type_response.status_code == 201
        bean_type_id = bean_type_response.get_json()['id']
        
        country_response = client.post('/api/countries?user_id=user1', json={'name': 'Test Country'})
        assert country_response.status_code == 201
        country_id = country_response.get_json()['id']
        
        region_response = client.post('/api/regions?user_id=user1', json={'name': 'Test Region', 'country_id': country_id})
        assert region_response.status_code == 201
        region_id = region_response.get_json()['id']
        
        # Create a product for user1
        product_response = client.post('/api/products?user_id=user1', json={
            'product_name': 'User1 Coffee',
            'roaster_id': roaster_id,
            'bean_type_id': [bean_type_id],
            'country_id': country_id,
            'region_id': [region_id]
        })
        assert product_response.status_code == 201
        product_data = product_response.get_json()
        product_id = product_data['id']
        
        # User1 creates a batch
        batch_response = client.post(f'/api/products/{product_id}/batches?user_id=user1', json={
            'roast_date': '2025-01-01',
            'amount_grams': 350
        })
        assert batch_response.status_code == 201
        batch_data = batch_response.get_json()
        batch_id = batch_data['id']
        
        # User1 should see their batch
        response = client.get(f'/api/products/{product_id}/batches?user_id=user1')
        assert response.status_code == 200
        user1_batches = response.get_json()
        assert len(user1_batches) == 1
        assert user1_batches[0]['product_id'] == product_id
        
        # User2 should NOT see User1's batch (product should not be accessible)
        response = client.get(f'/api/products/{product_id}/batches?user_id=user2')
        assert response.status_code == 404  # Product not found for user2
        
        # User2 should NOT be able to access the individual batch either
        response = client.get(f'/api/batches/{batch_id}?user_id=user2')
        assert response.status_code == 404  # Batch not found for user2
        
        print("✅ Batches are properly isolated between users")