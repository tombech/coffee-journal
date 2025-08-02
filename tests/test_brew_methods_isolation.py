"""
Test brew_methods isolation to verify the fix works.
"""

import pytest
import tempfile
from coffeejournal import create_app


class TestBrewMethodsIsolation:
    """Test brew_methods isolation."""
    
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
    
    def test_brew_methods_are_properly_isolated(self, client):
        """Verify brew_methods are isolated between users."""
        
        # User1 creates a brew method
        response = client.post('/api/brew_methods?user_id=user1', json={
            'name': 'User1 Brew Method'
        })
        assert response.status_code == 201
        
        # User1 should see their brew method
        response = client.get('/api/brew_methods?user_id=user1')
        assert response.status_code == 200
        user1_brew_methods = response.get_json()
        assert len(user1_brew_methods) == 1
        assert user1_brew_methods[0]['name'] == 'User1 Brew Method'
        
        # User2 should NOT see User1's brew method (isolation test)
        response = client.get('/api/brew_methods?user_id=user2')
        assert response.status_code == 200
        user2_brew_methods = response.get_json()
        assert len(user2_brew_methods) == 0  # Should be empty if properly isolated
        
        print("✅ Brew methods are properly isolated between users")