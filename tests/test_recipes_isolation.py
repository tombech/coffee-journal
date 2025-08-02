"""
Test recipes isolation to verify the fix works.
"""

import pytest
import tempfile
from coffeejournal import create_app


class TestRecipesIsolation:
    """Test recipes isolation."""
    
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
    
    def test_recipes_are_properly_isolated(self, client):
        """Verify recipes are isolated between users."""
        
        # User1 creates a recipe
        response = client.post('/api/recipes?user_id=user1', json={
            'name': 'User1 Recipe'
        })
        assert response.status_code == 201
        
        # User1 should see their recipe
        response = client.get('/api/recipes?user_id=user1')
        assert response.status_code == 200
        user1_recipes = response.get_json()
        assert len(user1_recipes) == 1
        assert user1_recipes[0]['name'] == 'User1 Recipe'
        
        # User2 should NOT see User1's recipe (isolation test)
        response = client.get('/api/recipes?user_id=user2')
        assert response.status_code == 200
        user2_recipes = response.get_json()
        assert len(user2_recipes) == 0  # Should be empty if properly isolated
        
        print("✅ Recipes are properly isolated between users")