"""
Test brew session integration with new lookup system.
"""
import pytest


class TestBrewSessionLookups:
    """Test brew session endpoints with lookup integration."""
    
    def test_brew_session_with_all_lookups(self, client):
        """Test creating a brew session with all lookup types."""
        # Create all required lookups
        brew_method_response = client.post('/api/brew_methods', json={'name': 'V60'})
        brew_method_id = brew_method_response.get_json()['id']
        
        recipe_response = client.post('/api/recipes', json={'name': 'Standard Recipe'})
        recipe_id = recipe_response.get_json()['id']
        
        grinder_response = client.post('/api/grinders', json={'name': 'Test Grinder'})
        grinder_id = grinder_response.get_json()['id']
        
        filter_response = client.post('/api/filters', json={'name': 'Paper Filter'})
        filter_id = filter_response.get_json()['id']
        
        kettle_response = client.post('/api/kettles', json={'name': 'Test Kettle'})
        kettle_id = kettle_response.get_json()['id']
        
        scale_response = client.post('/api/scales', json={'name': 'Test Scale'})
        scale_id = scale_response.get_json()['id']
        
        # Create a product and batch
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
        
        # Create brew session with all lookups
        session_data = {
            'brew_method_id': brew_method_id,
            'recipe_id': recipe_id,
            'grinder_id': grinder_id,
            'filter_id': filter_id,
            'kettle_id': kettle_id,
            'scale_id': scale_id,
            'timestamp': '2024-01-01T10:00:00',
            'amount_coffee_grams': 20.0,
            'amount_water_grams': 300.0,
            'notes': 'Test brew with all lookups'
        }
        
        response = client.post(f'/api/batches/{batch_id}/brew_sessions', json=session_data)
        assert response.status_code == 201
        
        session = response.get_json()
        assert session['brew_method_id'] == brew_method_id
        assert session['recipe_id'] == recipe_id
        assert session['grinder_id'] == grinder_id
        assert session['filter_id'] == filter_id
        assert session['kettle_id'] == kettle_id
        assert session['scale_id'] == scale_id
    
    def test_get_all_brew_sessions_enriched(self, client):
        """Test that get all brew sessions returns enriched data with lookup names."""
        # Create lookups
        brew_method_response = client.post('/api/brew_methods', json={'name': 'Chemex'})
        brew_method_id = brew_method_response.get_json()['id']
        
        recipe_response = client.post('/api/recipes', json={'name': 'Slow Pour'})
        recipe_id = recipe_response.get_json()['id']
        
        grinder_response = client.post('/api/grinders', json={'name': 'Baratza'})
        grinder_id = grinder_response.get_json()['id']
        
        # Create a product and batch
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
        
        # Create brew session
        session_data = {
            'brew_method_id': brew_method_id,
            'recipe_id': recipe_id,
            'grinder_id': grinder_id,
            'timestamp': '2024-01-01T10:00:00'
        }
        
        session_response = client.post(f'/api/batches/{batch_id}/brew_sessions', json=session_data)
        session_id = session_response.get_json()['id']
        
        # Get all brew sessions
        response = client.get('/api/brew_sessions')
        assert response.status_code == 200
        
        sessions = response.get_json()
        created_session = next(s for s in sessions if s['id'] == session_id)
        
        # Verify enriched fields
        assert created_session['brew_method']['name'] == 'Chemex'
        assert created_session['recipe']['name'] == 'Slow Pour'
        assert created_session['grinder']['name'] == 'Baratza'
        
        # Verify ID fields are still there
        assert created_session['brew_method_id'] == brew_method_id
        assert created_session['recipe_id'] == recipe_id
        assert created_session['grinder_id'] == grinder_id
    
    def test_brew_session_with_null_lookups(self, client):
        """Test brew session creation with null lookup values."""
        # Create a product and batch
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
        
        # Create brew session with null lookups
        session_data = {
            'timestamp': '2024-01-01T10:00:00',
            'brew_method_id': None,
            'recipe_id': None,
            'grinder_id': None,
            'filter_id': None,
            'kettle_id': None,
            'scale_id': None
        }
        
        response = client.post(f'/api/batches/{batch_id}/brew_sessions', json=session_data)
        assert response.status_code == 201
        
        session = response.get_json()
        assert session['brew_method_id'] is None
        assert session['recipe_id'] is None
        assert session['grinder_id'] is None
        assert session['filter_id'] is None
        assert session['kettle_id'] is None
        assert session['scale_id'] is None
    
    def test_brew_session_with_nonexistent_lookups(self, client):
        """Test brew session creation with non-existent lookup IDs."""
        # Create a product and batch
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
        
        # Try to create brew session with non-existent lookup IDs
        session_data = {
            'timestamp': '2024-01-01T10:00:00',
            'brew_method_id': 99999,  # Non-existent
            'recipe_id': 99999       # Non-existent
        }
        
        # This should still work - the system doesn't validate lookup IDs exist
        # The enrichment will just show None for the names
        response = client.post(f'/api/batches/{batch_id}/brew_sessions', json=session_data)
        assert response.status_code == 201
        
        # Get the session back enriched
        sessions_response = client.get('/api/brew_sessions')
        sessions = sessions_response.get_json()
        created_session = sessions[-1]  # Most recent
        
        # Enriched names should be None for non-existent IDs
        assert created_session['brew_method'] is None
        assert created_session['recipe'] is None
    
    def test_brew_session_lookup_consistency(self, client):
        """Test that lookup IDs and names stay consistent."""
        # Create a brew method
        brew_method_response = client.post('/api/brew_methods', json={'name': 'Original Name'})
        brew_method_id = brew_method_response.get_json()['id']
        
        # Create a product and batch
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
        
        # Create brew session
        session_data = {
            'brew_method_id': brew_method_id,
            'timestamp': '2024-01-01T10:00:00'
        }
        
        session_response = client.post(f'/api/batches/{batch_id}/brew_sessions', json=session_data)
        session_id = session_response.get_json()['id']
        
        # Update the brew method name
        client.put(f'/api/brew_methods/{brew_method_id}', json={'name': 'Updated Name'})
        
        # Get the brew session again
        sessions_response = client.get('/api/brew_sessions')
        sessions = sessions_response.get_json()
        updated_session = next(s for s in sessions if s['id'] == session_id)
        
        # The enriched name should reflect the updated name
        assert updated_session['brew_method']['name'] == 'Updated Name'
        assert updated_session['brew_method_id'] == brew_method_id