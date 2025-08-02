"""
Specific test for regions isolation to understand the issue.
"""

import pytest
import tempfile
from coffeejournal import create_app


class TestRegionsSpecificIsolation:
    """Test regions specific isolation."""
    
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
    
    def test_regions_specific_isolation_issue(self, client):
        """Test regions isolation in detail."""
        
        # Create country for user1
        country_response = client.post('/api/countries?user_id=user1', json={
            'name': 'User1 Country'
        })
        assert country_response.status_code == 201
        country_data = country_response.get_json()
        country_id = country_data['id']
        
        # Create region for user1
        region_response = client.post('/api/regions?user_id=user1', json={
            'name': 'User1 Region',
            'country_id': country_id
        })
        print(f"Region create response: {region_response.status_code}, {region_response.get_json()}")
        assert region_response.status_code == 201
        
        # Check what user1 sees
        user1_regions_response = client.get('/api/regions?user_id=user1')
        print(f"User1 regions: {user1_regions_response.get_json()}")
        assert user1_regions_response.status_code == 200
        user1_regions = user1_regions_response.get_json()
        assert len(user1_regions) == 1
        
        # Check what user2 sees (should be empty)
        user2_regions_response = client.get('/api/regions?user_id=user2')
        print(f"User2 regions: {user2_regions_response.get_json()}")
        assert user2_regions_response.status_code == 200
        user2_regions = user2_regions_response.get_json()
        
        if len(user2_regions) > 0:
            print(f"❌ ISOLATION FAILURE: User2 can see {len(user2_regions)} regions")
            for region in user2_regions:
                print(f"  - {region}")
        else:
            print("✅ Proper isolation: User2 sees no regions")