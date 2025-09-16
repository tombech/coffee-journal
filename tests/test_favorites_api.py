"""
Test the favorites statistics API endpoint - simplified version.
"""

import pytest
import json
import uuid
import tempfile
from coffeejournal import create_app


class TestFavoritesAPI:
    """Test the /stats/favorites endpoint."""

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

    @pytest.fixture
    def test_user_id(self):
        """Generate a unique test user ID."""
        return f'test_user_{uuid.uuid4().hex[:8]}'

    def test_favorites_endpoint_returns_valid_response(self, client, test_user_id):
        """Test that the favorites endpoint returns a valid response structure."""
        # Test the favorites endpoint with empty data
        response = client.get(f'/api/stats/favorites?user_id={test_user_id}')
        assert response.status_code == 200

        favorites = response.get_json()
        assert isinstance(favorites, dict)

        # Should contain expected category keys (even if empty)
        expected_categories = ['roaster', 'bean_type', 'country', 'region', 'brew_method', 'recipe', 'bean_process']

        # At least some categories should be present (they could be empty lists)
        for category in favorites.keys():
            assert category in expected_categories
            assert isinstance(favorites[category], list)

    def test_home_summary_endpoint_returns_valid_response(self, client, test_user_id):
        """Test that the home summary endpoint returns a valid response structure."""
        response = client.get(f'/api/stats/home-summary?user_id={test_user_id}')
        assert response.status_code == 200

        summary = response.get_json()
        assert isinstance(summary, dict)

        # Check required fields
        required_fields = [
            'products_with_active_batches',
            'products_without_active_batches',
            'total_products',
            'total_brew_sessions',
            'total_shots',
            'total_brewing_events',
            'total_grams_used',
            'total_grams_inventory',
            'total_grams_remaining',
            'average_coffee_per_session',
            'estimated_sessions_remaining'
        ]

        for field in required_fields:
            assert field in summary
            assert isinstance(summary[field], (int, float))

    def test_favorites_endpoint_with_minimal_data(self, client, test_user_id):
        """Test favorites endpoint behavior with minimal valid data."""
        # Clean up any existing data
        client.delete(f'/api/test/cleanup/{test_user_id}')

        # Create minimal test data - just a roaster
        roaster_data = {'name': 'Test Roaster'}
        roaster_response = client.post(f'/api/roasters?user_id={test_user_id}',
                                     json=roaster_data)
        assert roaster_response.status_code == 201

        # Test the favorites endpoint
        response = client.get(f'/api/stats/favorites?user_id={test_user_id}')
        assert response.status_code == 200

        favorites = response.get_json()
        assert isinstance(favorites, dict)

        # With no sessions, favorites should be empty or have empty lists
        for category_items in favorites.values():
            assert isinstance(category_items, list)
            # Items should be empty since no brewing sessions exist
            assert len(category_items) == 0