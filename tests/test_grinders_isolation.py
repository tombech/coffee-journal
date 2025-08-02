"""
Test grinders isolation to verify the fix works.
"""

import pytest
import tempfile
from coffeejournal import create_app


class TestGrindersIsolation:
    """Test grinders isolation."""
    
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
    
    def test_grinders_are_properly_isolated(self, client):
        """Verify grinders are isolated between users."""
        
        # User1 creates a grinder
        response = client.post('/api/grinders?user_id=user1', json={
            'name': 'User1 Grinder'
        })
        assert response.status_code == 201
        
        # User1 should see their grinder
        response = client.get('/api/grinders?user_id=user1')
        assert response.status_code == 200
        user1_grinders = response.get_json()
        assert len(user1_grinders) == 1
        assert user1_grinders[0]['name'] == 'User1 Grinder'
        
        # User2 should NOT see User1's grinder (isolation test)
        response = client.get('/api/grinders?user_id=user2')
        assert response.status_code == 200
        user2_grinders = response.get_json()
        assert len(user2_grinders) == 0  # Should be empty if properly isolated
        
        print("✅ Grinders are properly isolated between users")