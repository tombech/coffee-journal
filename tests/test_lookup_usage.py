"""
Test usage checking and reference updating for lookup types.
"""
import pytest


class TestUsageChecking:
    """Test usage checking functionality for lookup types."""
    
    def test_roaster_usage_checking(self, client):
        """Test usage checking for roasters."""
        # Create a roaster
        roaster_response = client.post('/api/roasters', json={'name': 'Test Roaster'})
        roaster_id = roaster_response.get_json()['id']
        
        # Check usage when not in use
        usage_response = client.get(f'/api/roasters/{roaster_id}/usage')
        assert usage_response.status_code == 200
        
        usage_info = usage_response.get_json()
        assert usage_info['in_use'] is False
        assert usage_info['usage_count'] == 0
        assert usage_info['usage_type'] == 'products'
        
        # Create a product using this roaster
        client.post('/api/products', json={
            'roaster': 'Test Roaster',
            'product_name': 'Test Product'
        })
        
        # Check usage when in use
        usage_response = client.get(f'/api/roasters/{roaster_id}/usage')
        usage_info = usage_response.get_json()
        assert usage_info['in_use'] is True
        assert usage_info['usage_count'] == 1
        assert usage_info['usage_type'] == 'products'
    
    def test_bean_type_usage_checking(self, client):
        """Test usage checking for bean types."""
        # Create a bean type
        bean_type_response = client.post('/api/bean_types', json={'name': 'Test Bean'})
        bean_type_id = bean_type_response.get_json()['id']
        
        # Check usage when not in use
        usage_response = client.get(f'/api/bean_types/{bean_type_id}/usage')
        usage_info = usage_response.get_json()
        assert usage_info['in_use'] is False
        assert usage_info['usage_count'] == 0
        
        # Create products using this bean type
        client.post('/api/products', json={
            'roaster': 'Test',
            'bean_type': ['Test Bean']
        })
        client.post('/api/products', json={
            'roaster': 'Test',
            'bean_type': 'Test Bean'  # Test single value
        })
        
        # Check usage when in use
        usage_response = client.get(f'/api/bean_types/{bean_type_id}/usage')
        usage_info = usage_response.get_json()
        assert usage_info['in_use'] is True
        assert usage_info['usage_count'] == 2
    
    def test_country_usage_checking(self, client):
        """Test usage checking for countries."""
        # Create a country
        country_response = client.post('/api/countries', json={'name': 'Test Country'})
        country_id = country_response.get_json()['id']
        
        # Create a product using this country
        client.post('/api/products', json={
            'roaster': 'Test',
            'country': 'Test Country'
        })
        
        # Check usage
        usage_response = client.get(f'/api/countries/{country_id}/usage')
        usage_info = usage_response.get_json()
        assert usage_info['in_use'] is True
        assert usage_info['usage_count'] == 1
    
    def test_brew_method_usage_checking(self, client):
        """Test usage checking for brew methods."""
        # Create a brew method
        brew_method_response = client.post('/api/brew_methods', json={'name': 'Test Method'})
        brew_method_id = brew_method_response.get_json()['id']
        
        # Create a product and batch first
        product_response = client.post('/api/products', json={
            'roaster': 'Test Roaster',
            'product_name': 'Test Product'
        })
        product_id = product_response.get_json()['id']
        
        batch_response = client.post(f'/api/products/{product_id}/batches', json={
            'roast_date': '2024-01-01',
            'amount_grams': 250
        })
        batch_id = batch_response.get_json()['id']
        
        # Create brew sessions using this method
        client.post(f'/api/batches/{batch_id}/brew_sessions', json={
            'brew_method_id': brew_method_id,
            'timestamp': '2024-01-01T10:00:00'
        })
        client.post(f'/api/batches/{batch_id}/brew_sessions', json={
            'brew_method_id': brew_method_id,
            'timestamp': '2024-01-02T10:00:00'
        })
        
        # Check usage
        usage_response = client.get(f'/api/brew_methods/{brew_method_id}/usage')
        usage_info = usage_response.get_json()
        assert usage_info['in_use'] is True
        assert usage_info['usage_count'] == 2
        assert usage_info['usage_type'] == 'brew_sessions'
    
    def test_recipe_usage_checking(self, client):
        """Test usage checking for recipes."""
        # Create a recipe
        recipe_response = client.post('/api/recipes', json={'name': 'Test Recipe'})
        recipe_id = recipe_response.get_json()['id']
        
        # Create a product and batch first
        product_response = client.post('/api/products', json={
            'roaster': 'Test Roaster',
            'product_name': 'Test Product'
        })
        product_id = product_response.get_json()['id']
        
        batch_response = client.post(f'/api/products/{product_id}/batches', json={
            'roast_date': '2024-01-01',
            'amount_grams': 250
        })
        batch_id = batch_response.get_json()['id']
        
        # Create a brew session using this recipe
        client.post(f'/api/batches/{batch_id}/brew_sessions', json={
            'recipe_id': recipe_id,
            'timestamp': '2024-01-01T10:00:00'
        })
        
        # Check usage
        usage_response = client.get(f'/api/recipes/{recipe_id}/usage')
        usage_info = usage_response.get_json()
        assert usage_info['in_use'] is True
        assert usage_info['usage_count'] == 1
    
    def test_grinder_usage_checking(self, client):
        """Test usage checking for grinders."""
        # Create a grinder
        grinder_response = client.post('/api/grinders', json={'name': 'Test Grinder'})
        grinder_id = grinder_response.get_json()['id']
        
        # Create a product and batch first
        product_response = client.post('/api/products', json={
            'roaster': 'Test Roaster',
            'product_name': 'Test Product'
        })
        product_id = product_response.get_json()['id']
        
        batch_response = client.post(f'/api/products/{product_id}/batches', json={
            'roast_date': '2024-01-01',
            'amount_grams': 250
        })
        batch_id = batch_response.get_json()['id']
        
        # Create a brew session using this grinder
        client.post(f'/api/batches/{batch_id}/brew_sessions', json={
            'grinder_id': grinder_id,
            'timestamp': '2024-01-01T10:00:00'
        })
        
        # Check usage
        usage_response = client.get(f'/api/grinders/{grinder_id}/usage')
        usage_info = usage_response.get_json()
        assert usage_info['in_use'] is True
        assert usage_info['usage_count'] == 1
    
    def test_filter_usage_checking(self, client):
        """Test usage checking for filters."""
        # Create a filter
        filter_response = client.post('/api/filters', json={'name': 'Test Filter'})
        filter_id = filter_response.get_json()['id']
        
        # Create a product and batch first
        product_response = client.post('/api/products', json={
            'roaster': 'Test Roaster',
            'product_name': 'Test Product'
        })
        product_id = product_response.get_json()['id']
        
        batch_response = client.post(f'/api/products/{product_id}/batches', json={
            'roast_date': '2024-01-01',
            'amount_grams': 250
        })
        batch_id = batch_response.get_json()['id']
        
        # Create a brew session using this filter
        client.post(f'/api/batches/{batch_id}/brew_sessions', json={
            'filter_id': filter_id,
            'timestamp': '2024-01-01T10:00:00'
        })
        
        # Check usage
        usage_response = client.get(f'/api/filters/{filter_id}/usage')
        usage_info = usage_response.get_json()
        assert usage_info['in_use'] is True
        assert usage_info['usage_count'] == 1
    
    def test_usage_checking_nonexistent_item(self, client):
        """Test usage checking for non-existent items returns 404."""
        response = client.get('/api/roasters/99999/usage')
        assert response.status_code == 404


