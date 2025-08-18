import pytest
import json
import tempfile
from datetime import datetime, timezone
from src.coffeejournal import create_app
from src.coffeejournal.repositories.factory import RepositoryFactory


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def client(temp_data_dir):
    """Create test client with temporary data directory."""
    app = create_app(test_config={
        'TESTING': True,
        'DATA_DIR': temp_data_dir,
        'SECRET_KEY': 'test'
    })
    with app.test_client() as client:
        yield client


@pytest.fixture
def factory(temp_data_dir):
    """Create repository factory."""
    return RepositoryFactory(storage_type='json', data_dir=temp_data_dir)


@pytest.fixture
def sample_data(factory):
    """Create sample data for testing."""
    # Create roaster
    roaster = factory.get_roaster_repository().create({'name': 'Test Roaster'})
    
    # Create product
    product = factory.get_product_repository().create({
        'product_name': 'Test Coffee',
        'roaster_id': roaster['id']
    })
    
    # Create batch
    batch = factory.get_batch_repository().create({
        'product_id': product['id'],
        'amount_grams': 250,
        'roast_date': '2024-01-01'
    })
    
    # Create lookup items
    brew_method = factory.get_brew_method_repository().create({'name': 'V60'})
    recipe = factory.get_recipe_repository().create({'name': 'Standard Recipe'})
    grinder = factory.get_grinder_repository().create({'name': 'Comandante'})
    filter_item = factory.get_filter_repository().create({'name': 'V60 Filter'})
    kettle = factory.get_kettle_repository().create({'name': 'Hario Buono'})
    scale = factory.get_scale_repository().create({'name': 'Acaia Pearl'})
    
    # Create original brew session
    original_session = factory.get_brew_session_repository().create({
        'product_id': product['id'],
        'product_batch_id': batch['id'],
        'brew_method_id': brew_method['id'],
        'recipe_id': recipe['id'],
        'grinder_id': grinder['id'],
        'grinder_setting': '15',
        'filter_id': filter_item['id'],
        'kettle_id': kettle['id'],
        'scale_id': scale['id'],
        'timestamp': '2024-01-15T08:30:00',
        'amount_coffee_grams': 20.0,
        'amount_water_grams': 320.0,
        'brew_temperature_c': 93.0,
        'bloom_time_seconds': 30,
        'brew_time_seconds': 180,
        'sweetness': 8,
        'acidity': 9,
        'bitterness': 3,
        'body': 6,
        'aroma': 9,
        'flavor_profile_match': 8,
        'score': 8.5,
        'notes': 'Excellent floral notes, very clean'
    })
    
    return {
        'roaster': roaster,
        'product': product,
        'batch': batch,
        'brew_method': brew_method,
        'recipe': recipe,
        'grinder': grinder,
        'filter': filter_item,
        'kettle': kettle,
        'scale': scale,
        'original_session': original_session
    }


def test_duplicate_brew_session_success(client, factory, sample_data):
    """Test successful brew session duplication."""
    batch_id = sample_data['batch']['id']
    session_id = sample_data['original_session']['id']
    
    response = client.post(f'/api/batches/{batch_id}/brew_sessions/{session_id}/duplicate')
    assert response.status_code == 201
    
    duplicated_data = json.loads(response.data)
    original = sample_data['original_session']
    
    # Should have different ID and timestamp
    assert duplicated_data['id'] != original['id']
    assert duplicated_data['timestamp'] != original['timestamp']
    
    # All other fields should be identical
    assert duplicated_data['product_id'] == original['product_id']
    assert duplicated_data['product_batch_id'] == original['product_batch_id']
    assert duplicated_data['brew_method_id'] == original['brew_method_id']
    assert duplicated_data['recipe_id'] == original['recipe_id']
    assert duplicated_data['grinder_id'] == original['grinder_id']
    assert duplicated_data['grinder_setting'] == original['grinder_setting']
    assert duplicated_data['filter_id'] == original['filter_id']
    assert duplicated_data['kettle_id'] == original['kettle_id']
    assert duplicated_data['scale_id'] == original['scale_id']
    assert duplicated_data['amount_coffee_grams'] == original['amount_coffee_grams']
    assert duplicated_data['amount_water_grams'] == original['amount_water_grams']
    assert duplicated_data['brew_temperature_c'] == original['brew_temperature_c']
    assert duplicated_data['bloom_time_seconds'] == original['bloom_time_seconds']
    assert duplicated_data['brew_time_seconds'] == original['brew_time_seconds']
    assert duplicated_data['sweetness'] == original['sweetness']
    assert duplicated_data['acidity'] == original['acidity']
    assert duplicated_data['bitterness'] == original['bitterness']
    assert duplicated_data['body'] == original['body']
    assert duplicated_data['aroma'] == original['aroma']
    assert duplicated_data['flavor_profile_match'] == original['flavor_profile_match']
    assert duplicated_data['score'] == original['score']
    assert duplicated_data['notes'] == original['notes']


