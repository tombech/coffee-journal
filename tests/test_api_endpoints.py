"""
Test API endpoints with the repository pattern.
"""
import pytest
from datetime import date, datetime


class TestProductEndpoints:
    """Test product API endpoints."""
    
    def test_create_product(self, client):
        """Test creating a product via API."""
        product_data = {
            'roaster_name': 'Blue Bottle Coffee',
            'bean_type_name': ['Arabica'],
            'product_name': 'Test Blend',
            'roast_type': 5,
            'description': 'A test coffee blend'
        }
        
        response = client.post('/api/products', json=product_data)
        assert response.status_code == 201
        
        product = response.get_json()
        assert product['roaster']['name'] == 'Blue Bottle Coffee'
        assert len(product['bean_type']) == 1
        assert product['bean_type'][0]['name'] == 'Arabica'
        assert product['product_name'] == 'Test Blend'
        assert product['roast_type'] == 5
        assert product['id'] is not None
    
    def test_get_products(self, client):
        """Test getting all products."""
        # Create some products first
        client.post('/api/products', json={
            'roaster_name': 'Roaster 1',
            'product_name': 'Product 1'
        })
        client.post('/api/products', json={
            'roaster_name': 'Roaster 2',
            'product_name': 'Product 2'
        })
        
        response = client.get('/api/products')
        assert response.status_code == 200
        
        products = response.get_json()
        assert len(products) >= 2
    
    def test_get_product_by_id(self, client):
        """Test getting a specific product."""
        # Create a product
        create_response = client.post('/api/products', json={
            'roaster_name': 'Test Roaster',
            'product_name': 'Test Product'
        })
        product_id = create_response.get_json()['id']
        
        # Get the product
        response = client.get(f'/api/products/{product_id}')
        assert response.status_code == 200
        
        product = response.get_json()
        assert product['id'] == product_id
        assert product['roaster']['name'] == 'Test Roaster'
        assert product['product_name'] == 'Test Product'
    
    def test_update_product(self, client):
        """Test updating a product."""
        # Create initial product
        create_response = client.post('/api/products', json={
            'roaster_name': 'Initial Roaster',
            'product_name': 'Initial Name',
            'roast_type': 5
        })
        product_id = create_response.get_json()['id']
        
        # Update the product
        update_data = {
            'roaster_name': 'Initial Roaster',  # Required field
            'product_name': 'Updated Name',
            'roast_type': 7,
            'description': 'Updated description'
        }
        
        response = client.put(f'/api/products/{product_id}', json=update_data)
        assert response.status_code == 200
        
        updated_product = response.get_json()
        assert updated_product['product_name'] == 'Updated Name'
        assert updated_product['roast_type'] == 7
        assert updated_product['description'] == 'Updated description'
        
        # Verify persistence
        get_response = client.get(f'/api/products/{product_id}')
        fetched_product = get_response.get_json()
        assert fetched_product['product_name'] == 'Updated Name'
        assert fetched_product['roast_type'] == 7
    
    def test_delete_product(self, client):
        """Test deleting a product."""
        # Create a product
        create_response = client.post('/api/products', json={
            'roaster_name': 'Test Roaster'
        })
        product_id = create_response.get_json()['id']
        
        # Delete the product
        response = client.delete(f'/api/products/{product_id}')
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(f'/api/products/{product_id}')
        assert get_response.status_code == 404
    
    def test_product_filters(self, client):
        """Test filtering products."""
        # Create test data
        client.post('/api/products', json={
            'roaster_name': 'Roaster A',
            'bean_type_name': ['Arabica']
        })
        client.post('/api/products', json={
            'roaster_name': 'Roaster B',
            'bean_type_name': ['Arabica']
        })
        client.post('/api/products', json={
            'roaster_name': 'Roaster A',
            'bean_type_name': ['Robusta']
        })
        
        # Test roaster filter
        response = client.get('/api/products?roaster=Roaster A')
        products = response.get_json()
        assert len(products) == 2
        assert all(p['roaster']['name'] == 'Roaster A' for p in products)
        
        # Test bean type filter
        response = client.get('/api/products?bean_type=Arabica')
        products = response.get_json()
        assert len(products) == 2
        # Bean type is an array of objects
        assert all(any(bt['name'] == 'Arabica' for bt in p.get('bean_type', [])) for p in products)


