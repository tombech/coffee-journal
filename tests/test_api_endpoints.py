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

    def test_create_batch_with_empty_roast_date(self, client):
        """Test creating a batch with empty roast_date (should use today's date as default)."""
        # First create a product
        product_response = client.post('/api/products', json={
            'roaster_name': 'Test Roaster'
        })
        product_id = product_response.get_json()['id']
        
        # Create a batch with empty roast_date (this should trigger the datetime import bug)
        batch_data = {
            'roast_date': '',  # Empty string - this triggers the datetime.now() code path
            'amount_grams': 250.0,
            'price': 15.99
        }
        
        response = client.post(f'/api/products/{product_id}/batches', json=batch_data)
        # This should succeed once we fix the datetime import
        assert response.status_code == 201
        
        batch = response.get_json()
        assert batch['product_id'] == product_id
        # Should have today's date as default
        import datetime
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        assert batch['roast_date'] == today

    def test_create_batch_with_missing_roast_date(self, client):
        """Test creating a batch with missing roast_date (should use today's date as default)."""
        # First create a product
        product_response = client.post('/api/products', json={
            'roaster_name': 'Test Roaster'
        })
        product_id = product_response.get_json()['id']
        
        # Create a batch without roast_date field (this should also trigger the datetime import bug)
        batch_data = {
            'amount_grams': 250.0,
            'price': 15.99
        }
        
        response = client.post(f'/api/products/{product_id}/batches', json=batch_data)
        # This should succeed once we fix the datetime import
        assert response.status_code == 201
        
        batch = response.get_json()
        assert batch['product_id'] == product_id
        # Should have today's date as default
        import datetime
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        assert batch['roast_date'] == today


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
        
        result = response.get_json()
        sessions = result['data']  # Handle pagination response
        assert len(sessions) >= 1
    
    def test_brew_session_decaf_method_enrichment(self, client):
        """Test that brew sessions include decaf_method enrichment in product_details."""
        # First create a decaf method
        decaf_method_response = client.post('/api/decaf_methods', json={
            'name': 'Test Swiss Water Process',
            'short_form': 'TSWP'
        })
        decaf_method_data = decaf_method_response.get_json()
        
        # Create product with decaf method
        product_response = client.post('/api/products', json={
            'roaster_name': 'Test Roaster',
            'decaf': True,
            'decaf_method_id': decaf_method_data['id']
        })
        product_id = product_response.get_json()['id']
        assert product_response.get_json()['decaf_method']['id'] == decaf_method_data['id']
        
        # Create batch and session
        batch_response = client.post(f'/api/products/{product_id}/batches', json={'roast_date': '2025-01-01'})
        batch_id = batch_response.get_json()['id']
        
        session_response = client.post(f'/api/batches/{batch_id}/brew_sessions', json={'brew_method': 'V60'})
        assert session_response.status_code == 201
        
        # Get all brew sessions and verify decaf_method enrichment
        response = client.get('/api/brew_sessions')
        assert response.status_code == 200
        
        result = response.get_json()
        sessions = result['data']
        
        # Find our session and verify decaf_method is enriched
        found_session = None
        for session in sessions:
            if session['product_id'] == product_id:
                found_session = session
                break
        
        assert found_session is not None, "Could not find the created session"
        assert 'product_details' in found_session
        assert 'decaf_method' in found_session['product_details']
        
        decaf_method = found_session['product_details']['decaf_method']
        assert decaf_method is not None
        assert decaf_method['id'] == decaf_method_data['id']
        assert decaf_method['name'] == decaf_method_data['name']
    
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
        
        all_sessions_result = all_sessions_response.get_json()
        all_sessions = all_sessions_result['data']  # Handle pagination response
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


