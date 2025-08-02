"""
Test decaf_methods isolation to verify the fix works.
"""

import pytest
import tempfile
from coffeejournal import create_app


class TestDecafMethodsIsolation:
    """Test decaf_methods isolation."""
    
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
    
    def test_decaf_methods_are_properly_isolated(self, client):
        """Verify decaf_methods are isolated between users."""
        
        # User1 creates a decaf method
        response = client.post('/api/decaf_methods?user_id=user1', json={
            'name': 'User1 Decaf Method'
        })
        assert response.status_code == 201
        
        # User1 should see their decaf method
        response = client.get('/api/decaf_methods?user_id=user1')
        assert response.status_code == 200
        user1_decaf_methods = response.get_json()
        assert len(user1_decaf_methods) == 1
        assert user1_decaf_methods[0]['name'] == 'User1 Decaf Method'
        
        # User2 should NOT see User1's decaf method (isolation test)
        response = client.get('/api/decaf_methods?user_id=user2')
        assert response.status_code == 200
        user2_decaf_methods = response.get_json()
        assert len(user2_decaf_methods) == 0  # Should be empty if properly isolated
        
        print("✅ Decaf methods are properly isolated between users")