class TestBatchEndpoints:
    """Test batch API endpoints."""
    
    def test_create_batch(self, client):
        """Test creating a batch."""
        # First create a product
        product_response = client.post('/api/products', json={
            'roaster_name': 'Test Roaster'
        })
        product_id = product_response.get_json()['id']
        
        # Create a batch using RESTful endpoint
        batch_data = {
            'roast_date': '2025-01-01',
            'amount_grams': 250.0,
            'price': 15.99,
            'seller': 'Local Coffee Shop'
        }
        
        response = client.post(f'/api/products/{product_id}/batches', json=batch_data)
        assert response.status_code == 201
        
        batch = response.get_json()
        assert batch['product_id'] == product_id
        assert batch['roast_date'] == '2025-01-01'
        assert batch['amount_grams'] == 250.0
        assert batch['price'] == 15.99
        assert batch['price_per_cup'] is not None
    
    def test_get_batches_by_product(self, client):
        """Test getting batches for a specific product."""
        # Create product
        product_response = client.post('/api/products', json={
            'roaster_name': 'Test Roaster'
        })
        product_id = product_response.get_json()['id']
        
        # Create batches using RESTful endpoints
        client.post(f'/api/products/{product_id}/batches', json={
            'roast_date': '2025-01-01'
        })
        client.post(f'/api/products/{product_id}/batches', json={
            'roast_date': '2025-01-02'
        })
        
        # Get batches for product
        response = client.get(f'/api/products/{product_id}/batches')
        assert response.status_code == 200
        
        batches = response.get_json()
        assert len(batches) == 2
        assert all(b['product_id'] == product_id for b in batches)
    
    def test_update_batch(self, client):
        """Test updating a batch."""
        # Create product and batch
        product_response = client.post('/api/products', json={
            'roaster_name': 'Test Roaster'
        })
        product_id = product_response.get_json()['id']
        
        batch_response = client.post(f'/api/products/{product_id}/batches', json={
            'roast_date': '2025-01-01',
            'price': 15.99
        })
        batch_id = batch_response.get_json()['id']
        
        # Update the batch
        update_data = {
            'product_id': product_id,
            'roast_date': '2025-01-01',
            'price': 16.99,
            'amount_grams': 300.0,
            'seller': 'Updated Seller'
        }
        
        response = client.put(f'/api/batches/{batch_id}', json=update_data)
        assert response.status_code == 200
        
        updated_batch = response.get_json()
        assert updated_batch['price'] == 16.99
        assert updated_batch['amount_grams'] == 300.0
        assert updated_batch['seller'] == 'Updated Seller'
    
    def test_cascade_delete_batches(self, client):
        """Test that deleting a product deletes its batches."""
        # Create product
        product_response = client.post('/api/products', json={
            'roaster_name': 'Test Roaster'
        })
        product_id = product_response.get_json()['id']
        
        # Create batch using RESTful endpoint
        batch_response = client.post(f'/api/products/{product_id}/batches', json={
            'roast_date': '2025-01-01'
        })
        batch_id = batch_response.get_json()['id']
        
        # Delete product
        client.delete(f'/api/products/{product_id}')
        
        # Verify batch is also deleted
        get_response = client.get(f'/api/batches/{batch_id}')
        assert get_response.status_code == 404


