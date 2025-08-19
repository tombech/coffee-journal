"""
Test for circular reference regression in shots and shot sessions APIs.
This test ensures that the JSON serialization works properly without circular references.
"""

import pytest
import json
from coffeejournal import create_app
from coffeejournal.repositories.factory import get_repository_factory


class TestCircularReferenceRegression:
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app({
            'TESTING': True,
            'DATA_DIR': 'test_data',
            'SECRET_KEY': 'test-secret-key'
        })
        with app.test_client() as client:
            yield client

    def test_shots_api_no_circular_reference(self, client):
        """Test that shots API doesn't have circular reference issues."""
        # Test with various parameter combinations that might trigger the issue
        test_cases = [
            '/api/shots',
            '/api/shots?page=1&page_size=30',
            '/api/shots?page=1&page_size=30&sort=timestamp&sort_direction=desc',
            '/api/shots?page=1&page_size=30&sort=timestamp&sort_direction=asc',
            '/api/shots?include_session_shots=true',
            '/api/shots?product_id=1',
            '/api/shots?brewer_id=1',
        ]
        
        for endpoint in test_cases:
            response = client.get(endpoint)
            
            # Should not return 500 error
            assert response.status_code != 500, f"Endpoint {endpoint} returned 500 error"
            
            if response.status_code == 200:
                # Should be able to parse JSON without circular reference error
                try:
                    data = response.get_json()
                    # Try to serialize back to JSON to detect circular references
                    json.dumps(data)
                    assert 'data' in data, f"Response should have 'data' key for {endpoint}"
                except (ValueError, TypeError) as e:
                    pytest.fail(f"Circular reference or JSON serialization error in {endpoint}: {e}")

    def test_shot_sessions_api_no_circular_reference(self, client):
        """Test that shot sessions API doesn't have circular reference issues."""
        # Test with various parameter combinations that might trigger the issue
        test_cases = [
            '/api/shot_sessions',
            '/api/shot_sessions?page=1&page_size=30',
            '/api/shot_sessions?page=1&page_size=30&sort=created_at&sort_direction=desc',
            '/api/shot_sessions?page=1&page_size=30&sort=created_at&sort_direction=asc',
            '/api/shot_sessions?include_shots=true',
            '/api/shot_sessions?include_shots=false',
            '/api/shot_sessions?product_id=1',
            '/api/shot_sessions?brewer_id=1',
        ]
        
        for endpoint in test_cases:
            response = client.get(endpoint)
            
            # Should not return 500 error
            assert response.status_code != 500, f"Endpoint {endpoint} returned 500 error"
            
            if response.status_code == 200:
                # Should be able to parse JSON without circular reference error
                try:
                    data = response.get_json()
                    # Try to serialize back to JSON to detect circular references
                    json.dumps(data)
                    assert 'data' in data, f"Response should have 'data' key for {endpoint}"
                except (ValueError, TypeError) as e:
                    pytest.fail(f"Circular reference or JSON serialization error in {endpoint}: {e}")

    def test_shots_filter_options_no_circular_reference(self, client):
        """Test that shots filter options API doesn't have circular reference issues."""
        response = client.get('/api/shots/filter_options')
        
        # Should not return 500 error
        assert response.status_code != 500, "Shots filter options returned 500 error"
        
        if response.status_code == 200:
            try:
                data = response.get_json()
                # Try to serialize back to JSON to detect circular references
                json.dumps(data)
            except (ValueError, TypeError) as e:
                pytest.fail(f"Circular reference or JSON serialization error in shots filter options: {e}")

    def test_shot_sessions_filter_options_no_circular_reference(self, client):
        """Test that shot sessions filter options API doesn't have circular reference issues."""
        response = client.get('/api/shot_sessions/filter_options')
        
        # Should not return 500 error
        assert response.status_code != 500, "Shot sessions filter options returned 500 error"
        
        if response.status_code == 200:
            try:
                data = response.get_json()
                # Try to serialize back to JSON to detect circular references
                json.dumps(data)
            except (ValueError, TypeError) as e:
                pytest.fail(f"Circular reference or JSON serialization error in shot sessions filter options: {e}")

    def test_individual_shot_detail_no_circular_reference(self, client):
        """Test that individual shot detail doesn't have circular reference issues."""
        # First get available shots
        response = client.get('/api/shots?page_size=1')
        if response.status_code == 200:
            data = response.get_json()
            if data.get('data'):
                shot_id = data['data'][0]['id']
                
                # Test individual shot endpoint
                detail_response = client.get(f'/api/shots/{shot_id}')
                assert detail_response.status_code != 500, f"Shot detail {shot_id} returned 500 error"
                
                if detail_response.status_code == 200:
                    try:
                        detail_data = detail_response.get_json()
                        # Try to serialize back to JSON to detect circular references
                        json.dumps(detail_data)
                    except (ValueError, TypeError) as e:
                        pytest.fail(f"Circular reference in shot detail {shot_id}: {e}")

    def test_individual_shot_session_detail_no_circular_reference(self, client):
        """Test that individual shot session detail doesn't have circular reference issues."""
        # First get available shot sessions
        response = client.get('/api/shot_sessions?page_size=1')
        if response.status_code == 200:
            data = response.get_json()
            if data.get('data'):
                session_id = data['data'][0]['id']
                
                # Test individual shot session endpoint
                detail_response = client.get(f'/api/shot_sessions/{session_id}')
                assert detail_response.status_code != 500, f"Shot session detail {session_id} returned 500 error"
                
                if detail_response.status_code == 200:
                    try:
                        detail_data = detail_response.get_json()
                        # Try to serialize back to JSON to detect circular references
                        json.dumps(detail_data)
                    except (ValueError, TypeError) as e:
                        pytest.fail(f"Circular reference in shot session detail {session_id}: {e}")

    def test_enrichment_logic_no_circular_reference(self, client):
        """Test that the enrichment logic itself doesn't create circular references."""
        from coffeejournal.api.shots import enrich_shot
        from coffeejournal.api.shot_sessions import enrich_shot_session_with_shots
        
        # Get a real shot and session to test enrichment
        factory = get_repository_factory()
        
        # Test shot enrichment
        shot_repo = factory.get_shot_repository(None)
        shots = shot_repo.find_all()
        if shots:
            shot = shots[0].copy()  # Make a copy to avoid modifying original
            enriched_shot = enrich_shot(shot, factory, None)
            
            # Should be able to serialize without circular reference
            try:
                json.dumps(enriched_shot)
            except (ValueError, TypeError) as e:
                pytest.fail(f"Circular reference in shot enrichment: {e}")
        
        # Test shot session enrichment
        session_repo = factory.get_shot_session_repository(None)
        sessions = session_repo.find_all()
        if sessions:
            session = sessions[0].copy()  # Make a copy to avoid modifying original
            enriched_session = enrich_shot_session_with_shots(session, factory, None)
            
            # Should be able to serialize without circular reference
            try:
                json.dumps(enriched_session)
            except (ValueError, TypeError) as e:
                pytest.fail(f"Circular reference in shot session enrichment: {e}")

    def test_specific_circular_reference_reproduction(self, client):
        """Test the exact API call that produces the circular reference error."""
        # This reproduces the exact error reported by the user
        response = client.get('/api/shot_sessions?page=1&page_size=30&sort=created_at&sort_direction=desc')
        
        # Should not return 500 error
        assert response.status_code != 500, "Shot sessions API returned 500 error with circular reference"
        
        if response.status_code == 200:
            try:
                data = response.get_json()
                # Try to serialize back to JSON to detect circular references
                json.dumps(data)
                assert 'data' in data, "Response should have 'data' key"
            except (ValueError, TypeError) as e:
                pytest.fail(f"Circular reference in shot sessions API: {e}")
        elif response.status_code == 400:
            # Check if we get a circular reference error message
            try:
                error_data = response.get_json()
                if 'error' in error_data and 'Circular reference' in error_data['error']:
                    pytest.fail(f"Circular reference detected in API response: {error_data['error']}")
            except:
                pass