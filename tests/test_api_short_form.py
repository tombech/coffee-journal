"""
Test API endpoints for short_form functionality and full lookup object responses.
"""
import pytest
import json


class TestAPIShortFormFunctionality:
    """Test API endpoints return full lookup objects and support short_form searches."""
    
    def test_brew_session_returns_full_lookup_objects(self, client):
        """Test that brew session endpoints return full lookup objects instead of just names."""
        # Create a roaster first
        roaster_response = client.post('/api/roasters', json={
            'name': 'Test Roaster',
            'short_form': 'TR'
        })
        assert roaster_response.status_code == 201
        
        # Create a product
        product_response = client.post('/api/products', json={
            'roaster': 'Test Roaster',
            'bean_type': 'Arabica',
            'product_name': 'Test Blend'
        })
        assert product_response.status_code == 201
        product = product_response.get_json()
        
        # Create a batch
        batch_response = client.post(f'/api/products/{product["id"]}/batches', json={
            'roast_date': '2024-01-01',
            'amount_grams': 250,
            'price': 15.0
        })
        assert batch_response.status_code == 201
        batch = batch_response.get_json()
        
        # Create a brew method with short_form
        brew_method_response = client.post('/api/brew_methods', json={
            'name': 'French Press',
            'short_form': 'FP'
        })
        assert brew_method_response.status_code == 201
        
        # Create brew session using full name
        session_response = client.post(f'/api/batches/{batch["id"]}/brew_sessions', json={
            'brew_method': 'French Press',
            'amount_coffee_grams': 25,
            'amount_water_grams': 400
        })
        assert session_response.status_code == 201
        session = session_response.get_json()
        
        # Verify brew_method is returned as full object
        assert isinstance(session['brew_method'], dict)
        assert session['brew_method']['name'] == 'French Press'
        assert session['brew_method']['short_form'] == 'FP'
        assert session['brew_method']['id'] is not None
    
    def test_brew_session_creation_with_short_form(self, client):
        """Test creating brew session using short_form identifiers."""
        # Create a product and batch first
        roaster_response = client.post('/api/roasters', json={'name': 'Short Form Roaster'})
        product_response = client.post('/api/products', json={
            'roaster': 'Short Form Roaster',
            'bean_type': 'Arabica',
            'product_name': 'Test Product'
        })
        product = product_response.get_json()
        
        batch_response = client.post(f'/api/products/{product["id"]}/batches', json={
            'roast_date': '2024-01-01',
            'amount_grams': 250,
            'price': 15.0
        })
        batch = batch_response.get_json()
        
        # Create brew method with short_form
        client.post('/api/brew_methods', json={
            'name': 'AeroPress',
            'short_form': 'AP'
        })
        
        # Create recipe with short_form
        client.post('/api/recipes', json={
            'name': 'Standard Recipe',
            'short_form': 'STD'
        })
        
        # Create grinder with short_form
        client.post('/api/grinders', json={
            'name': 'Baratza Encore',
            'short_form': 'BE'
        })
        
        # Create brew session using short_form identifiers
        response = client.post(f'/api/batches/{batch["id"]}/brew_sessions', json={
            'brew_method': 'AP',  # Using short_form
            'recipe': 'STD',      # Using short_form
            'grinder': 'BE',      # Using short_form
            'amount_coffee_grams': 18,
            'amount_water_grams': 200
        })
        
        assert response.status_code == 201
        session = response.get_json()
        
        # Verify lookup objects are returned with correct data
        assert session['brew_method']['name'] == 'AeroPress'
        assert session['brew_method']['short_form'] == 'AP'
        
        assert session['recipe']['name'] == 'Standard Recipe'
        assert session['recipe']['short_form'] == 'STD'
        
        assert session['grinder']['name'] == 'Baratza Encore'
        assert session['grinder']['short_form'] == 'BE'
    
    def test_brew_session_no_duplicate_creation(self, client):
        """Test that using short_form doesn't create duplicate lookup items."""
        # Create product and batch
        roaster_response = client.post('/api/roasters', json={'name': 'No Dup Roaster'})
        product_response = client.post('/api/products', json={
            'roaster': 'No Dup Roaster',
            'bean_type': 'Arabica',
            'product_name': 'Test Product'
        })
        product = product_response.get_json()
        
        batch_response = client.post(f'/api/products/{product["id"]}/batches', json={
            'roast_date': '2024-01-01',
            'amount_grams': 250,
            'price': 15.0
        })
        batch = batch_response.get_json()
        
        # Create brew method
        brew_method_response = client.post('/api/brew_methods', json={
            'name': 'V60',
            'short_form': 'V60'
        })
        original_brew_method = brew_method_response.get_json()
        
        # Get initial count of brew methods
        initial_response = client.get('/api/brew_methods')
        initial_count = len(initial_response.get_json())
        
        # Create brew session using short_form
        session_response = client.post(f'/api/batches/{batch["id"]}/brew_sessions', json={
            'brew_method': 'V60',  # Using short_form (same as name in this case)
            'amount_coffee_grams': 20,
            'amount_water_grams': 300
        })
        assert session_response.status_code == 201
        session = session_response.get_json()
        
        # Verify it found the existing brew method
        assert session['brew_method']['id'] == original_brew_method['id']
        
        # Verify no new brew method was created
        final_response = client.get('/api/brew_methods')
        final_count = len(final_response.get_json())
        assert final_count == initial_count
    
    def test_get_all_brew_sessions_returns_full_objects(self, client):
        """Test that GET /api/brew_sessions returns full lookup objects."""
        # Create necessary data
        roaster_response = client.post('/api/roasters', json={'name': 'API Test Roaster'})
        product_response = client.post('/api/products', json={
            'roaster': 'API Test Roaster',
            'bean_type': 'Arabica',
            'product_name': 'API Test Product'
        })
        product = product_response.get_json()
        
        batch_response = client.post(f'/api/products/{product["id"]}/batches', json={
            'roast_date': '2024-01-01',
            'amount_grams': 250,
            'price': 15.0
        })
        batch = batch_response.get_json()
        
        # Create lookup items
        client.post('/api/brew_methods', json={
            'name': 'Chemex',
            'short_form': 'CMX',
            'description': 'Pour-over brewing method'
        })
        
        client.post('/api/filters', json={
            'name': 'Paper Filter',
            'short_form': 'PAPER'
        })
        
        # Create brew session
        client.post(f'/api/batches/{batch["id"]}/brew_sessions', json={
            'brew_method': 'CMX',
            'filter': 'PAPER',
            'amount_coffee_grams': 30,
            'amount_water_grams': 500
        })
        
        # Get all brew sessions
        response = client.get('/api/brew_sessions')
        assert response.status_code == 200
        sessions = response.get_json()
        
        # Find our session
        test_session = None
        for session in sessions:
            if (session.get('brew_method') and 
                isinstance(session['brew_method'], dict) and
                session['brew_method'].get('name') == 'Chemex'):
                test_session = session
                break
        
        assert test_session is not None
        
        # Verify full objects are returned
        assert isinstance(test_session['brew_method'], dict)
        assert test_session['brew_method']['name'] == 'Chemex'
        assert test_session['brew_method']['short_form'] == 'CMX'
        assert test_session['brew_method']['description'] == 'Pour-over brewing method'
        
        assert isinstance(test_session['filter'], dict)
        assert test_session['filter']['name'] == 'Paper Filter'
        assert test_session['filter']['short_form'] == 'PAPER'
    
    def test_brew_session_update_with_short_form(self, client):
        """Test updating brew session using short_form identifiers."""
        # Create necessary data
        roaster_response = client.post('/api/roasters', json={'name': 'Update Test Roaster'})
        product_response = client.post('/api/products', json={
            'roaster': 'Update Test Roaster',
            'bean_type': 'Arabica',
            'product_name': 'Update Test Product'
        })
        product = product_response.get_json()
        
        batch_response = client.post(f'/api/products/{product["id"]}/batches', json={
            'roast_date': '2024-01-01',
            'amount_grams': 250,
            'price': 15.0
        })
        batch = batch_response.get_json()
        
        # Create initial brew method
        client.post('/api/brew_methods', json={
            'name': 'French Press',
            'short_form': 'FP'
        })
        
        # Create alternative brew method
        client.post('/api/brew_methods', json={
            'name': 'Espresso',
            'short_form': 'ESP'
        })
        
        # Create initial brew session
        session_response = client.post(f'/api/batches/{batch["id"]}/brew_sessions', json={
            'brew_method': 'FP',
            'amount_coffee_grams': 25,
            'amount_water_grams': 400
        })
        session = session_response.get_json()
        session_id = session['id']
        
        # Update brew session using short_form
        update_response = client.put(f'/api/brew_sessions/{session_id}', json={
            'brew_method': 'ESP',  # Change to Espresso using short_form
            'amount_coffee_grams': 18,
            'amount_water_grams': 36
        })
        
        assert update_response.status_code == 200
        updated_session = update_response.get_json()
        
        # Verify the brew method was updated correctly
        assert updated_session['brew_method']['name'] == 'Espresso'
        assert updated_session['brew_method']['short_form'] == 'ESP'
        assert updated_session['amount_coffee_grams'] == 18
        assert updated_session['amount_water_grams'] == 36