class TestBrewSessionEndpoints:
    """Test brew session API endpoints."""
    
    def test_create_brew_session(self, client):
        """Test creating a brew session."""
        # Create product and batch
        product_response = client.post('/api/products', json={
            'roaster_name': 'Test Roaster'
        })
        product_id = product_response.get_json()['id']
        
        batch_response = client.post(f'/api/products/{product_id}/batches', json={
            'roast_date': '2025-01-01'
        })
        batch_id = batch_response.get_json()['id']
        
        # Create brew session using RESTful endpoint
        session_data = {
            'brew_method': 'V60',
            'amount_coffee_grams': 18.0,
            'amount_water_grams': 300.0,
            'brew_temperature_c': 93.0,
            'sweetness': 8,
            'notes': 'Great cup!'
        }
        
        response = client.post(f'/api/batches/{batch_id}/brew_sessions', json=session_data)
        assert response.status_code == 201
        
        session = response.get_json()
        assert session['product_batch_id'] == batch_id
        assert session['product_id'] == product_id
        assert session['brew_method']['name'] == 'V60'
        assert session['amount_coffee_grams'] == 18.0
        assert session['brew_ratio'] == '1:16.7'
    
    def test_get_all_brew_sessions(self, client):
        """Test getting all brew sessions."""
        # Create product and batch
        product_response = client.post('/api/products', json={
            'roaster_name': 'Test Roaster',
            'bean_type_name': ['Arabica']
        })
        product_id = product_response.get_json()['id']
        
        batch_response = client.post(f'/api/products/{product_id}/batches', json={
            'roast_date': '2025-01-01'
        })
        batch_id = batch_response.get_json()['id']
        
        # Create sessions using RESTful endpoint
        client.post(f'/api/batches/{batch_id}/brew_sessions', json={
            'brew_method': 'V60'
        })
        
        response = client.get('/api/brew_sessions')
        assert response.status_code == 200
        
        sessions = response.get_json()
        assert len(sessions) >= 1
    
    def test_update_brew_session(self, client):
        """Test updating a brew session."""
        # Create product and batch
        product_response = client.post('/api/products', json={
            'roaster_name': 'Test Roaster'
        })
        product_id = product_response.get_json()['id']
        
        batch_response = client.post(f'/api/products/{product_id}/batches', json={
            'roast_date': '2025-01-01'
        })
        batch_id = batch_response.get_json()['id']
        
        # Create session using RESTful endpoint
        session_response = client.post(f'/api/batches/{batch_id}/brew_sessions', json={
            'sweetness': 7
        })
        session_id = session_response.get_json()['id']
        
        # Update session
        update_data = {
            'product_batch_id': batch_id,
            'product_id': product_id,
            'sweetness': 9,
            'notes': 'Updated notes',
            'brew_method': 'Chemex'
        }
        
        response = client.put(f'/api/brew_sessions/{session_id}', json=update_data)
        assert response.status_code == 200
        
        updated_session = response.get_json()
        assert updated_session['sweetness'] == 9
        assert updated_session['notes'] == 'Updated notes'
        assert updated_session['brew_method']['name'] == 'Chemex'
    
    def test_brew_session_with_method_and_recipe(self, client):
        """Test that brew method and recipe are properly stored and returned."""
        # Create product and batch
        product_response = client.post('/api/products', json={
            'roaster_name': 'Test Roaster',
            'bean_type_name': ['Arabica']
        })
        product_id = product_response.get_json()['id']
        
        batch_response = client.post(f'/api/products/{product_id}/batches', json={
            'roast_date': '2025-01-01',
            'amount_grams': 340
        })
        batch_id = batch_response.get_json()['id']
        
        # Create brew session with method and recipe
        session_data = {
            'brew_method': 'Aeropress',
            'recipe': 'Inverted Method - 2:30 total',
            'amount_coffee_grams': 15.0,
            'amount_water_grams': 225.0,
            'brew_temperature_c': 85.0,
            'brew_time_seconds': 150,
            'notes': 'Testing method and recipe storage'
        }
        
        # Create the session
        create_response = client.post(f'/api/batches/{batch_id}/brew_sessions', json=session_data)
        assert create_response.status_code == 201
        
        created_session = create_response.get_json()
        session_id = created_session['id']
        
        # Verify the response includes method and recipe
        assert created_session['brew_method']['name'] == 'Aeropress'
        assert created_session['recipe']['name'] == 'Inverted Method - 2:30 total'
        
        # Get the session directly
        get_response = client.get(f'/api/brew_sessions/{session_id}')
        assert get_response.status_code == 200
        
        fetched_session = get_response.get_json()
        assert fetched_session['brew_method']['name'] == 'Aeropress'
        assert fetched_session['recipe']['name'] == 'Inverted Method - 2:30 total'
        
        # Get all sessions and verify our session is included with method and recipe
        all_sessions_response = client.get('/api/brew_sessions')
        assert all_sessions_response.status_code == 200
        
        all_sessions = all_sessions_response.get_json()
        our_session = next((s for s in all_sessions if s['id'] == session_id), None)
        assert our_session is not None
        assert our_session['brew_method']['name'] == 'Aeropress'
        assert our_session['recipe']['name'] == 'Inverted Method - 2:30 total'
        
        # Get sessions by batch and verify method and recipe are included
        batch_sessions_response = client.get(f'/api/batches/{batch_id}/brew_sessions')
        assert batch_sessions_response.status_code == 200
        
        batch_sessions = batch_sessions_response.get_json()
        batch_session = next((s for s in batch_sessions if s['id'] == session_id), None)
        assert batch_session is not None
        assert batch_session['brew_method']['name'] == 'Aeropress'
        assert batch_session['recipe']['name'] == 'Inverted Method - 2:30 total'