def test_duplicate_brew_session_updates_timestamp(client, factory, sample_data):
    """Test that duplicated session has current timestamp."""
    batch_id = sample_data['batch']['id']
    session_id = sample_data['original_session']['id']
    
    before_request = datetime.now(timezone.utc)
    
    response = client.post(f'/api/batches/{batch_id}/brew_sessions/{session_id}/duplicate')
    assert response.status_code == 201
    
    after_request = datetime.now(timezone.utc)
    
    duplicated_data = json.loads(response.data)
    
    # Parse the timestamp
    timestamp_str = duplicated_data['timestamp']
    if timestamp_str.endswith('Z'):
        timestamp_str = timestamp_str[:-1] + '+00:00'
    
    duplicated_timestamp = datetime.fromisoformat(timestamp_str)
    
    # Should be between before and after request times
    assert before_request <= duplicated_timestamp <= after_request


def test_duplicate_brew_session_creates_new_record(client, factory, sample_data):
    """Test that duplication actually creates a new database record."""
    batch_id = sample_data['batch']['id']
    session_id = sample_data['original_session']['id']
    
    # Get initial count
    all_sessions_before = factory.get_brew_session_repository().find_all()
    count_before = len(all_sessions_before)
    
    response = client.post(f'/api/batches/{batch_id}/brew_sessions/{session_id}/duplicate')
    assert response.status_code == 201
    
    # Should have one more session
    all_sessions_after = factory.get_brew_session_repository().find_all()
    count_after = len(all_sessions_after)
    assert count_after == count_before + 1
    
    # Verify the new session exists in database
    duplicated_data = json.loads(response.data)
    new_session = factory.get_brew_session_repository().find_by_id(duplicated_data['id'])
    assert new_session is not None
    assert new_session['id'] == duplicated_data['id']


def test_duplicate_nonexistent_session(client, sample_data):
    """Test duplication of non-existent session returns 404."""
    batch_id = sample_data['batch']['id']
    nonexistent_session_id = 99999
    
    response = client.post(f'/api/batches/{batch_id}/brew_sessions/{nonexistent_session_id}/duplicate')
    assert response.status_code == 404
    
    error_data = json.loads(response.data)
    assert 'message' in error_data
    assert 'not found' in error_data['message'].lower()


def test_duplicate_with_nonexistent_batch(client, sample_data):
    """Test duplication with non-existent batch returns 404."""
    nonexistent_batch_id = 99999
    session_id = sample_data['original_session']['id']
    
    response = client.post(f'/api/batches/{nonexistent_batch_id}/brew_sessions/{session_id}/duplicate')
    assert response.status_code == 404


def test_duplicate_session_from_different_batch(client, factory, sample_data):
    """Test duplication fails when session doesn't belong to the specified batch."""
    # Create another batch
    another_batch = factory.get_batch_repository().create({
        'product_id': sample_data['product']['id'],
        'amount_grams': 300,
        'roast_date': '2024-01-02'
    })
    
    # Try to duplicate session from first batch using second batch ID
    session_id = sample_data['original_session']['id']
    
    response = client.post(f'/api/batches/{another_batch["id"]}/brew_sessions/{session_id}/duplicate')
    assert response.status_code == 400
    
    error_data = json.loads(response.data)
    assert 'does not belong to batch' in error_data['message']


