"""
Tests for specific bug fixes to ensure they don't regress.
"""
import pytest
import json
from coffeejournal import create_app
from coffeejournal.repositories.factory import RepositoryFactory


class TestBugFixes:
    """Test class for verifying bug fixes."""
    
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
    
    @pytest.fixture
    def setup_test_data(self, app):
        """Set up basic test data."""
        with app.app_context():
            # Create a basic product and batch for testing
            client = app.test_client()
            
            # Create roaster
            roaster_response = client.post('/api/roasters', json={'name': 'Test Roaster'})
            assert roaster_response.status_code == 201
            roaster = roaster_response.get_json()
            
            # Create bean type
            bean_type_response = client.post('/api/bean_types', json={'name': 'Arabica'})
            assert bean_type_response.status_code == 201
            bean_type = bean_type_response.get_json()
            
            # Create country
            country_response = client.post('/api/countries', json={'name': 'Ethiopia'})
            assert country_response.status_code == 201
            country = country_response.get_json()
            
            # Create product
            product_data = {
                'name': 'Test Coffee',
                'roaster_id': roaster['id'],
                'bean_type_ids': [bean_type['id']],
                'country_id': country['id']
            }
            product_response = client.post('/api/products', json=product_data)
            assert product_response.status_code == 201
            product = product_response.get_json()
            
            # Create batch
            batch_data = {
                'roast_date': '2024-01-01',
                'purchase_date': '2024-01-02',
                'amount_grams': 500
            }
            batch_response = client.post(f'/api/products/{product["id"]}/batches', json=batch_data)
            assert batch_response.status_code == 201
            batch = batch_response.get_json()
            
            return {
                'roaster': roaster,
                'bean_type': bean_type,
                'country': country,
                'product': product,
                'batch': batch
            }
    
    def test_duplicate_lookup_prevention(self, client, setup_test_data):
        """
        Bug Fix Test 1: Prevent duplicate lookup items with case/whitespace variations.
        
        Tests that get_or_create_by_identifier doesn't create duplicates for:
        - Different case: "Paper Filter" vs "paper filter"
        - Whitespace: "Paper Filter" vs " Paper Filter "
        - Mixed: "PAPER FILTER" vs "paper filter"
        """
        batch = setup_test_data['batch']
        
        # Create first brew session with "Paper Filter"
        brew_data_1 = {
            'filter': 'Paper Filter',
            'brew_method': 'V60',
            'grinder': 'Baratza Encore',
            'amount_coffee_grams': 25.0,
            'amount_water_grams': 400.0,
            'brew_temperature_c': 93.5
        }
        
        response1 = client.post(f'/api/batches/{batch["id"]}/brew_sessions', json=brew_data_1)
        assert response1.status_code == 201
        
        # Create second brew session with variations
        brew_data_2 = {
            'filter': 'paper filter',  # lowercase
            'brew_method': ' V60 ',    # padded
            'grinder': 'BARATZA ENCORE',  # uppercase
            'amount_coffee_grams': 26.0,
            'amount_water_grams': 420.0,
            'brew_temperature_c': 94.0
        }
        
        response2 = client.post(f'/api/batches/{batch["id"]}/brew_sessions', json=brew_data_2)
        assert response2.status_code == 201
        
        # Check that we didn't create duplicates
        filters_response = client.get('/api/filters')
        filters = filters_response.get_json()
        filter_names = [f['name'] for f in filters]
        assert len([f for f in filter_names if f.lower().strip() == 'paper filter']) == 1
        
        brew_methods_response = client.get('/api/brew_methods')
        brew_methods = brew_methods_response.get_json()
        brew_method_names = [bm['name'] for bm in brew_methods]
        assert len([bm for bm in brew_method_names if bm.lower().strip() == 'v60']) == 1
        
        grinders_response = client.get('/api/grinders')
        grinders = grinders_response.get_json()
        grinder_names = [g['name'] for g in grinders]
        assert len([g for g in grinder_names if g.lower().strip() == 'baratza encore']) == 1
    
    def test_float_temperature_acceptance(self, client, setup_test_data):
        """
        Bug Fix Test 2: Ensure brew temperature accepts float values.
        
        Tests that decimal temperatures like 93.5°C are accepted and stored correctly.
        """
        batch = setup_test_data['batch']
        
        test_temperatures = [93.5, 94.2, 87.75, 95.0, 88]
        
        for temp in test_temperatures:
            brew_data = {
                'brew_temperature_c': temp,
                'amount_coffee_grams': 25.0,
                'amount_water_grams': 400.0
            }
            
            response = client.post(f'/api/batches/{batch["id"]}/brew_sessions', json=brew_data)
            assert response.status_code == 201
            
            # Verify the temperature was stored correctly
            brew_session = response.get_json()
            assert brew_session['brew_temperature_c'] == temp
    
    def test_update_references_functionality(self, client, setup_test_data):
        """
        Bug Fix Test 3: Verify "Replace with other item and delete" functionality works.
        
        Tests the update_references endpoint for replacing references before deletion.
        """
        batch = setup_test_data['batch']
        
        # Create two filters
        filter1_response = client.post('/api/filters', json={'name': 'Paper Filter'})
        assert filter1_response.status_code == 201
        filter1 = filter1_response.get_json()
        
        filter2_response = client.post('/api/filters', json={'name': 'Metal Filter'})
        assert filter2_response.status_code == 201
        filter2 = filter2_response.get_json()
        
        # Create brew session using filter1
        brew_data = {
            'filter_id': filter1['id'],
            'amount_coffee_grams': 25.0,
            'amount_water_grams': 400.0
        }
        
        brew_response = client.post(f'/api/batches/{batch["id"]}/brew_sessions', json=brew_data)
        assert brew_response.status_code == 201
        brew_session = brew_response.get_json()
        
        # Verify filter1 is in use
        usage_response = client.get(f'/api/filters/{filter1["id"]}/usage')
        assert usage_response.status_code == 200
        usage_info = usage_response.get_json()
        assert usage_info['in_use'] is True
        assert usage_info['usage_count'] == 1
        
        # Replace filter1 references with filter2
        update_response = client.post(
            f'/api/filters/{filter1["id"]}/update_references',
            json={'action': 'replace', 'replacement_id': filter2['id']}
        )
        assert update_response.status_code == 200
        
        # Verify the brew session now references filter2
        updated_brew_response = client.get(f'/api/brew_sessions/{brew_session["id"]}')
        updated_brew = updated_brew_response.get_json()
        assert updated_brew['filter_id'] == filter2['id']
        
        # Verify filter1 is no longer in use
        usage_response = client.get(f'/api/filters/{filter1["id"]}/usage')
        assert usage_response.status_code == 200
        usage_info = usage_response.get_json()
        assert usage_info['in_use'] is False
        assert usage_info['usage_count'] == 0
        
        # Now filter1 can be safely deleted
        delete_response = client.delete(f'/api/filters/{filter1["id"]}')
        assert delete_response.status_code == 204
        
        # Verify filter1 is gone
        get_response = client.get(f'/api/filters/{filter1["id"]}')
        assert get_response.status_code == 404
    
    def test_remove_references_functionality(self, client, setup_test_data):
        """
        Test the "Remove all references and delete" functionality.
        """
        batch = setup_test_data['batch']
        
        # Create a kettle
        kettle_response = client.post('/api/kettles', json={'name': 'Test Kettle'})
        assert kettle_response.status_code == 201
        kettle = kettle_response.get_json()
        
        # Create brew session using the kettle
        brew_data = {
            'kettle_id': kettle['id'],
            'amount_coffee_grams': 25.0,
            'amount_water_grams': 400.0
        }
        
        brew_response = client.post(f'/api/batches/{batch["id"]}/brew_sessions', json=brew_data)
        assert brew_response.status_code == 201
        brew_session = brew_response.get_json()
        
        # Remove all references to the kettle
        update_response = client.post(
            f'/api/kettles/{kettle["id"]}/update_references',
            json={'action': 'remove'}
        )
        assert update_response.status_code == 200
        
        # Verify the brew session no longer references the kettle
        updated_brew_response = client.get(f'/api/brew_sessions/{brew_session["id"]}')
        updated_brew = updated_brew_response.get_json()
        assert updated_brew['kettle_id'] is None
        
        # Verify kettle is no longer in use
        usage_response = client.get(f'/api/kettles/{kettle["id"]}/usage')
        assert usage_response.status_code == 200
        usage_info = usage_response.get_json()
        assert usage_info['in_use'] is False
        
        # Now kettle can be safely deleted
        delete_response = client.delete(f'/api/kettles/{kettle["id"]}')
        assert delete_response.status_code == 204
    
    def test_brew_session_edit_validation(self, client, setup_test_data):
        """
        Bug Fix Test 4: Ensure editing brew session validates batch selection.
        
        Tests that editing a brew session requires a valid batch ID to prevent 404 errors.
        """
        batch = setup_test_data['batch']
        
        # Create a brew session
        brew_data = {
            'amount_coffee_grams': 25.0,
            'amount_water_grams': 400.0,
            'brew_temperature_c': 93.5
        }
        
        brew_response = client.post(f'/api/batches/{batch["id"]}/brew_sessions', json=brew_data)
        assert brew_response.status_code == 201
        brew_session = brew_response.get_json()
        
        # Try to update with invalid batch ID (empty string)
        update_data = {
            'product_batch_id': '',  # This should cause validation error
            'amount_coffee_grams': 26.0
        }
        
        update_response = client.put(f'/api/brew_sessions/{brew_session["id"]}', json=update_data)
        # Backend should reject with 404 for invalid batch
        assert update_response.status_code == 404
        
        # Try to update with None batch ID
        update_data_none = {
            'product_batch_id': None,
            'amount_coffee_grams': 26.0
        }
        
        update_response_none = client.put(f'/api/brew_sessions/{brew_session["id"]}', json=update_data_none)
        # Backend should reject with 404 for None batch
        assert update_response_none.status_code == 404
        
        # Valid update should work
        valid_update_data = {
            'product_batch_id': batch['id'],
            'amount_coffee_grams': 26.0
        }
        
        valid_update_response = client.put(f'/api/brew_sessions/{brew_session["id"]}', json=valid_update_data)
        assert valid_update_response.status_code == 200
        
        updated_session = valid_update_response.get_json()
        assert updated_session['amount_coffee_grams'] == 26.0
        assert updated_session['product_batch_id'] == batch['id']
    
    def test_edit_brew_session_change_product_and_batch(self, client, setup_test_data):
        """
        Bug Fix Test 4b: Test editing brew session to change product and batch.
        
        This reproduces the exact user scenario: editing an existing session
        to select a new product and new batch, then saving the form.
        """
        # Get original setup
        original_batch = setup_test_data['batch']
        original_product = setup_test_data['product']
        
        # Create a second product and batch to change to
        roaster = setup_test_data['roaster']
        bean_type = setup_test_data['bean_type']
        country = setup_test_data['country']
        
        # Create second product
        product2_data = {
            'name': 'Test Coffee 2',
            'roaster_id': roaster['id'],
            'bean_type_ids': [bean_type['id']],
            'country_id': country['id']
        }
        product2_response = client.post('/api/products', json=product2_data)
        assert product2_response.status_code == 201
        product2 = product2_response.get_json()
        
        # Create second batch
        batch2_data = {
            'roast_date': '2024-02-01',
            'purchase_date': '2024-02-02',
            'amount_grams': 250
        }
        batch2_response = client.post(f'/api/products/{product2["id"]}/batches', json=batch2_data)
        assert batch2_response.status_code == 201
        batch2 = batch2_response.get_json()
        
        # Create original brew session with first product/batch
        original_brew_data = {
            'amount_coffee_grams': 25.0,
            'amount_water_grams': 400.0,
            'brew_temperature_c': 93.5,
            'score': 7.5
        }
        
        brew_response = client.post(f'/api/batches/{original_batch["id"]}/brew_sessions', json=original_brew_data)
        assert brew_response.status_code == 201
        brew_session = brew_response.get_json()
        
        # Verify original session is linked to first product/batch
        assert brew_session['product_id'] == original_product['id']
        assert brew_session['product_batch_id'] == original_batch['id']
        
        # Now edit the session to change to the second product and batch
        # This is the exact scenario the user described
        edit_data = {
            'product_id': product2['id'],          # Change to new product
            'product_batch_id': batch2['id'],      # Change to new batch
            'amount_coffee_grams': 27.0,           # Also change some brewing parameters
            'amount_water_grams': 450.0,
            'brew_temperature_c': 94.0,
            'score': 8.0
        }
        
        # This should work without 404 error
        edit_response = client.put(f'/api/brew_sessions/{brew_session["id"]}', json=edit_data)
        
        if edit_response.status_code != 200:
            print(f"Edit failed with status {edit_response.status_code}")
            print(f"Response: {edit_response.get_json()}")
        
        assert edit_response.status_code == 200
        
        # Verify the changes were applied correctly
        updated_session = edit_response.get_json()
        assert updated_session['product_id'] == product2['id']
        assert updated_session['product_batch_id'] == batch2['id']
        assert updated_session['amount_coffee_grams'] == 27.0
        assert updated_session['amount_water_grams'] == 450.0
        assert updated_session['brew_temperature_c'] == 94.0
        assert updated_session['score'] == 8.0
        
        # Verify we can fetch the updated session
        fetch_response = client.get(f'/api/brew_sessions/{brew_session["id"]}')
        assert fetch_response.status_code == 200
        fetched_session = fetch_response.get_json()
        assert fetched_session['product_id'] == product2['id']
        assert fetched_session['product_batch_id'] == batch2['id']
    
    def test_edit_brew_session_mismatched_product_batch_validation(self, client, setup_test_data):
        """
        Bug Fix Test 4c: Test that editing brew session validates batch belongs to product.
        
        This tests the specific scenario where a user might select a batch that doesn't 
        belong to the selected product, which should result in a validation error.
        """
        # Get original setup
        original_batch = setup_test_data['batch']
        original_product = setup_test_data['product']
        
        # Create a second product and batch
        roaster = setup_test_data['roaster']
        bean_type = setup_test_data['bean_type']
        country = setup_test_data['country']
        
        # Create second product
        product2_data = {
            'name': 'Test Coffee 2',
            'roaster_id': roaster['id'],
            'bean_type_ids': [bean_type['id']],
            'country_id': country['id']
        }
        product2_response = client.post('/api/products', json=product2_data)
        assert product2_response.status_code == 201
        product2 = product2_response.get_json()
        
        # Create second batch for product2
        batch2_data = {
            'roast_date': '2024-02-01',
            'purchase_date': '2024-02-02',
            'amount_grams': 250
        }
        batch2_response = client.post(f'/api/products/{product2["id"]}/batches', json=batch2_data)
        assert batch2_response.status_code == 201
        batch2 = batch2_response.get_json()
        
        # Create original brew session
        original_brew_data = {
            'amount_coffee_grams': 25.0,
            'amount_water_grams': 400.0,
            'brew_temperature_c': 93.5
        }
        
        brew_response = client.post(f'/api/batches/{original_batch["id"]}/brew_sessions', json=original_brew_data)
        assert brew_response.status_code == 201
        brew_session = brew_response.get_json()
        
        # Try to edit session with mismatched product and batch
        # This should fail: trying to use batch2 (belongs to product2) with original_product
        invalid_edit_data = {
            'product_id': original_product['id'],  # Original product
            'product_batch_id': batch2['id'],      # Batch from different product - INVALID!
            'amount_coffee_grams': 27.0
        }
        
        # This should result in a 400 validation error
        edit_response = client.put(f'/api/brew_sessions/{brew_session["id"]}', json=invalid_edit_data)
        
        if edit_response.status_code != 400:
            print(f"Expected 400, got {edit_response.status_code}")
            print(f"Response: {edit_response.get_json()}")
        
        assert edit_response.status_code == 400
        error_response = edit_response.get_json()
        assert 'Batch does not belong to the specified product' in error_response['error']
        
        # Verify the session wasn't changed
        fetch_response = client.get(f'/api/brew_sessions/{brew_session["id"]}')
        assert fetch_response.status_code == 200
        unchanged_session = fetch_response.get_json()
        assert unchanged_session['product_id'] == original_product['id']
        assert unchanged_session['product_batch_id'] == original_batch['id']
    
    def test_edit_brew_session_nonexistent_product_error(self, client, setup_test_data):
        """
        Bug Fix Test 4d: Test editing brew session with nonexistent product ID.
        
        This reproduces the exact "Product not found" error the user experienced.
        """
        batch = setup_test_data['batch']
        
        # Create a brew session
        brew_data = {
            'amount_coffee_grams': 25.0,
            'amount_water_grams': 400.0,
            'brew_temperature_c': 93.5
        }
        
        brew_response = client.post(f'/api/batches/{batch["id"]}/brew_sessions', json=brew_data)
        assert brew_response.status_code == 201
        brew_session = brew_response.get_json()
        
        # Try to edit with nonexistent product ID
        invalid_edit_data = {
            'product_id': 99999,  # This product doesn't exist
            'product_batch_id': batch['id'],
            'amount_coffee_grams': 27.0
        }
        
        edit_response = client.put(f'/api/brew_sessions/{brew_session["id"]}', json=invalid_edit_data)
        
        print(f"Status: {edit_response.status_code}")
        print(f"Response: {edit_response.get_json()}")
        
        # This should result in "Product not found" error
        assert edit_response.status_code == 404
        error_response = edit_response.get_json()
        assert error_response['error'] == 'Product not found'
    
    def test_edit_brew_session_with_string_ids_from_frontend(self, client, setup_test_data):
        """
        Bug Fix Test 4e: Test editing brew session with string IDs (as sent by frontend forms).
        
        This reproduces the exact issue where HTML forms send IDs as strings,
        but the backend expects integers for lookups.
        """
        # Get original setup
        original_batch = setup_test_data['batch']
        original_product = setup_test_data['product']
        
        # Create a second product and batch to change to
        roaster = setup_test_data['roaster']
        bean_type = setup_test_data['bean_type']
        country = setup_test_data['country']
        
        # Create second product
        product2_data = {
            'name': 'Test Coffee 2',
            'roaster_id': roaster['id'],
            'bean_type_ids': [bean_type['id']],
            'country_id': country['id']
        }
        product2_response = client.post('/api/products', json=product2_data)
        assert product2_response.status_code == 201
        product2 = product2_response.get_json()
        
        # Create second batch
        batch2_data = {
            'roast_date': '2024-02-01',
            'purchase_date': '2024-02-02',
            'amount_grams': 250
        }
        batch2_response = client.post(f'/api/products/{product2["id"]}/batches', json=batch2_data)
        assert batch2_response.status_code == 201
        batch2 = batch2_response.get_json()
        
        # Create original brew session
        original_brew_data = {
            'amount_coffee_grams': 25.0,
            'amount_water_grams': 400.0,
            'brew_temperature_c': 93.5
        }
        
        brew_response = client.post(f'/api/batches/{original_batch["id"]}/brew_sessions', json=original_brew_data)
        assert brew_response.status_code == 201
        brew_session = brew_response.get_json()
        
        # Edit with STRING IDs (as HTML forms send them)
        # This is exactly what the frontend sends after form input
        edit_data = {
            'product_id': str(product2['id']),      # STRING instead of int
            'product_batch_id': str(batch2['id']),  # STRING instead of int
            'amount_coffee_grams': 27.0,
            'amount_water_grams': 450.0,
            'brew_temperature_c': 94.0
        }
        
        # This should work now (was failing before with "Product not found")
        edit_response = client.put(f'/api/brew_sessions/{brew_session["id"]}', json=edit_data)
        
        if edit_response.status_code != 200:
            print(f"Edit failed with status {edit_response.status_code}")
            print(f"Response: {edit_response.get_json()}")
        
        assert edit_response.status_code == 200
        
        # Verify the changes were applied correctly
        updated_session = edit_response.get_json()
        assert updated_session['product_id'] == product2['id']  # Should be converted back to int
        assert updated_session['product_batch_id'] == batch2['id']  # Should be converted back to int
        assert updated_session['amount_coffee_grams'] == 27.0
    
    def test_brew_session_edit_invalid_batch_id_rejection(self, client, setup_test_data):
        """
        Bug Fix Test 4: Ensure brew session update rejects invalid batch IDs.
        
        Tests that when editing a brew session and changing the product,
        an empty or null batch ID is properly rejected with a 404 error.
        This prevents the scenario where the frontend sends an empty
        product_batch_id and causes a 404 error.
        """
        batch = setup_test_data['batch']
        
        # Create a second product and batch
        product2_response = client.post('/api/products', json={'roaster_name': 'Second Roaster'})
        assert product2_response.status_code == 201
        product2 = product2_response.get_json()
        
        batch2_response = client.post(f'/api/products/{product2["id"]}/batches', json={'roast_date': '2025-01-03'})
        assert batch2_response.status_code == 201
        batch2 = batch2_response.get_json()
        
        # Create a brew session with the first batch
        brew_data = {
            'brew_method': 'V60',
            'amount_coffee_grams': 18.0,
            'amount_water_grams': 300.0,
            'notes': 'Original session'
        }
        brew_response = client.post(f'/api/batches/{batch["id"]}/brew_sessions', json=brew_data)
        assert brew_response.status_code == 201
        brew_session = brew_response.get_json()
        
        # Test 1: Try to update with empty string batch ID (frontend bug scenario)
        update_data_empty = {
            'product_batch_id': '',  # Empty string should be rejected
            'product_id': product2['id'],
            'brew_method': 'Chemex',
            'notes': 'Updated notes'
        }
        update_response_empty = client.put(f'/api/brew_sessions/{brew_session["id"]}', json=update_data_empty)
        assert update_response_empty.status_code == 404
        error_data = update_response_empty.get_json()
        assert 'Batch not found' in error_data['error']
        
        # Test 2: Try to update with null batch ID
        update_data_null = {
            'product_batch_id': None,
            'product_id': product2['id'],
            'brew_method': 'Chemex',
            'notes': 'Updated notes'
        }
        update_response_null = client.put(f'/api/brew_sessions/{brew_session["id"]}', json=update_data_null)
        assert update_response_null.status_code == 404
        error_data = update_response_null.get_json()
        assert 'Batch not found' in error_data['error']
        
        # Test 3: Valid update should work
        update_data_valid = {
            'product_batch_id': batch2['id'],
            'product_id': product2['id'],
            'brew_method': 'Chemex',
            'notes': 'Updated notes'
        }
        update_response_valid = client.put(f'/api/brew_sessions/{brew_session["id"]}', json=update_data_valid)
        assert update_response_valid.status_code == 200
        updated_session = update_response_valid.get_json()
        assert updated_session['product_batch_id'] == batch2['id']
        assert updated_session['product_id'] == product2['id']
        assert updated_session['notes'] == 'Updated notes'