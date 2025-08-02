"""
Test filters isolation to verify the fix works.
"""

import pytest
import tempfile
from coffeejournal import create_app


class TestFiltersIsolation:
    """Test filters isolation."""
    
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
    
    def test_filters_are_properly_isolated(self, client):
        """Verify filters are isolated between users."""
        
        # User1 creates a filter
        response = client.post('/api/filters?user_id=user1', json={
            'name': 'User1 Filter'
        })
        assert response.status_code == 201
        
        # User1 should see their filter
        response = client.get('/api/filters?user_id=user1')
        assert response.status_code == 200
        user1_filters = response.get_json()
        assert len(user1_filters) == 1
        assert user1_filters[0]['name'] == 'User1 Filter'
        
        # User2 should NOT see User1's filter (isolation test)
        response = client.get('/api/filters?user_id=user2')
        assert response.status_code == 200
        user2_filters = response.get_json()
        assert len(user2_filters) == 0  # Should be empty if properly isolated
        
        print("✅ Filters are properly isolated between users")