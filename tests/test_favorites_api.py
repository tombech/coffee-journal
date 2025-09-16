"""
Test the favorites statistics API endpoint.
"""

import pytest
import json
import uuid
import tempfile
from unittest.mock import patch
from datetime import datetime
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

    def test_favorites_endpoint_basic_functionality(self, client, test_user_id):
        """Test basic functionality of the favorites endpoint."""
        # Clean up any existing data
        client.delete(f'/api/test/cleanup/{test_user_id}')

        # Create test data - roaster
        roaster_data = {
            'name': 'Test Roaster',
            'description': 'A test roaster'
        }
        roaster_response = client.post(f'/api/roasters?user_id={test_user_id}',
                                     json=roaster_data)
        assert roaster_response.status_code == 201
        roaster = roaster_response.get_json()

        # Create test data - bean type
        bean_type_data = {
            'name': 'Arabica',
            'description': 'Test bean type'
        }
        bean_type_response = client.post(f'/api/bean_types?user_id={test_user_id}',
                                       json=bean_type_data)
        assert bean_type_response.status_code == 201
        bean_type = bean_type_response.get_json()

        # Create test data - country
        country_data = {
            'name': 'Ethiopia',
            'description': 'Test country'
        }
        country_response = client.post(f'/api/countries?user_id={test_user_id}',
                                     json=country_data)
        assert country_response.status_code == 201
        country = country_response.get_json()

        # Create test data - brew method
        brew_method_data = {
            'name': 'V60',
            'description': 'Pour over method'
        }
        brew_method_response = client.post(f'/api/brew_methods?user_id={test_user_id}',
                                         json=brew_method_data)
        assert brew_method_response.status_code == 201
        brew_method = brew_method_response.get_json()

        # Create test product
        product_data = {
            'product_name': 'Test Coffee',
            'roaster_id': roaster['id'],
            'bean_type_id': [bean_type['id']],
            'country_id': country['id'],
            'bean_process': ['Washed (wet)']
        }
        product_response = client.post(f'/api/products?user_id={test_user_id}',
                                     json=product_data)
        assert product_response.status_code == 201
        product = product_response.get_json()

        # Create multiple high-scoring brew sessions (need 3+ for minimum usage)
        for i in range(4):
            session_data = {
                'product_id': product['id'],
                'brew_method_id': brew_method['id'],
                'score': 8.5 + (i * 0.1),  # High scores
                'timestamp': f'2024-01-{10+i:02d}T10:00:00Z'
            }
            session_response = client.post(f'/api/brew_sessions?user_id={test_user_id}',
                                         json=session_data)
            assert session_response.status_code == 201

        # Test the favorites endpoint
        response = client.get(f'/api/stats/favorites?user_id={test_user_id}')
        assert response.status_code == 200

        favorites = response.get_json()
        assert isinstance(favorites, dict)

        # Check that we have favorites for the items we created
        expected_types = ['roaster', 'bean_type', 'country', 'brew_method', 'bean_process']

        for fav_type in expected_types:
            if fav_type in favorites and favorites[fav_type]:
                items = favorites[fav_type]
                assert len(items) >= 1

                # Check structure of each item
                for item in items:
                    assert 'type' in item
                    assert 'item' in item
                    assert 'avg_score' in item
                    assert 'total_sessions' in item
                    assert 'total_shots' in item
                    assert 'total_uses' in item
                    assert 'score_count' in item

                    assert item['type'] == fav_type
                    assert item['avg_score'] > 0
                    assert item['total_uses'] >= 3  # Minimum usage requirement

    def test_favorites_endpoint_minimum_usage_filter(self, client, test_user_id):
        """Test that favorites endpoint filters by minimum usage."""
        # Clean up any existing data
        client.delete(f'/api/test/cleanup/{test_user_id}')

        # Create test data
        roaster_data = {'name': 'Low Usage Roaster'}
        roaster_response = client.post(f'/api/roasters?user_id={test_user_id}',
                                     json=roaster_data)
        assert roaster_response.status_code == 201
        roaster = roaster_response.get_json()

        product_data = {
            'product_name': 'Low Usage Coffee',
            'roaster_id': roaster['id']
        }
        product_response = client.post(f'/api/products?user_id={test_user_id}',
                                     json=product_data)
        assert product_response.status_code == 201
        product = product_response.get_json()

        # Create only 2 sessions (below minimum of 3)
        for i in range(2):
            session_data = {
                'product_id': product['id'],
                'score': 9.0,
                'timestamp': f'2024-01-{10+i:02d}T10:00:00Z'
            }
            session_response = client.post(f'/api/brew_sessions?user_id={test_user_id}',
                                         json=session_data)
            assert session_response.status_code == 201

        # Test the favorites endpoint
        response = client.get(f'/api/stats/favorites?user_id={test_user_id}')
        assert response.status_code == 200

        favorites = response.get_json()

        # Should not include roaster with only 2 uses
        if 'roaster' in favorites:
            assert len(favorites['roaster']) == 0

    def test_favorites_endpoint_with_shots(self, client, test_user_id):
        """Test favorites endpoint includes shot data."""
        # Clean up any existing data
        client.delete(f'/api/test/cleanup/{test_user_id}')

        # Create test data
        roaster_data = {'name': 'Shot Roaster'}
        roaster_response = client.post(f'/api/roasters?user_id={test_user_id}',
                                     json=roaster_data)
        assert roaster_response.status_code == 201
        roaster = roaster_response.get_json()

        product_data = {
            'product_name': 'Shot Coffee',
            'roaster_id': roaster['id']
        }
        product_response = client.post(f'/api/products?user_id={test_user_id}',
                                     json=product_data)
        assert product_response.status_code == 201
        product = product_response.get_json()

        # Create shots with high scores
        for i in range(4):
            shot_data = {
                'product_id': product['id'],
                'dose_grams': 18.0,
                'yield_grams': 36.0,
                'overall_score': 8.5 + (i * 0.1),
                'timestamp': f'2024-01-{10+i:02d}T10:00:00Z'
            }
            shot_response = client.post(f'/api/shots?user_id={test_user_id}',
                                      json=shot_data)
            assert shot_response.status_code == 201

        # Test the favorites endpoint
        response = client.get(f'/api/stats/favorites?user_id={test_user_id}')
        assert response.status_code == 200

        favorites = response.get_json()

        # Should include roaster with shot data
        assert 'roaster' in favorites
        assert len(favorites['roaster']) >= 1

        roaster_item = favorites['roaster'][0]
        assert roaster_item['total_shots'] >= 4
        assert roaster_item['total_uses'] >= 4

    def test_favorites_endpoint_score_sorting(self, client, test_user_id):
        """Test that favorites are sorted by average score within each category."""
        # Clean up any existing data
        client.delete(f'/api/test/cleanup/{test_user_id}')

        # Create two roasters
        roaster1_data = {'name': 'Lower Score Roaster'}
        roaster1_response = client.post(f'/api/roasters?user_id={test_user_id}',
                                      json=roaster1_data)
        assert roaster1_response.status_code == 201
        roaster1 = roaster1_response.get_json()

        roaster2_data = {'name': 'Higher Score Roaster'}
        roaster2_response = client.post(f'/api/roasters?user_id={test_user_id}',
                                      json=roaster2_data)
        assert roaster2_response.status_code == 201
        roaster2 = roaster2_response.get_json()

        # Create products for each roaster
        product1_data = {
            'product_name': 'Lower Coffee',
            'roaster_id': roaster1['id']
        }
        product1_response = client.post(f'/api/products?user_id={test_user_id}',
                                      json=product1_data)
        assert product1_response.status_code == 201
        product1 = product1_response.get_json()

        product2_data = {
            'product_name': 'Higher Coffee',
            'roaster_id': roaster2['id']
        }
        product2_response = client.post(f'/api/products?user_id={test_user_id}',
                                      json=product2_data)
        assert product2_response.status_code == 201
        product2 = product2_response.get_json()

        # Create sessions with different average scores
        # Lower scoring sessions for roaster1
        for i in range(4):
            session_data = {
                'product_id': product1['id'],
                'score': 6.0 + (i * 0.1),  # Average: ~6.15
                'timestamp': f'2024-01-{10+i:02d}T10:00:00Z'
            }
            client.post(f'/api/brew_sessions?user_id={test_user_id}', json=session_data)

        # Higher scoring sessions for roaster2
        for i in range(4):
            session_data = {
                'product_id': product2['id'],
                'score': 8.0 + (i * 0.1),  # Average: ~8.15
                'timestamp': f'2024-01-{15+i:02d}T10:00:00Z'
            }
            client.post(f'/api/brew_sessions?user_id={test_user_id}', json=session_data)

        # Test the favorites endpoint
        response = client.get(f'/api/stats/favorites?user_id={test_user_id}')
        assert response.status_code == 200

        favorites = response.get_json()

        # Check roaster sorting
        assert 'roaster' in favorites
        assert len(favorites['roaster']) == 2

        # Higher scoring roaster should be first
        assert favorites['roaster'][0]['item']['name'] == 'Higher Score Roaster'
        assert favorites['roaster'][1]['item']['name'] == 'Lower Score Roaster'
        assert favorites['roaster'][0]['avg_score'] > favorites['roaster'][1]['avg_score']

    def test_favorites_endpoint_empty_data(self, client, test_user_id):
        """Test favorites endpoint with no data."""
        # Clean up any existing data
        client.delete(f'/api/test/cleanup/{test_user_id}')

        # Test the favorites endpoint with no data
        response = client.get(f'/api/stats/favorites?user_id={test_user_id}')
        assert response.status_code == 200

        favorites = response.get_json()
        assert isinstance(favorites, dict)

        # All categories should be empty or missing
        for category_items in favorites.values():
            assert len(category_items) == 0

    def test_favorites_endpoint_bean_process_grouping(self, client, test_user_id):
        """Test that bean processes are properly grouped and calculated."""
        # Clean up any existing data
        client.delete(f'/api/test/cleanup/{test_user_id}')

        # Create products with different bean processes
        product1_data = {
            'product_name': 'Washed Coffee',
            'bean_process': ['Washed (wet)']
        }
        product1_response = client.post(f'/api/products?user_id={test_user_id}',
                                      json=product1_data)
        assert product1_response.status_code == 201
        product1 = product1_response.get_json()

        product2_data = {
            'product_name': 'Natural Coffee',
            'bean_process': ['Natural (dry)']
        }
        product2_response = client.post(f'/api/products?user_id={test_user_id}',
                                      json=product2_data)
        assert product2_response.status_code == 201
        product2 = product2_response.get_json()

        # Create multiple sessions for each product (need 3+ for minimum)
        for i in range(4):
            # High scores for washed
            session_data = {
                'product_id': product1['id'],
                'score': 8.5,
                'timestamp': f'2024-01-{10+i:02d}T10:00:00Z'
            }
            client.post(f'/api/brew_sessions?user_id={test_user_id}', json=session_data)

            # Lower scores for natural
            session_data = {
                'product_id': product2['id'],
                'score': 7.0,
                'timestamp': f'2024-01-{15+i:02d}T10:00:00Z'
            }
            client.post(f'/api/brew_sessions?user_id={test_user_id}', json=session_data)

        # Test the favorites endpoint
        response = client.get(f'/api/stats/favorites?user_id={test_user_id}')
        assert response.status_code == 200

        favorites = response.get_json()

        # Check bean process favorites
        assert 'bean_process' in favorites
        assert len(favorites['bean_process']) == 2

        # Should be sorted by score (washed first)
        assert favorites['bean_process'][0]['item']['name'] == 'Washed (wet)'
        assert favorites['bean_process'][1]['item']['name'] == 'Natural (dry)'
        assert favorites['bean_process'][0]['avg_score'] > favorites['bean_process'][1]['avg_score']