"""
Tests for default/favorite lookup items functionality.
"""
import pytest
from coffeejournal import create_app


class TestDefaultLookupItems:
    """Test class for verifying default lookup items."""
    
    @pytest.fixture
    def app(self, tmp_path):
        """Create test app with temporary data directory."""
        test_config = {
            'TESTING': True,
            'DATA_DIR': str(tmp_path)
        }
        app = create_app(test_config=test_config)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_create_lookup_item_with_default_flag(self, client):
        """Test creating a lookup item with is_default=True."""
        # Create first roaster as default
        roaster_data = {'name': 'Default Roaster', 'is_default': True}
        response = client.post('/api/roasters', json=roaster_data)
        
        assert response.status_code == 201
        roaster = response.get_json()
        assert roaster['is_default'] is True
        
        # Verify it's retrievable as default
        default_response = client.get('/api/roasters/default')
        assert default_response.status_code == 200
        default_roaster = default_response.get_json()
        assert default_roaster['id'] == roaster['id']
    
    def test_create_lookup_item_without_default_flag(self, client):
        """Test creating a lookup item without is_default defaults to False."""
        roaster_data = {'name': 'Regular Roaster'}
        response = client.post('/api/roasters', json=roaster_data)
        
        assert response.status_code == 201
        roaster = response.get_json()
        assert roaster['is_default'] is False
    
    def test_only_one_default_per_type(self, client):
        """Test that only one item can be default per type."""
        # Create first default roaster
        roaster1_data = {'name': 'First Default', 'is_default': True}
        response1 = client.post('/api/roasters', json=roaster1_data)
        assert response1.status_code == 201
        roaster1 = response1.get_json()
        assert roaster1['is_default'] is True
        
        # Create second default roaster - this should clear the first one
        roaster2_data = {'name': 'Second Default', 'is_default': True}
        response2 = client.post('/api/roasters', json=roaster2_data)
        assert response2.status_code == 201
        roaster2 = response2.get_json()
        assert roaster2['is_default'] is True
        
        # Verify only the second one is default
        default_response = client.get('/api/roasters/default')
        assert default_response.status_code == 200
        default_roaster = default_response.get_json()
        assert default_roaster['id'] == roaster2['id']
        
        # Verify first roaster is no longer default
        roaster1_response = client.get(f'/api/roasters/{roaster1["id"]}')
        updated_roaster1 = roaster1_response.get_json()
        assert updated_roaster1['is_default'] is False
    
    def test_set_default_via_endpoint(self, client):
        """Test setting default via the set_default endpoint."""
        # Create two roasters
        roaster1_data = {'name': 'Roaster 1'}
        roaster2_data = {'name': 'Roaster 2'}
        
        response1 = client.post('/api/roasters', json=roaster1_data)
        response2 = client.post('/api/roasters', json=roaster2_data)
        
        roaster1 = response1.get_json()
        roaster2 = response2.get_json()
        
        # Set roaster1 as default
        set_default_response = client.post(f'/api/roasters/{roaster1["id"]}/set_default')
        assert set_default_response.status_code == 200
        updated_roaster1 = set_default_response.get_json()
        assert updated_roaster1['is_default'] is True
        
        # Verify it's the default
        default_response = client.get('/api/roasters/default')
        assert default_response.status_code == 200
        default_roaster = default_response.get_json()
        assert default_roaster['id'] == roaster1['id']
        
        # Set roaster2 as default - should clear roaster1
        set_default_response = client.post(f'/api/roasters/{roaster2["id"]}/set_default')
        assert set_default_response.status_code == 200
        updated_roaster2 = set_default_response.get_json()
        assert updated_roaster2['is_default'] is True
        
        # Verify new default
        default_response = client.get('/api/roasters/default')
        default_roaster = default_response.get_json()
        assert default_roaster['id'] == roaster2['id']
    
    def test_clear_default_via_endpoint(self, client):
        """Test clearing default via the clear_default endpoint."""
        # Create default roaster
        roaster_data = {'name': 'Default Roaster', 'is_default': True}
        response = client.post('/api/roasters', json=roaster_data)
        roaster = response.get_json()
        
        # Clear default
        clear_response = client.post(f'/api/roasters/{roaster["id"]}/clear_default')
        assert clear_response.status_code == 200
        updated_roaster = clear_response.get_json()
        assert updated_roaster['is_default'] is False
        
        # Verify no default exists
        default_response = client.get('/api/roasters/default')
        assert default_response.status_code == 404
    
    def test_update_default_flag_via_put(self, client):
        """Test updating the is_default flag via PUT endpoint."""
        # Create roaster
        roaster_data = {'name': 'Test Roaster'}
        response = client.post('/api/roasters', json=roaster_data)
        roaster = response.get_json()
        
        # Update to default
        update_data = {'is_default': True}
        update_response = client.put(f'/api/roasters/{roaster["id"]}', json=update_data)
        assert update_response.status_code == 200
        updated_roaster = update_response.get_json()
        assert updated_roaster['is_default'] is True
        
        # Update back to non-default
        update_data = {'is_default': False}
        update_response = client.put(f'/api/roasters/{roaster["id"]}', json=update_data)
        assert update_response.status_code == 200
        updated_roaster = update_response.get_json()
        assert updated_roaster['is_default'] is False
    
    def test_get_default_when_none_exists(self, client):
        """Test getting default when no default is set."""
        # No defaults exist yet
        default_response = client.get('/api/roasters/default')
        assert default_response.status_code == 404
        error = default_response.get_json()
        assert 'No default roaster set' in error['error']
    
    def test_set_default_nonexistent_item(self, client):
        """Test setting default on non-existent item."""
        set_response = client.post('/api/roasters/99999/set_default')
        assert set_response.status_code == 404
    
    def test_clear_default_nonexistent_item(self, client):
        """Test clearing default on non-existent item."""
        clear_response = client.post('/api/roasters/99999/clear_default')
        assert clear_response.status_code == 404
    
    def test_default_with_audit_timestamps(self, client):
        """Test that default functionality works with audit timestamps."""
        roaster_data = {'name': 'Default Roaster', 'is_default': True}
        response = client.post('/api/roasters', json=roaster_data)
        
        assert response.status_code == 201
        roaster = response.get_json()
        assert 'created_at' in roaster
        assert 'updated_at' in roaster
        assert roaster['is_default'] is True
    
    def test_multiple_types_can_have_defaults(self, client):
        """Test that different lookup types can each have their own default."""
        # Set default roaster
        roaster_data = {'name': 'Default Roaster', 'is_default': True}
        roaster_response = client.post('/api/roasters', json=roaster_data)
        assert roaster_response.status_code == 201
        
        # Set default grinder
        grinder_data = {'name': 'Default Grinder', 'is_default': True}
        grinder_response = client.post('/api/grinders', json=grinder_data)
        assert grinder_response.status_code == 201
        
        # Both should be retrievable as defaults
        default_roaster_response = client.get('/api/roasters/default')
        assert default_roaster_response.status_code == 200
        
        default_grinder_response = client.get('/api/grinders/default')
        assert default_grinder_response.status_code == 200
        
        # Verify they're different items
        default_roaster = default_roaster_response.get_json()
        default_grinder = default_grinder_response.get_json()
        assert default_roaster['name'] == 'Default Roaster'
        assert default_grinder['name'] == 'Default Grinder'