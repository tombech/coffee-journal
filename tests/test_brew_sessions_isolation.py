"""
Test brew sessions isolation to verify the fix works.
"""

import pytest
import tempfile
from coffeejournal import create_app


class TestBrewSessionsIsolation:
    """Test brew sessions isolation."""
    
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
    
    def test_brew_sessions_are_properly_isolated(self, client):
        """Verify brew sessions are isolated between users."""
        
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
        
        # Create a batch for user1
        batch_response = client.post(f'/api/products/{product_id}/batches?user_id=user1', json={
            'roast_date': '2025-01-01',
            'amount_grams': 350
        })
        assert batch_response.status_code == 201
        batch_data = batch_response.get_json()
        batch_id = batch_data['id']
        
        # Create a brew session for user1
        session_response = client.post(f'/api/batches/{batch_id}/brew_sessions?user_id=user1', json={
            'amount_coffee_grams': 20,
            'amount_water_grams': 300,
            'brew_temperature_c': 94,
            'score': 8.5
        })
        assert session_response.status_code == 201
        session_data = session_response.get_json()
        session_id = session_data['id']
        
        # User1 should see their brew session in global list
        response = client.get('/api/brew_sessions?user_id=user1')
        assert response.status_code == 200
        result = response.get_json()
        user1_sessions = result['data']  # Handle pagination response
        assert len(user1_sessions) == 1
        assert user1_sessions[0]['id'] == session_id
        
        # User2 should NOT see User1's brew session (isolation test)
        response = client.get('/api/brew_sessions?user_id=user2')
        assert response.status_code == 200
        result = response.get_json()
        user2_sessions = result['data']  # Handle pagination response
        assert len(user2_sessions) == 0  # Should be empty if properly isolated
        
        # User2 should NOT be able to access the individual brew session
        response = client.get(f'/api/brew_sessions/{session_id}?user_id=user2')
        assert response.status_code == 404  # Session not found for user2
        
        print("✅ Brew sessions are properly isolated between users")