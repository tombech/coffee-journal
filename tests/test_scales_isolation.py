"""
Test scales isolation to verify the fix works.
"""

import pytest
import tempfile
from coffeejournal import create_app


class TestScalesIsolation:
    """Test scales isolation."""
    
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
    
    def test_scales_are_properly_isolated(self, client):
        """Verify scales are isolated between users."""
        
        # User1 creates a scale
        response = client.post('/api/scales?user_id=user1', json={
            'name': 'User1 Scale'
        })
        assert response.status_code == 201
        
        # User1 should see their scale
        response = client.get('/api/scales?user_id=user1')
        assert response.status_code == 200
        user1_scales = response.get_json()
        assert len(user1_scales) == 1
        assert user1_scales[0]['name'] == 'User1 Scale'
        
        # User2 should NOT see User1's scale (isolation test)
        response = client.get('/api/scales?user_id=user2')
        assert response.status_code == 200
        user2_scales = response.get_json()
        assert len(user2_scales) == 0  # Should be empty if properly isolated
        
        print("✅ Scales are properly isolated between users")