"""
Test comprehensive CRUD operations for all lookup types.
"""
import pytest


class TestLookupCRUD:
    """Test CRUD operations for all lookup types."""
    
    LOOKUP_TYPES = [
        ('roasters', 'roaster'),
        ('bean_types', 'bean_type'),
        ('countries', 'country'),
        ('brew_methods', 'brew_method'),
        ('recipes', 'recipe'),
        ('decaf_methods', 'decaf_method'),
        ('grinders', 'grinder'),
        ('filters', 'filter'),
        ('kettles', 'kettle'),
        ('scales', 'scale'),
    ]
    
    @pytest.mark.parametrize("endpoint,singular", LOOKUP_TYPES)
    def test_create_lookup_item(self, client, endpoint, singular):
        """Test creating a lookup item with extended properties."""
        data = {
            'name': f'Test {singular.title()}',
            'description': f'Test {singular} description',
            'notes': f'Some notes about this {singular}',
            'product_url': f'https://example.com/{singular}',
            'image_url': f'https://example.com/{singular}.jpg',
            'short_form': f'T{singular[0].upper()}',
            'icon': f'{singular}.png'
        }
        
        response = client.post(f'/api/{endpoint}', json=data)
        assert response.status_code == 201
        
        item = response.get_json()
        assert item['name'] == data['name']
        assert item['description'] == data['description']
        assert item['notes'] == data['notes']
        assert item['product_url'] == data['product_url']
        assert item['image_url'] == data['image_url']
        assert item['short_form'] == data['short_form']
        assert item['icon'] == data['icon']
        assert item['id'] is not None
    
    @pytest.mark.parametrize("endpoint,singular", LOOKUP_TYPES)
    def test_get_all_lookup_items(self, client, endpoint, singular):
        """Test getting all lookup items."""
        # Create two items
        client.post(f'/api/{endpoint}', json={'name': f'{singular.title()} 1'})
        client.post(f'/api/{endpoint}', json={'name': f'{singular.title()} 2'})
        
        response = client.get(f'/api/{endpoint}')
        assert response.status_code == 200
        
        items = response.get_json()
        assert len(items) >= 2
        names = [item['name'] for item in items]
        assert f'{singular.title()} 1' in names
        assert f'{singular.title()} 2' in names
    
    @pytest.mark.parametrize("endpoint,singular", LOOKUP_TYPES)
    def test_get_lookup_item_by_id(self, client, endpoint, singular):
        """Test getting a specific lookup item by ID."""
        # Create an item
        create_response = client.post(f'/api/{endpoint}', json={
            'name': f'Specific {singular.title()}',
            'description': 'Specific description'
        })
        assert create_response.status_code == 201
        
        created_item = create_response.get_json()
        item_id = created_item['id']
        
        # Get the item by ID
        response = client.get(f'/api/{endpoint}/{item_id}')
        assert response.status_code == 200
        
        item = response.get_json()
        assert item['id'] == item_id
        assert item['name'] == f'Specific {singular.title()}'
        assert item['description'] == 'Specific description'
    
    @pytest.mark.parametrize("endpoint,singular", LOOKUP_TYPES)
    def test_get_nonexistent_lookup_item(self, client, endpoint, singular):
        """Test getting a non-existent lookup item returns 404."""
        response = client.get(f'/api/{endpoint}/99999')
        assert response.status_code == 404
        
        error = response.get_json()
        assert 'error' in error
        assert 'not found' in error['error'].lower()
    
    @pytest.mark.parametrize("endpoint,singular", LOOKUP_TYPES)
    def test_update_lookup_item(self, client, endpoint, singular):
        """Test updating a lookup item."""
        # Create an item
        create_response = client.post(f'/api/{endpoint}', json={
            'name': f'Original {singular.title()}',
            'description': 'Original description'
        })
        item_id = create_response.get_json()['id']
        
        # Update the item
        update_data = {
            'name': f'Updated {singular.title()}',
            'description': 'Updated description',
            'notes': 'New notes',
            'product_url': 'https://updated.com'
        }
        
        response = client.put(f'/api/{endpoint}/{item_id}', json=update_data)
        assert response.status_code == 200
        
        updated_item = response.get_json()
        assert updated_item['name'] == update_data['name']
        assert updated_item['description'] == update_data['description']
        assert updated_item['notes'] == update_data['notes']
        assert updated_item['product_url'] == update_data['product_url']
    
    @pytest.mark.parametrize("endpoint,singular", LOOKUP_TYPES)
    def test_update_nonexistent_lookup_item(self, client, endpoint, singular):
        """Test updating a non-existent lookup item returns 404."""
        update_data = {'name': 'Updated Name'}
        
        response = client.put(f'/api/{endpoint}/99999', json=update_data)
        assert response.status_code == 404
    
    @pytest.mark.parametrize("endpoint,singular", LOOKUP_TYPES)
    def test_delete_lookup_item(self, client, endpoint, singular):
        """Test deleting a lookup item."""
        # Create an item
        create_response = client.post(f'/api/{endpoint}', json={
            'name': f'To Delete {singular.title()}'
        })
        item_id = create_response.get_json()['id']
        
        # Delete the item
        response = client.delete(f'/api/{endpoint}/{item_id}')
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = client.get(f'/api/{endpoint}/{item_id}')
        assert get_response.status_code == 404
    
    @pytest.mark.parametrize("endpoint,singular", LOOKUP_TYPES)
    def test_delete_nonexistent_lookup_item(self, client, endpoint, singular):
        """Test deleting a non-existent lookup item returns 404."""
        response = client.delete(f'/api/{endpoint}/99999')
        assert response.status_code == 404


class TestLookupValidation:
    """Test validation for lookup CRUD operations."""
    
    @pytest.mark.parametrize("endpoint,singular", TestLookupCRUD.LOOKUP_TYPES)
    def test_create_lookup_item_without_name(self, client, endpoint, singular):
        """Test creating a lookup item without required name field."""
        data = {
            'description': 'Missing name field'
        }
        
        response = client.post(f'/api/{endpoint}', json=data)
        assert response.status_code == 400
        
        error = response.get_json()
        assert 'error' in error
        assert 'name' in error['error'].lower()
    
    @pytest.mark.parametrize("endpoint,singular", TestLookupCRUD.LOOKUP_TYPES)
    def test_create_lookup_item_empty_name(self, client, endpoint, singular):
        """Test creating a lookup item with empty name."""
        data = {
            'name': ''
        }
        
        response = client.post(f'/api/{endpoint}', json=data)
        assert response.status_code == 400
    
    @pytest.mark.parametrize("endpoint,singular", TestLookupCRUD.LOOKUP_TYPES)
    def test_update_lookup_item_empty_data(self, client, endpoint, singular):
        """Test updating a lookup item with no data."""
        # Create an item first
        create_response = client.post(f'/api/{endpoint}', json={'name': 'Test Item'})
        item_id = create_response.get_json()['id']
        
        # Try to update with no data
        response = client.put(f'/api/{endpoint}/{item_id}', json={})
        assert response.status_code == 400