class TestLookupEndpoints:
    """Test lookup table API endpoints."""
    
    def test_get_roasters(self, client):
        """Test getting roasters."""
        # Create products with roasters
        client.post('/api/products', json={'roaster_name': 'Roaster A'})
        client.post('/api/products', json={'roaster_name': 'Roaster B'})
        
        response = client.get('/api/roasters')
        assert response.status_code == 200
        
        roasters = response.get_json()
        roaster_names = [r['name'] for r in roasters]
        assert 'Roaster A' in roaster_names
        assert 'Roaster B' in roaster_names
    
    def test_get_bean_types(self, client):
        """Test getting bean types."""
        # Create products with bean types
        client.post('/api/products', json={
            'roaster_name': 'Test',
            'bean_type_name': ['Arabica']
        })
        client.post('/api/products', json={
            'roaster_name': 'Test',
            'bean_type_name': ['Robusta']
        })
        
        response = client.get('/api/bean_types')
        assert response.status_code == 200
        
        bean_types = response.get_json()
        bean_type_names = [bt['name'] for bt in bean_types]
        assert 'Arabica' in bean_type_names
        assert 'Robusta' in bean_type_names
    
    def test_lookup_deduplication(self, client):
        """Test that lookups are properly deduplicated."""
        # Create multiple products with same roaster
        client.post('/api/products', json={'roaster_name': 'Duplicate Roaster'})
        client.post('/api/products', json={'roaster_name': 'Duplicate Roaster'})
        client.post('/api/products', json={'roaster_name': 'Duplicate Roaster'})
        
        response = client.get('/api/roasters')
        roasters = response.get_json()
        
        # Count how many times "Duplicate Roaster" appears
        duplicate_count = sum(1 for r in roasters if r['name'] == 'Duplicate Roaster')
        assert duplicate_count == 1


class TestErrorHandling:
    """Test API error handling."""
    
    def test_product_not_found(self, client):
        """Test handling of non-existent product."""
        response = client.get('/api/products/99999')
        assert response.status_code == 404
        assert 'error' in response.get_json()
    
    def test_missing_required_field(self, client):
        """Test creating product without required roaster."""
        response = client.post('/api/products', json={
            'product_name': 'Missing Roaster'
        })
        assert response.status_code == 400
        assert 'error' in response.get_json()
    
    def test_invalid_product_for_batch(self, client):
        """Test creating batch with invalid product ID."""
        response = client.post('/api/products/99999/batches', json={
            'roast_date': '2025-01-01'
        })
        assert response.status_code == 404
        assert 'error' in response.get_json()