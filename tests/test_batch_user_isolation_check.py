"""
Batch test to identify all endpoints that lack proper user isolation.
"""

import pytest
import tempfile
from coffeejournal import create_app


class TestBatchUserIsolationCheck:
    """Test user isolation across all remaining endpoints."""
    
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
    
    def test_all_remaining_lookup_endpoints_for_isolation(self, client):
        """Test all remaining lookup endpoints for proper user isolation."""
        
        # Test data for each endpoint type
        test_cases = [
            {
                'name': 'regions',
                'create_data': {'name': 'User1 Region', 'country_id': 1},
                'setup_country': True  # Need to create a country first
            },
            {
                'name': 'brew_methods',
                'create_data': {'name': 'User1 Brew Method'}
            },
            {
                'name': 'recipes',
                'create_data': {'name': 'User1 Recipe'}
            },
            {
                'name': 'grinders',
                'create_data': {'name': 'User1 Grinder'}
            },
            {
                'name': 'filters',
                'create_data': {'name': 'User1 Filter'}
            },
            {
                'name': 'kettles',
                'create_data': {'name': 'User1 Kettle'}
            },
            {
                'name': 'scales',
                'create_data': {'name': 'User1 Scale'}
            },
            {
                'name': 'decaf_methods',
                'create_data': {'name': 'User1 Decaf Method'}
            }
        ]
        
        for test_case in test_cases:
            endpoint = test_case['name']
            create_data = test_case['create_data']
            
            print(f"\n=== Testing {endpoint} isolation ===")
            
            # Setup country for regions if needed
            if test_case.get('setup_country'):
                country_response = client.post('/api/countries?user_id=user1', json={
                    'name': 'Test Country for Regions'
                })
                assert country_response.status_code == 201
                country_data = country_response.get_json()
                create_data['country_id'] = country_data['id']
            
            # User1 creates an item
            response = client.post(f'/api/{endpoint}?user_id=user1', json=create_data)
            assert response.status_code == 201, f"Failed to create {endpoint} for user1: {response.get_json()}"
            
            # User1 should see their item
            response = client.get(f'/api/{endpoint}?user_id=user1')
            assert response.status_code == 200, f"Failed to get {endpoint} for user1"
            user1_items = response.get_json()
            assert len(user1_items) >= 1, f"User1 should see their {endpoint}"
            
            # User2 should NOT see User1's item (isolation test)
            response = client.get(f'/api/{endpoint}?user_id=user2')
            assert response.status_code == 200, f"Failed to get {endpoint} for user2"
            user2_items = response.get_json()
            
            # Check isolation
            if len(user2_items) > 0:
                # Find if any items belong to user1 (they shouldn't)
                user1_item_names = [item['name'] for item in user1_items]
                user2_item_names = [item['name'] for item in user2_items]
                
                overlapping_items = set(user1_item_names) & set(user2_item_names)
                if overlapping_items:
                    pytest.fail(f"❌ {endpoint} NOT properly isolated! User2 can see User1's items: {overlapping_items}")
                else:
                    print(f"✅ {endpoint} properly isolated (different items)")
            else:
                print(f"✅ {endpoint} properly isolated (user2 sees no items)")
    
    def test_batch_endpoints_support_user_id_parameter(self, client):
        """Test that all endpoints accept user_id parameter without errors."""
        
        # Test endpoints that should support user_id
        endpoints_to_test = [
            '/api/regions',
            '/api/brew_methods', 
            '/api/recipes',
            '/api/grinders',
            '/api/filters',
            '/api/kettles',
            '/api/scales',
            '/api/decaf_methods'
        ]
        
        for endpoint in endpoints_to_test:
            print(f"\n=== Testing {endpoint} user_id parameter support ===")
            
            # GET request with user_id should not return 400 error
            response = client.get(f'{endpoint}?user_id=test_user')
            assert response.status_code == 200, f"{endpoint} should accept user_id parameter, got {response.status_code}: {response.get_json()}"
            print(f"✅ {endpoint} accepts user_id parameter")