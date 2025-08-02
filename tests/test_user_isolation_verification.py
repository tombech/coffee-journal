"""
Tests to verify proper user isolation - different users should not see each other's data.
"""

import pytest
import tempfile
from coffeejournal import create_app


class TestUserIsolationVerification:
    """Verify that users cannot see each other's data."""
    
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
    
    def test_bean_types_are_truly_isolated(self, client):
        """Verify bean types are isolated between users."""
        # User1 creates a bean type
        response = client.post('/api/bean_types?user_id=user1', json={
            'name': 'User1 Bean Type'
        })
        assert response.status_code == 201
        
        # User1 should see their bean type
        response = client.get('/api/bean_types?user_id=user1')
        assert response.status_code == 200
        user1_bean_types = response.get_json()
        assert len(user1_bean_types) == 1
        assert user1_bean_types[0]['name'] == 'User1 Bean Type'
        
        # User2 should NOT see User1's bean type (isolation test)
        response = client.get('/api/bean_types?user_id=user2')
        assert response.status_code == 200
        user2_bean_types = response.get_json()
        assert len(user2_bean_types) == 0  # This should pass if properly isolated
    
    def test_countries_are_truly_isolated(self, client):
        """Verify countries are isolated between users."""
        # User1 creates a country
        response = client.post('/api/countries?user_id=user1', json={
            'name': 'User1 Country'
        })
        assert response.status_code == 201
        
        # User1 should see their country
        response = client.get('/api/countries?user_id=user1')
        assert response.status_code == 200
        user1_countries = response.get_json()
        assert len(user1_countries) == 1
        assert user1_countries[0]['name'] == 'User1 Country'
        
        # User2 should NOT see User1's country (isolation test)
        response = client.get('/api/countries?user_id=user2')
        assert response.status_code == 200
        user2_countries = response.get_json()
        assert len(user2_countries) == 0  # This should pass if properly isolated
    
    def test_roasters_are_truly_isolated(self, client):
        """Verify roasters are isolated between users (this should pass since we fixed them)."""
        # User1 creates a roaster
        response = client.post('/api/roasters?user_id=user1', json={
            'name': 'User1 Roaster'
        })
        assert response.status_code == 201
        
        # User1 should see their roaster
        response = client.get('/api/roasters?user_id=user1')
        assert response.status_code == 200
        user1_roasters = response.get_json()
        assert len(user1_roasters) == 1
        assert user1_roasters[0]['name'] == 'User1 Roaster'
        
        # User2 should NOT see User1's roaster (isolation test)
        response = client.get('/api/roasters?user_id=user2')
        assert response.status_code == 200
        user2_roasters = response.get_json()
        assert len(user2_roasters) == 0  # This should pass since we fixed roasters