class TestBrewSessionFilterOptionsEndpoint:
    """Test the new filter options endpoint for brew sessions."""
    
    def test_filter_options_endpoint_exists(self, client):
        """Test that the filter options endpoint exists and returns 200."""
        response = client.get('/api/brew_sessions/filter_options')
        assert response.status_code == 200
        
        options = response.get_json()
        assert isinstance(options, dict)
    
    def test_filter_options_structure(self, client):
        """Test that filter options have the correct structure."""
        response = client.get('/api/brew_sessions/filter_options')
        assert response.status_code == 200
        
        options = response.get_json()
        
        # Check all expected filter categories are present
        expected_categories = [
            'roasters', 'bean_types', 'countries', 'brew_methods', 
            'recipes', 'grinders', 'filters', 'kettles', 'scales', 'decaf_options'
        ]
        
        for category in expected_categories:
            assert category in options, f"Missing filter category: {category}"
            assert isinstance(options[category], list), f"Category {category} should be a list"
    
    def test_filter_options_id_name_pairs(self, client):
        """Test that filter options return proper ID-name pairs."""
        # Create some test data first
        product_response = client.post('/api/products', json={
            'roaster_name': 'Test Filter Roaster',
            'bean_type_name': ['Test Bean Type'],
            'country_name': 'Test Country'
        })
        product_id = product_response.get_json()['id']
        
        batch_response = client.post(f'/api/products/{product_id}/batches', json={
            'roast_date': '2025-01-01'
        })
        batch_id = batch_response.get_json()['id']
        
        # Create brew session
        client.post(f'/api/batches/{batch_id}/brew_sessions', json={
            'brew_method': 'V60',
            'grinder': 'Test Grinder'
        })
        
        response = client.get('/api/brew_sessions/filter_options')
        assert response.status_code == 200
        
        options = response.get_json()
        
        # Check that ID-name pairs are returned for main categories
        for category in ['roasters', 'bean_types', 'countries', 'brew_methods', 'grinders']:
            if options[category]:  # Only check if category has items
                item = options[category][0]
                assert isinstance(item, dict), f"Items in {category} should be objects"
                assert 'id' in item, f"Items in {category} should have 'id' field"
                assert 'name' in item, f"Items in {category} should have 'name' field"
                assert isinstance(item['id'], int), f"ID in {category} should be integer"
                assert isinstance(item['name'], str), f"Name in {category} should be string"
    
    def test_filter_options_no_regions(self, client):
        """Test that region filter is not included in filter options."""
        response = client.get('/api/brew_sessions/filter_options')
        assert response.status_code == 200
        
        options = response.get_json()
        assert 'regions' not in options, "Region filter should be removed"
    
    def test_filter_options_decaf_format(self, client):
        """Test that decaf options have the correct static format."""
        response = client.get('/api/brew_sessions/filter_options')
        assert response.status_code == 200
        
        options = response.get_json()
        decaf_options = options['decaf_options']
        
        assert len(decaf_options) == 2, "Should have exactly 2 decaf options"
        
        # Check the format of decaf options
        expected_options = [
            {'id': 'true', 'name': 'Yes'},
            {'id': 'false', 'name': 'No'}
        ]
        
        assert decaf_options == expected_options, "Decaf options should match expected format"
    
    def test_filter_options_consistency_with_filtering(self, client):
        """Test that filter options remain consistent regardless of current filtering."""
        # Create test data
        product_response = client.post('/api/products', json={
            'roaster_name': 'Consistent Test Roaster',
            'bean_type_name': ['Arabica']
        })
        product_id = product_response.get_json()['id']
        
        batch_response = client.post(f'/api/products/{product_id}/batches', json={
            'roast_date': '2025-01-01'
        })
        batch_id = batch_response.get_json()['id']
        
        client.post(f'/api/batches/{batch_id}/brew_sessions', json={
            'brew_method': 'V60'
        })
        
        # Get filter options before any filtering
        response_before = client.get('/api/brew_sessions/filter_options')
        options_before = response_before.get_json()
        
        # Apply some filtering to brew sessions
        filtered_response = client.get('/api/brew_sessions?roaster=1&page_size=1')
        assert filtered_response.status_code == 200  # Ensure filtering works
        
        # Get filter options after filtering
        response_after = client.get('/api/brew_sessions/filter_options')
        options_after = response_after.get_json()
        
        # Options should be identical (bug fix verification)
        assert options_before == options_after, "Filter options should remain consistent"


