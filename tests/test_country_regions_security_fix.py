"""
Test country/regions security fix verification.

This test specifically verifies that the critical security vulnerability
in handle_country_regions() has been fixed.
"""

import pytest
import tempfile
from coffeejournal import create_app


class TestCountryRegionsSecurityFix:
    """Test the country/regions security fix."""
    
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
    
    def test_country_regions_endpoint_now_requires_user_id(self, client):
        """Verify that country/regions endpoint now properly validates user_id."""
        
        # First create required data for user1
        country_response = client.post('/api/countries?user_id=user1', json={'name': 'Test Country'})
        assert country_response.status_code == 201
        country_id = country_response.get_json()['id']
        
        # Test GET: user1 should see empty regions list (proper isolation)
        response = client.get(f'/api/countries/{country_id}/regions?user_id=user1')
        assert response.status_code == 200
        user1_regions = response.get_json()
        assert len(user1_regions) == 0
        
        # Test POST: user1 can create region
        region_response = client.post(f'/api/countries/{country_id}/regions?user_id=user1', json={
            'name': 'Test Region'
        })
        assert region_response.status_code == 201
        region_data = region_response.get_json()
        assert region_data['name'] == 'Test Region'
        assert region_data['country_id'] == country_id
        
        # Verify user1 can see their region
        response = client.get(f'/api/countries/{country_id}/regions?user_id=user1')
        assert response.status_code == 200
        user1_regions = response.get_json()
        assert len(user1_regions) == 1
        assert user1_regions[0]['name'] == 'Test Region'
        
        # CRITICAL SECURITY TEST: user2 should NOT see user1's data
        response = client.get(f'/api/countries/{country_id}/regions?user_id=user2')
        assert response.status_code == 404  # Country doesn't exist for user2
        
        # User2 should NOT be able to create regions in user1's country
        response = client.post(f'/api/countries/{country_id}/regions?user_id=user2', json={
            'name': 'Malicious Region'
        })
        assert response.status_code == 404  # Country not found for user2
        
        print("✅ Country/regions endpoint security fix verified - proper user isolation working")
    
    def test_country_regions_endpoint_validates_user_id_format(self, client):
        """Verify that invalid user_id values are rejected."""
        
        # Test with malicious user_id (path traversal attempt)
        response = client.get('/api/countries/1/regions?user_id=../../../etc/passwd')
        assert response.status_code == 400
        assert 'error' in response.get_json()
        
        # Test with empty user_id
        response = client.get('/api/countries/1/regions?user_id=')
        assert response.status_code == 400
        assert 'error' in response.get_json()
        
        print("✅ User ID validation working correctly")