class TestUpdateReferences:
    """Test update references functionality."""
    
    def test_roaster_update_references_remove(self, client):
        """Test removing roaster references from products."""
        # Create two roasters
        roaster1_response = client.post('/api/roasters', json={'name': 'Roaster 1'})
        roaster1_id = roaster1_response.get_json()['id']
        
        # Create products using the roaster
        product1_response = client.post('/api/products', json={
            'roaster': 'Roaster 1',
            'product_name': 'Product 1'
        })
        product2_response = client.post('/api/products', json={
            'roaster': 'Roaster 1',
            'product_name': 'Product 2'
        })
        
        # Remove references
        update_response = client.post(f'/api/roasters/{roaster1_id}/update_references', json={
            'action': 'remove'
        })
        assert update_response.status_code == 200
        
        update_result = update_response.get_json()
        assert update_result['updated_count'] == 2
        
        # Verify products have empty roaster
        product1 = client.get(f'/api/products/{product1_response.get_json()["id"]}').get_json()
        product2 = client.get(f'/api/products/{product2_response.get_json()["id"]}').get_json()
        assert product1['roaster'] is None
        assert product2['roaster'] is None
    
    def test_roaster_update_references_replace(self, client):
        """Test replacing roaster references in products."""
        # Create two roasters
        roaster1_response = client.post('/api/roasters', json={'name': 'Roaster 1'})
        roaster1_id = roaster1_response.get_json()['id']
        
        roaster2_response = client.post('/api/roasters', json={'name': 'Roaster 2'})
        roaster2_id = roaster2_response.get_json()['id']
        
        # Create products using the first roaster
        product1_response = client.post('/api/products', json={
            'roaster': 'Roaster 1',
            'product_name': 'Product 1'
        })
        
        # Replace references
        update_response = client.post(f'/api/roasters/{roaster1_id}/update_references', json={
            'action': 'replace',
            'replacement_id': roaster2_id
        })
        assert update_response.status_code == 200
        
        update_result = update_response.get_json()
        assert update_result['updated_count'] == 1
        
        # Verify product now uses the replacement roaster
        product1 = client.get(f'/api/products/{product1_response.get_json()["id"]}').get_json()
        assert product1['roaster']['name'] == 'Roaster 2'
    
    def test_bean_type_update_references_remove(self, client):
        """Test removing bean type references from products."""
        # Create a bean type
        bean_type_response = client.post('/api/bean_types', json={'name': 'Test Bean'})
        bean_type_id = bean_type_response.get_json()['id']
        
        # Create products using the bean type
        product1_response = client.post('/api/products', json={
            'roaster': 'Test',
            'bean_type': ['Test Bean', 'Other Bean'],
            'product_name': 'Product 1'
        })
        product2_response = client.post('/api/products', json={
            'roaster': 'Test',
            'bean_type': 'Test Bean',  # Single value
            'product_name': 'Product 2'
        })
        
        # Remove references
        update_response = client.post(f'/api/bean_types/{bean_type_id}/update_references', json={
            'action': 'remove'
        })
        assert update_response.status_code == 200
        
        update_result = update_response.get_json()
        assert update_result['updated_count'] == 2
        
        # Verify bean type was removed
        product1 = client.get(f'/api/products/{product1_response.get_json()["id"]}').get_json()
        product2 = client.get(f'/api/products/{product2_response.get_json()["id"]}').get_json()
        
        # Product 1 should have 'Other Bean' remaining
        bean_type_names_1 = [bt['name'] for bt in product1['bean_type']]
        assert 'Test Bean' not in bean_type_names_1
        assert 'Other Bean' in bean_type_names_1
        
        # Product 2 should have empty array
        assert product2['bean_type'] == []
    
    def test_bean_type_update_references_replace(self, client):
        """Test replacing bean type references in products."""
        # Create two bean types
        bean_type1_response = client.post('/api/bean_types', json={'name': 'Bean 1'})
        bean_type1_id = bean_type1_response.get_json()['id']
        
        bean_type2_response = client.post('/api/bean_types', json={'name': 'Bean 2'})
        bean_type2_id = bean_type2_response.get_json()['id']
        
        # Create product using the first bean type
        product_response = client.post('/api/products', json={
            'roaster': 'Test',
            'bean_type': ['Bean 1', 'Other Bean'],
            'product_name': 'Product 1'
        })
        
        # Replace references
        update_response = client.post(f'/api/bean_types/{bean_type1_id}/update_references', json={
            'action': 'replace',
            'replacement_id': bean_type2_id
        })
        assert update_response.status_code == 200
        
        # Verify bean type was replaced
        product = client.get(f'/api/products/{product_response.get_json()["id"]}').get_json()
        bean_type_names = [bt['name'] for bt in product['bean_type']]
        assert 'Bean 1' not in bean_type_names
        assert 'Bean 2' in bean_type_names
        assert 'Other Bean' in bean_type_names  # Other bean types preserved
    
    def test_update_references_nonexistent_item(self, client):
        """Test update references for non-existent items returns 404."""
        response = client.post('/api/roasters/99999/update_references', json={
            'action': 'remove'
        })
        assert response.status_code == 404
    
    def test_update_references_invalid_replacement_id(self, client):
        """Test update references with invalid replacement ID."""
        # Create a roaster
        roaster_response = client.post('/api/roasters', json={'name': 'Test Roaster'})
        roaster_id = roaster_response.get_json()['id']
        
        # Try to replace with non-existent roaster
        response = client.post(f'/api/roasters/{roaster_id}/update_references', json={
            'action': 'replace',
            'replacement_id': 99999
        })
        # Should still succeed but with 0 updates since replacement doesn't exist
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['updated_count'] == 0