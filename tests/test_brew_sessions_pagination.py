"""
Tests for brew sessions pagination API functionality.

This module tests the REST API pagination implementation for the /api/brew_sessions endpoint,
including parameter validation, response format, sorting, and edge cases.
"""

import pytest
from datetime import datetime, timezone
from src.coffeejournal import create_app
from src.coffeejournal.repositories.factory import init_repository_factory


class TestBrewSessionsPagination:
    """Test pagination functionality for brew sessions API."""

    @pytest.fixture
    def app(self):
        """Create test app with isolated data."""
        app = create_app({
            'TESTING': True,
            'SECRET_KEY': 'test-secret-key',
            'DATA_DIR': 'test_data'
        })
        
        with app.app_context():
            init_repository_factory(storage_type='json', data_dir='test_data')
            yield app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @pytest.fixture
    def sample_data(self, client):
        """Create sample data for pagination testing."""
        # Create a product first
        product_response = client.post('/api/products', json={
            'product_name': 'Test Coffee',
            'roaster': 'Test Roaster',
            'bean_type': ['Arabica']
        })
        product_id = product_response.get_json()['id']
        
        # Create a batch
        batch_response = client.post('/api/products/' + str(product_id) + '/batches', json={
            'roast_date': '2024-01-01',
            'amount_grams': 500,
            'price': 25.00
        })
        batch_id = batch_response.get_json()['id']
        
        # Create multiple brew sessions with different timestamps
        session_ids = []
        base_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        
        for i in range(8):  # Create 8 sessions for pagination testing
            timestamp = base_time.replace(hour=10 + i)  # Different hours
            session_response = client.post(f'/api/batches/{batch_id}/brew_sessions', json={
                'timestamp': timestamp.isoformat(),
                'amount_coffee_grams': 15 + i,
                'amount_water_grams': 250 + (i * 10),
                'brew_method': f'Method {i}',
                'notes': f'Session {i}'
            })
            session_ids.append(session_response.get_json()['id'])
        
        return {
            'product_id': product_id,
            'batch_id': batch_id,
            'session_ids': session_ids
        }

    def test_pagination_response_format(self, client, sample_data):
        """Test that pagination response follows REST API standards."""
        response = client.get('/api/brew_sessions?page=1&page_size=3')
        assert response.status_code == 200
        
        result = response.get_json()
        
        # Verify top-level structure
        assert 'data' in result
        assert 'pagination' in result
        assert isinstance(result['data'], list)
        assert isinstance(result['pagination'], dict)
        
        # Verify pagination metadata structure
        pagination = result['pagination']
        required_fields = ['page', 'page_size', 'total_count', 'total_pages', 
                          'has_next', 'has_previous', 'next_page', 'previous_page']
        for field in required_fields:
            assert field in pagination, f"Missing pagination field: {field}"

    def test_pagination_default_parameters(self, client, sample_data):
        """Test default pagination parameters."""
        response = client.get('/api/brew_sessions')
        assert response.status_code == 200
        
        result = response.get_json()
        pagination = result['pagination']
        
        # Default values
        assert pagination['page'] == 1
        assert pagination['page_size'] == 30
        assert pagination['total_count'] >= 8  # At least our test data
        
    def test_pagination_with_page_size_3(self, client, sample_data):
        """Test pagination with page size 3."""
        # Test first page
        response = client.get('/api/brew_sessions?page=1&page_size=3')
        assert response.status_code == 200
        
        result = response.get_json()
        pagination = result['pagination']
        sessions = result['data']
        
        assert len(sessions) == 3
        assert pagination['page'] == 1
        assert pagination['page_size'] == 3
        assert pagination['total_count'] >= 8
        assert pagination['total_pages'] >= 3
        assert pagination['has_next'] is True
        assert pagination['has_previous'] is False
        assert pagination['next_page'] == 2
        assert pagination['previous_page'] is None

    def test_pagination_middle_page(self, client, sample_data):
        """Test pagination middle page."""
        response = client.get('/api/brew_sessions?page=2&page_size=3')
        assert response.status_code == 200
        
        result = response.get_json()
        pagination = result['pagination']
        sessions = result['data']
        
        assert len(sessions) == 3
        assert pagination['page'] == 2
        assert pagination['has_next'] is True
        assert pagination['has_previous'] is True
        assert pagination['next_page'] == 3
        assert pagination['previous_page'] == 1

    def test_pagination_last_page(self, client, sample_data):
        """Test pagination last page behavior."""
        # Get total pages first
        response = client.get('/api/brew_sessions?page_size=3')
        total_pages = response.get_json()['pagination']['total_pages']
        
        # Test last page
        response = client.get(f'/api/brew_sessions?page={total_pages}&page_size=3')
        assert response.status_code == 200
        
        result = response.get_json()
        pagination = result['pagination']
        
        assert pagination['page'] == total_pages
        assert pagination['has_next'] is False
        assert pagination['has_previous'] is True
        assert pagination['next_page'] is None
        assert pagination['previous_page'] == total_pages - 1

    def test_pagination_invalid_page_parameters(self, client, sample_data):
        """Test invalid page parameters are handled gracefully."""
        # Page 0 should default to 1
        response = client.get('/api/brew_sessions?page=0&page_size=3')
        assert response.status_code == 200
        assert response.get_json()['pagination']['page'] == 1
        
        # Negative page should default to 1
        response = client.get('/api/brew_sessions?page=-1&page_size=3')
        assert response.status_code == 200
        assert response.get_json()['pagination']['page'] == 1

    def test_pagination_invalid_page_size_parameters(self, client, sample_data):
        """Test invalid page size parameters are handled gracefully."""
        # Page size 0 should default to 30
        response = client.get('/api/brew_sessions?page=1&page_size=0')
        assert response.status_code == 200
        assert response.get_json()['pagination']['page_size'] == 30
        
        # Negative page size should default to 30
        response = client.get('/api/brew_sessions?page=1&page_size=-1')
        assert response.status_code == 200
        assert response.get_json()['pagination']['page_size'] == 30
        
        # Page size > 100 should be limited to 30
        response = client.get('/api/brew_sessions?page=1&page_size=150')
        assert response.status_code == 200
        assert response.get_json()['pagination']['page_size'] == 30

    def test_pagination_page_beyond_total(self, client, sample_data):
        """Test requesting page beyond total pages."""
        response = client.get('/api/brew_sessions?page=999&page_size=3')
        assert response.status_code == 200
        
        result = response.get_json()
        sessions = result['data']
        pagination = result['pagination']
        
        # Should return empty data but valid pagination metadata
        assert len(sessions) == 0
        assert pagination['page'] == 999
        assert pagination['has_next'] is False
        assert pagination['has_previous'] is True

    def test_pagination_sorting_newest_first(self, client, sample_data):
        """Test that sessions are sorted by timestamp, newest first."""
        response = client.get('/api/brew_sessions?page=1&page_size=8')
        assert response.status_code == 200
        
        sessions = response.get_json()['data']
        assert len(sessions) >= 8
        
        # Verify timestamps are in descending order (newest first)
        timestamps = [session['timestamp'] for session in sessions[:8]]
        sorted_timestamps = sorted(timestamps, reverse=True)
        assert timestamps == sorted_timestamps

    def test_pagination_with_different_page_sizes(self, client, sample_data):
        """Test pagination works correctly with different page sizes."""
        test_sizes = [1, 2, 5, 10]
        
        for page_size in test_sizes:
            response = client.get(f'/api/brew_sessions?page=1&page_size={page_size}')
            assert response.status_code == 200
            
            result = response.get_json()
            sessions = result['data']
            pagination = result['pagination']
            
            assert pagination['page_size'] == page_size
            assert len(sessions) <= page_size
            
            # If we have enough data, should return exactly page_size items
            if pagination['total_count'] >= page_size:
                assert len(sessions) == page_size

    def test_pagination_consistency_across_pages(self, client, sample_data):
        """Test that pagination is consistent - no duplicate or missing items."""
        # Get all sessions across multiple pages
        all_session_ids = set()
        page = 1
        page_size = 3
        
        while True:
            response = client.get(f'/api/brew_sessions?page={page}&page_size={page_size}')
            assert response.status_code == 200
            
            result = response.get_json()
            sessions = result['data']
            pagination = result['pagination']
            
            # Collect session IDs
            for session in sessions:
                session_id = session['id']
                assert session_id not in all_session_ids, f"Duplicate session ID {session_id} on page {page}"
                all_session_ids.add(session_id)
            
            if not pagination['has_next']:
                break
            page += 1
        
        # Verify we got at least our test data
        assert len(all_session_ids) >= 8

    def test_pagination_empty_result_set(self, client):
        """Test pagination behavior with empty result set."""
        # Use a user with no data
        response = client.get('/api/brew_sessions?user_id=empty_user&page=1&page_size=10')
        assert response.status_code == 200
        
        result = response.get_json()
        sessions = result['data']
        pagination = result['pagination']
        
        assert len(sessions) == 0
        assert pagination['total_count'] == 0
        assert pagination['total_pages'] == 1
        assert pagination['has_next'] is False
        assert pagination['has_previous'] is False
        assert pagination['next_page'] is None
        assert pagination['previous_page'] is None

    def test_pagination_preserves_session_enrichment(self, client, sample_data):
        """Test that pagination doesn't break session enrichment."""
        response = client.get('/api/brew_sessions?page=1&page_size=3')
        assert response.status_code == 200
        
        sessions = response.get_json()['data']
        
        for session in sessions:
            # Verify enriched fields are present
            assert 'brew_ratio' in session
            assert 'product_name' in session
            assert 'product_details' in session
            
            # Verify lookup objects are enriched
            if session.get('brew_method_id'):
                assert 'brew_method' in session
                assert session['brew_method'] is not None
                assert 'name' in session['brew_method']

    def test_pagination_large_page_size_limit(self, client, sample_data):
        """Test that very large page sizes are limited appropriately."""
        response = client.get('/api/brew_sessions?page=1&page_size=1000')
        assert response.status_code == 200
        
        pagination = response.get_json()['pagination']
        
        # Should be limited to max allowed (30)
        assert pagination['page_size'] == 30

    def test_pagination_string_parameters(self, client, sample_data):
        """Test pagination handles string parameters gracefully."""
        # String numbers should be converted
        response = client.get('/api/brew_sessions?page=2&page_size=3')
        assert response.status_code == 200
        
        pagination = response.get_json()['pagination']
        assert pagination['page'] == 2
        assert pagination['page_size'] == 3
        
        # Invalid strings should default to defaults
        response = client.get('/api/brew_sessions?page=invalid&page_size=also_invalid')
        assert response.status_code == 200
        
        pagination = response.get_json()['pagination']
        assert pagination['page'] == 1  # Default
        assert pagination['page_size'] == 30  # Default

    def test_server_side_sorting_by_product_name(self, client, sample_data):
        """Test server-side sorting by product_name (enriched field)."""
        # Test ascending sort
        response = client.get('/api/brew_sessions?page=1&page_size=5&sort=product_name&sort_direction=asc')
        assert response.status_code == 200
        
        result = response.get_json()
        sessions = result['data']
        assert len(sessions) > 0
        
        # Extract product names and verify ascending order
        product_names = [session.get('product_name', '') for session in sessions]
        sorted_names = sorted(product_names)
        assert product_names == sorted_names, f"Expected {sorted_names}, got {product_names}"
        
        # Test descending sort
        response = client.get('/api/brew_sessions?page=1&page_size=5&sort=product_name&sort_direction=desc')
        assert response.status_code == 200
        
        result = response.get_json()
        sessions_desc = result['data']
        
        product_names_desc = [session.get('product_name', '') for session in sessions_desc]
        sorted_names_desc = sorted(product_names_desc, reverse=True)
        assert product_names_desc == sorted_names_desc

    def test_server_side_sorting_by_brew_method(self, client, sample_data):
        """Test server-side sorting by brew_method (enriched field)."""
        # Create sessions with different brew methods
        product_response = client.post('/api/products', json={
            'product_name': 'Sorting Test Coffee',
            'roaster': 'Test Roaster',
            'bean_type': ['Arabica']
        })
        product_id = product_response.get_json()['id']
        
        batch_response = client.post('/api/products/' + str(product_id) + '/batches', json={
            'roast_date': '2024-01-15',
            'amount_grams': 500
        })
        batch_id = batch_response.get_json()['id']
        
        # Create sessions with different methods
        methods = ['V60', 'Chemex', 'AeroPress', 'French Press']
        for i, method in enumerate(methods):
            client.post(f'/api/batches/{batch_id}/brew_sessions', json={
                'brew_method': method,
                'timestamp': f'2024-01-15T{10+i}:00:00Z',
                'notes': f'Method test {i}'
            })
        
        # Test ascending sort by brew method
        response = client.get('/api/brew_sessions?page=1&page_size=10&sort=brew_method&sort_direction=asc')
        assert response.status_code == 200
        
        result = response.get_json()
        sessions = result['data']
        
        # Extract method names from sessions that have methods
        method_names = []
        for session in sessions:
            if session.get('brew_method') and session['brew_method'].get('name'):
                method_names.append(session['brew_method']['name'])
        
        # Verify we have our test methods
        test_methods_found = [name for name in method_names if name in methods]
        assert len(test_methods_found) >= 3, f"Expected at least 3 test methods, found: {test_methods_found}"
        
        # For sessions with methods, verify they're in sorted order
        if len(method_names) > 1:
            sorted_methods = sorted(method_names)
            assert method_names == sorted_methods, f"Methods not sorted: {method_names}"

    def test_server_side_sorting_by_score(self, client, sample_data):
        """Test server-side sorting by score field."""
        # Create sessions with different scores
        product_response = client.post('/api/products', json={
            'product_name': 'Score Test Coffee',
            'roaster': 'Test Roaster'
        })
        product_id = product_response.get_json()['id']
        
        batch_response = client.post('/api/products/' + str(product_id) + '/batches', json={
            'roast_date': '2024-01-16'
        })
        batch_id = batch_response.get_json()['id']
        
        # Create sessions with different scores
        scores = [8.5, 6.2, 9.1, 7.0]
        for i, score in enumerate(scores):
            client.post(f'/api/batches/{batch_id}/brew_sessions', json={
                'score': score,
                'timestamp': f'2024-01-16T{10+i}:00:00Z',
                'notes': f'Score test {score}'
            })
        
        # Test descending sort by score (highest first)
        response = client.get('/api/brew_sessions?page=1&page_size=10&sort=score&sort_direction=desc')
        assert response.status_code == 200
        
        result = response.get_json()
        sessions = result['data']
        
        # Extract scores from sessions that have scores
        session_scores = []
        for session in sessions:
            if session.get('score') and session['score'] > 0:
                session_scores.append(session['score'])
        
        # Verify we have our test scores and they're in descending order
        if len(session_scores) > 1:
            sorted_scores_desc = sorted(session_scores, reverse=True)
            assert session_scores == sorted_scores_desc, f"Scores not sorted descending: {session_scores}"

    def test_server_side_sorting_with_pagination(self, client, sample_data):
        """Test that server-side sorting works correctly across pagination boundaries."""
        # Get all sessions sorted by timestamp ascending
        all_sessions = []
        page = 1
        page_size = 3
        
        while True:
            response = client.get(f'/api/brew_sessions?page={page}&page_size={page_size}&sort=timestamp&sort_direction=asc')
            assert response.status_code == 200
            
            result = response.get_json()
            sessions = result['data']
            pagination = result['pagination']
            
            all_sessions.extend(sessions)
            
            if not pagination['has_next']:
                break
            page += 1
        
        # Verify all sessions are in ascending timestamp order
        timestamps = [session['timestamp'] for session in all_sessions]
        sorted_timestamps = sorted(timestamps)
        assert timestamps == sorted_timestamps, "Sessions not properly sorted across pagination"
        
        # Verify no duplicate sessions across pages
        session_ids = [session['id'] for session in all_sessions]
        assert len(session_ids) == len(set(session_ids)), "Duplicate sessions found across pages"

    def test_server_side_sorting_invalid_parameters(self, client, sample_data):
        """Test server-side sorting with invalid parameters."""
        # Invalid sort field should default to timestamp
        response = client.get('/api/brew_sessions?sort=invalid_field&sort_direction=asc')
        assert response.status_code == 200
        
        # Invalid sort direction should default to desc
        response = client.get('/api/brew_sessions?sort=timestamp&sort_direction=invalid')
        assert response.status_code == 200
        
        # Should still return valid data
        result = response.get_json()
        assert 'data' in result
        assert 'pagination' in result
        assert isinstance(result['data'], list)

    def test_server_side_sorting_default_parameters(self, client, sample_data):
        """Test default sorting parameters."""
        response = client.get('/api/brew_sessions')
        assert response.status_code == 200
        
        result = response.get_json()
        sessions = result['data']
        
        # Default should be timestamp descending (newest first)
        if len(sessions) > 1:
            timestamps = [session['timestamp'] for session in sessions]
            sorted_timestamps_desc = sorted(timestamps, reverse=True)
            assert timestamps == sorted_timestamps_desc, "Default sort should be timestamp desc"