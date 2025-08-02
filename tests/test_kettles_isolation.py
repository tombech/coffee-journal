"""
Test kettles isolation to verify the fix works.
"""

import pytest
import tempfile
from coffeejournal import create_app


class TestKettlesIsolation:
    """Test kettles isolation."""
    
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
    
    def test_kettles_are_properly_isolated(self, client):
        """Verify kettles are isolated between users."""
        
        # User1 creates a kettle
        response = client.post('/api/kettles?user_id=user1', json={
            'name': 'User1 Kettle'
        })
        assert response.status_code == 201
        
        # User1 should see their kettle
        response = client.get('/api/kettles?user_id=user1')
        assert response.status_code == 200
        user1_kettles = response.get_json()
        assert len(user1_kettles) == 1
        assert user1_kettles[0]['name'] == 'User1 Kettle'
        
        # User2 should NOT see User1's kettle (isolation test)
        response = client.get('/api/kettles?user_id=user2')
        assert response.status_code == 200
        user2_kettles = response.get_json()
        assert len(user2_kettles) == 0  # Should be empty if properly isolated
        
        print("✅ Kettles are properly isolated between users")