class TestIDBasedFilteringAPI:
    """Test ID-based filtering functionality in brew sessions API."""
    
    def test_filter_by_roaster_id(self, client):
        """Test filtering brew sessions by roaster ID."""
        # Create products with different roasters
        product1_response = client.post('/api/products', json={
            'roaster_name': 'Filter Roaster 1',
            'product_name': 'Product 1'
        })
        product1_id = product1_response.get_json()['id']
        roaster1_id = product1_response.get_json()['roaster']['id']
        
        product2_response = client.post('/api/products', json={
            'roaster_name': 'Filter Roaster 2',
            'product_name': 'Product 2'
        })
        product2_id = product2_response.get_json()['id']
        
        # Create batches and sessions
        batch1_response = client.post(f'/api/products/{product1_id}/batches', json={'roast_date': '2025-01-01'})
        batch1_id = batch1_response.get_json()['id']
        
        batch2_response = client.post(f'/api/products/{product2_id}/batches', json={'roast_date': '2025-01-01'})
        batch2_id = batch2_response.get_json()['id']
        
        client.post(f'/api/batches/{batch1_id}/brew_sessions', json={'brew_method': 'V60'})
        client.post(f'/api/batches/{batch2_id}/brew_sessions', json={'brew_method': 'Chemex'})
        
        # Filter by roaster ID
        response = client.get(f'/api/brew_sessions?roaster={roaster1_id}')
        assert response.status_code == 200
        
        result = response.get_json()
        sessions = result['data']
        
        # Should only return sessions from roaster 1
        assert len(sessions) >= 1
        for session in sessions:
            assert session['product_details']['roaster']['id'] == roaster1_id
    
    def test_filter_by_country_id(self, client):
        """Test filtering brew sessions by country ID."""
        # Create product with specific country
        product_response = client.post('/api/products', json={
            'roaster_name': 'Test Roaster',
            'country_name': 'Ethiopia'
        })
        product_id = product_response.get_json()['id']
        country_id = product_response.get_json()['country']['id']
        
        # Create batch and session
        batch_response = client.post(f'/api/products/{product_id}/batches', json={'roast_date': '2025-01-01'})
        batch_id = batch_response.get_json()['id']
        
        client.post(f'/api/batches/{batch_id}/brew_sessions', json={'brew_method': 'V60'})
        
        # Filter by country ID
        response = client.get(f'/api/brew_sessions?country={country_id}')
        assert response.status_code == 200
        
        result = response.get_json()
        sessions = result['data']
        
        # Should return sessions from Ethiopia
        assert len(sessions) >= 1
        for session in sessions:
            assert session['product_details']['country']['id'] == country_id
    
    def test_filter_by_brew_method_id(self, client):
        """Test filtering brew sessions by brew method ID."""
        # Create product and batch
        product_response = client.post('/api/products', json={'roaster_name': 'Test Roaster'})
        product_id = product_response.get_json()['id']
        
        batch_response = client.post(f'/api/products/{product_id}/batches', json={'roast_date': '2025-01-01'})
        batch_id = batch_response.get_json()['id']
        
        # Create session with specific brew method
        session_response = client.post(f'/api/batches/{batch_id}/brew_sessions', json={'brew_method': 'Aeropress'})
        session = session_response.get_json()
        brew_method_id = session['brew_method']['id']
        
        # Filter by brew method ID
        response = client.get(f'/api/brew_sessions?brew_method={brew_method_id}')
        assert response.status_code == 200
        
        result = response.get_json()
        sessions = result['data']
        
        # Should return sessions with Aeropress method
        assert len(sessions) >= 1
        for session in sessions:
            assert session['brew_method']['id'] == brew_method_id
    
    def test_filter_by_region_id(self, client):
        """Test filtering brew sessions by region ID."""
        # Create product with specific region
        product_response = client.post('/api/products', json={
            'roaster_name': 'Test Roaster',
            'country_name': 'Ethiopia',
            'region_name': ['Yirgacheffe']
        })
        product_id = product_response.get_json()['id']
        regions = product_response.get_json()['region']
        region_id = regions[0]['id']  # Get first region ID
        
        # Create batch and session
        batch_response = client.post(f'/api/products/{product_id}/batches', json={'roast_date': '2025-01-01'})
        batch_id = batch_response.get_json()['id']
        
        client.post(f'/api/batches/{batch_id}/brew_sessions', json={'brew_method': 'V60'})
        
        # Filter by region ID
        response = client.get(f'/api/brew_sessions?region={region_id}')
        assert response.status_code == 200
        
        result = response.get_json()
        sessions = result['data']
        
        # Should return sessions from Yirgacheffe region
        assert len(sessions) >= 1
        for session in sessions:
            found = False
            for region in session['product_details']['region']:
                if region['id'] == region_id:
                    found = True
                    break
            assert found, f"Region ID {region_id} not found in session regions"
    
    def test_filter_by_decaf_method_id(self, client):
        """Test filtering brew sessions by decaf method ID."""
        # First create a decaf method
        decaf_method_response = client.post('/api/decaf_methods', json={
            'name': 'Test Swiss Water Process',
            'short_form': 'TSWP'
        })
        decaf_method_id = decaf_method_response.get_json()['id']
        
        # Create product with decaf method
        product_response = client.post('/api/products', json={
            'roaster_name': 'Test Roaster',
            'decaf': True,
            'decaf_method_id': decaf_method_id
        })
        product_id = product_response.get_json()['id']
        assert product_response.get_json()['decaf_method']['id'] == decaf_method_id
        
        # Create batch and session
        batch_response = client.post(f'/api/products/{product_id}/batches', json={'roast_date': '2025-01-01'})
        batch_id = batch_response.get_json()['id']
        
        client.post(f'/api/batches/{batch_id}/brew_sessions', json={'brew_method': 'V60'})
        
        # Filter by decaf method ID
        response = client.get(f'/api/brew_sessions?decaf_method={decaf_method_id}')
        assert response.status_code == 200
        
        result = response.get_json()
        sessions = result['data']
        
        # Should return sessions from products with Swiss Water Process
        assert len(sessions) >= 1
        for session in sessions:
            assert session['product_details']['decaf_method']['id'] == decaf_method_id