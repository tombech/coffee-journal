"""Test that brew temperature field accepts float values."""

import pytest
from coffeejournal import create_app
from coffeejournal.repositories.factory import get_repository_factory


@pytest.fixture
def app():
    """Create test Flask app with temporary data directory."""
    import tempfile
    import os
    
    test_dir = tempfile.mkdtemp()
    os.environ['DATA_DIR'] = test_dir
    
    app = create_app()
    app.config['TESTING'] = True
    
    yield app
    
    # Clean up
    import shutil
    shutil.rmtree(test_dir)


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_brew_temperature_accepts_float(client):
    """Test that brew temperature field accepts and stores float values correctly."""
    # Create test data
    roaster_response = client.post('/api/roasters', json={'name': 'Test Roaster'})
    assert roaster_response.status_code == 201
    roaster_id = roaster_response.get_json()['id']
    
    bean_type_response = client.post('/api/bean_types', json={'name': 'Test Bean'})
    assert bean_type_response.status_code == 201
    bean_type_id = bean_type_response.get_json()['id']
    
    country_response = client.post('/api/countries', json={'name': 'Test Country'})
    assert country_response.status_code == 201
    country_id = country_response.get_json()['id']
    
    # Create product
    product_response = client.post('/api/products', json={
        'product_name': 'Test Coffee',
        'roaster_id': roaster_id,
        'bean_type_id': [bean_type_id],
        'country_id': country_id
    })
    assert product_response.status_code == 201
    product_id = product_response.get_json()['id']
    
    # Create batch
    batch_response = client.post(f'/api/products/{product_id}/batches', json={
        'roast_date': '2024-01-01',
        'purchase_date': '2024-01-02',
        'amount_grams': 250.0,
        'price': 20.0
    })
    assert batch_response.status_code == 201
    batch_id = batch_response.get_json()['id']
    
    # Test 1: Create brew session with float temperature
    session_response = client.post(f'/api/batches/{batch_id}/brew_sessions', json={
        'timestamp': '2024-01-03T09:00:00',
        'brew_method': 'V60',
        'amount_coffee_grams': 20.0,
        'amount_water_grams': 320.0,
        'brew_temperature_c': 93.5,  # Float temperature
        'brew_time_seconds': 180,
        'sweetness': 7,
        'acidity': 8,
        'bitterness': 3,
        'body': 6,
        'aroma': 8,
        'flavor_profile_match': 7,
        'score': 7.5,
        'notes': 'Testing float temperature'
    })
    
    assert session_response.status_code == 201
    created_session = session_response.get_json()
    
    # Verify temperature was stored as float
    assert created_session['brew_temperature_c'] == 93.5
    assert isinstance(created_session['brew_temperature_c'], float)
    
    # Test 2: Fetch session and verify temperature persisted correctly
    get_response = client.get(f'/api/brew_sessions/{created_session["id"]}')
    assert get_response.status_code == 200
    fetched_session = get_response.get_json()
    
    assert fetched_session['brew_temperature_c'] == 93.5
    assert isinstance(fetched_session['brew_temperature_c'], float)
    
    # Test 3: Update session with different float temperature
    update_response = client.put(f'/api/brew_sessions/{created_session["id"]}', json={
        'product_id': product_id,
        'product_batch_id': batch_id,
        'brew_temperature_c': 94.2
    })
    
    assert update_response.status_code == 200
    updated_session = update_response.get_json()
    
    # Verify updated temperature is float
    assert updated_session['brew_temperature_c'] == 94.2
    assert isinstance(updated_session['brew_temperature_c'], float)
    
    # Test 4: Create session with integer temperature (should still work)
    int_temp_response = client.post(f'/api/batches/{batch_id}/brew_sessions', json={
        'timestamp': '2024-01-04T09:00:00',
        'brew_method': 'Chemex',
        'amount_coffee_grams': 30.0,
        'amount_water_grams': 500.0,
        'brew_temperature_c': 95,  # Integer temperature
        'brew_time_seconds': 240,
        'notes': 'Testing integer temperature'
    })
    
    assert int_temp_response.status_code == 201
    int_temp_session = int_temp_response.get_json()
    
    # Integer should be converted to float for consistency
    assert int_temp_session['brew_temperature_c'] == 95.0
    assert isinstance(int_temp_session['brew_temperature_c'], float)
    
    # Test 5: Edge case with high precision float
    precision_response = client.post(f'/api/batches/{batch_id}/brew_sessions', json={
        'timestamp': '2024-01-05T09:00:00',
        'brew_method': 'AeroPress',
        'amount_coffee_grams': 15.0,
        'amount_water_grams': 250.0,
        'brew_temperature_c': 87.75,  # High precision float
        'brew_time_seconds': 120,
        'notes': 'Testing high precision temperature'
    })
    
    assert precision_response.status_code == 201
    precision_session = precision_response.get_json()
    
    # High precision should be preserved
    assert precision_session['brew_temperature_c'] == 87.75
    assert isinstance(precision_session['brew_temperature_c'], float)