"""
Simple test to verify product isolation.
"""

import pytest
import tempfile
from coffeejournal import create_app


class TestProductsIsolationSimple:
    """Test products isolation."""
    
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
    
    def test_products_are_properly_isolated(self, client):
        """Verify products are isolated between users."""
        
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
        
        # User1 should be able to access their product
        response = client.get(f'/api/products/{product_id}?user_id=user1')
        assert response.status_code == 200
        product = response.get_json()
        assert product['product_name'] == 'User1 Coffee'
        
        # User2 should NOT be able to access user1's product
        response = client.get(f'/api/products/{product_id}?user_id=user2')
        print(f"User2 accessing user1's product - Status: {response.status_code}, Data: {response.get_json()}")
        assert response.status_code == 404  # Product should not be found for user2
        
        print("✅ Products are properly isolated between users")