def test_duplicate_minimal_session(client, factory, sample_data):
    """Test duplication of session with minimal required fields."""
    # Create minimal session
    minimal_session = factory.get_brew_session_repository().create({
        'product_id': sample_data['product']['id'],
        'product_batch_id': sample_data['batch']['id'],
        'amount_coffee_grams': 18.0,
        'amount_water_grams': 300.0,
        'timestamp': '2024-01-16T09:00:00'
        # All other fields are optional/None
    })
    
    batch_id = sample_data['batch']['id']
    
    response = client.post(f'/api/batches/{batch_id}/brew_sessions/{minimal_session["id"]}/duplicate')
    assert response.status_code == 201
    
    duplicated_data = json.loads(response.data)
    
    # Required fields should be copied
    assert duplicated_data['product_id'] == minimal_session['product_id']
    assert duplicated_data['product_batch_id'] == minimal_session['product_batch_id']
    assert duplicated_data['amount_coffee_grams'] == minimal_session['amount_coffee_grams']
    assert duplicated_data['amount_water_grams'] == minimal_session['amount_water_grams']
    
    # Optional fields should remain None/unset
    assert duplicated_data.get('brew_method_id') is None
    assert duplicated_data.get('recipe_id') is None
    assert duplicated_data.get('grinder_id') is None
    assert duplicated_data.get('notes') == '' or duplicated_data.get('notes') is None


def test_duplicate_session_with_ratings(client, factory, sample_data):
    """Test duplication preserves all rating fields."""
    # Create session with ratings
    session_with_ratings = factory.get_brew_session_repository().create({
        'product_id': sample_data['product']['id'],
        'product_batch_id': sample_data['batch']['id'],
        'amount_coffee_grams': 20.0,
        'amount_water_grams': 320.0,
        'timestamp': '2024-01-17T10:00:00',
        'sweetness': 8,
        'acidity': 9,
        'bitterness': 3,
        'body': 7,
        'aroma': 9,
        'flavor_profile_match': 8,
        'score': 8.25
    })
    
    batch_id = sample_data['batch']['id']
    
    response = client.post(f'/api/batches/{batch_id}/brew_sessions/{session_with_ratings["id"]}/duplicate')
    assert response.status_code == 201
    
    duplicated_data = json.loads(response.data)
    
    # All ratings should be preserved exactly
    assert duplicated_data['sweetness'] == 8
    assert duplicated_data['acidity'] == 9
    assert duplicated_data['bitterness'] == 3
    assert duplicated_data['body'] == 7
    assert duplicated_data['aroma'] == 9
    assert duplicated_data['flavor_profile_match'] == 8
    assert duplicated_data['score'] == 8.25


def test_duplicate_session_preserves_metadata(client, sample_data):
    """Test that duplication preserves created_at but updates updated_at."""
    batch_id = sample_data['batch']['id']
    session_id = sample_data['original_session']['id']
    
    response = client.post(f'/api/batches/{batch_id}/brew_sessions/{session_id}/duplicate')
    assert response.status_code == 201
    
    duplicated_data = json.loads(response.data)
    
    # Should have created_at and updated_at
    assert 'created_at' in duplicated_data
    assert 'updated_at' in duplicated_data
    
    # Both should be recent (since it's a new record)
    now = datetime.now(timezone.utc)
    created_at = datetime.fromisoformat(duplicated_data['created_at'].replace('Z', '+00:00'))
    updated_at = datetime.fromisoformat(duplicated_data['updated_at'].replace('Z', '+00:00'))
    
    # Both timestamps should be very recent
    time_diff_created = abs((now - created_at).total_seconds())
    time_diff_updated = abs((now - updated_at).total_seconds())
    assert time_diff_created < 5  # Within 5 seconds
    assert time_diff_updated < 5  # Within 5 seconds


def test_duplicate_endpoint_http_methods(client, sample_data):
    """Test that only POST method is allowed for duplication endpoint."""
    batch_id = sample_data['batch']['id']
    session_id = sample_data['original_session']['id']
    url = f'/api/batches/{batch_id}/brew_sessions/{session_id}/duplicate'
    
    # POST should work
    response = client.post(url)
    assert response.status_code == 201
    
    # Other methods should not be allowed
    response = client.get(url)
    assert response.status_code == 405
    
    response = client.put(url)
    assert response.status_code == 405
    
    response = client.delete(url)
    assert response.status_code == 405