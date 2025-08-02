"""
Debug test to isolate the exact issue.
"""

import pytest
import tempfile
from coffeejournal import create_app


class TestDebugIsolation:
    """Debug isolation issue."""
    
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
    
    def test_debug_product_isolation(self, client):
        """Debug exactly what's happening with product isolation."""
        
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
        print(f"Created product with ID: {product_id}")
        
        # Test 1: Direct product access by user2 (this worked in previous test)
        response = client.get(f'/api/products/{product_id}?user_id=user2')
        print(f"Direct product access by user2 - Status: {response.status_code}, Data: {response.get_json()}")
        
        # Test 2: Product batches access by user2 (this is failing)
        response = client.get(f'/api/products/{product_id}/batches?user_id=user2')
        print(f"Product batches access by user2 - Status: {response.status_code}, Data: {response.get_json()}")
        
        # Test 3: Check if product exists in user1's context
        response = client.get(f'/api/products/{product_id}?user_id=user1')
        print(f"Direct product access by user1 - Status: {response.status_code}, Data: {response.get_json()}")
        
        # Test 4: Check if batches endpoint works for user1
        response = client.get(f'/api/products/{product_id}/batches?user_id=user1')
        print(f"Product batches access by user1 - Status: {response.status_code}, Data: {response.get_json()}")
        
        print("Debug complete")