import pytest
import tempfile
import os
from src.coffeejournal import create_app


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def app(temp_data_dir):
    """Create Flask app with test configuration."""
    app = create_app({
        'TESTING': True,
        'DATA_DIR': temp_data_dir,
        'SECRET_KEY': 'test-secret-key'
    })
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_grinder_create_valid_number(client):
    """Test creating grinder with valid numeric value."""
    response = client.post('/api/grinders', 
        json={'name': 'Test Grinder', 'manually_ground_grams': 50.5},
        headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['manually_ground_grams'] == 50.5
    assert isinstance(data['manually_ground_grams'], float)


def test_grinder_create_string_number(client):
    """Test creating grinder with string number (should be converted)."""
    response = client.post('/api/grinders', 
        json={'name': 'Test Grinder 2', 'manually_ground_grams': '100'},
        headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['manually_ground_grams'] == 100.0
    assert isinstance(data['manually_ground_grams'], float)


def test_grinder_create_invalid_string(client):
    """Test creating grinder with invalid string (should fail)."""
    response = client.post('/api/grinders', 
        json={'name': 'Test Grinder 3', 'manually_ground_grams': 'invalid'},
        headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 400
    error = response.get_json()
    assert 'Manual ground amount must be a valid number' in error['error']


def test_grinder_create_negative_number(client):
    """Test creating grinder with negative number (should fail)."""
    response = client.post('/api/grinders', 
        json={'name': 'Test Grinder 4', 'manually_ground_grams': -10},
        headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 400
    error = response.get_json()
    assert 'Manual ground amount cannot be negative' in error['error']


def test_grinder_create_null_value(client):
    """Test creating grinder with null value (should be allowed)."""
    response = client.post('/api/grinders', 
        json={'name': 'Test Grinder 5', 'manually_ground_grams': None},
        headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['manually_ground_grams'] is None


def test_grinder_create_missing_field(client):
    """Test creating grinder without manually_ground_grams field."""
    response = client.post('/api/grinders', 
        json={'name': 'Test Grinder 6'},
        headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 201
    data = response.get_json()
    # The default should be applied
    assert data['manually_ground_grams'] == 0


def test_grinder_update_valid_number(client):
    """Test updating grinder with valid numeric value."""
    # Create grinder first
    response = client.post('/api/grinders', 
        json={'name': 'Update Test Grinder', 'manually_ground_grams': 50},
        headers={'Content-Type': 'application/json'})
    grinder = response.get_json()
    grinder_id = grinder['id']
    
    # Update with valid number
    response = client.put(f'/api/grinders/{grinder_id}', 
        json={'manually_ground_grams': 75.5},
        headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['manually_ground_grams'] == 75.5
    assert isinstance(data['manually_ground_grams'], float)


def test_grinder_update_string_number(client):
    """Test updating grinder with string number (should be converted)."""
    # Create grinder first
    response = client.post('/api/grinders', 
        json={'name': 'Update Test Grinder 2', 'manually_ground_grams': 50},
        headers={'Content-Type': 'application/json'})
    grinder = response.get_json()
    grinder_id = grinder['id']
    
    # Update with string number
    response = client.put(f'/api/grinders/{grinder_id}', 
        json={'manually_ground_grams': '125.75'},
        headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['manually_ground_grams'] == 125.75
    assert isinstance(data['manually_ground_grams'], float)


def test_grinder_update_invalid_string(client):
    """Test updating grinder with invalid string (should fail)."""
    # Create grinder first
    response = client.post('/api/grinders', 
        json={'name': 'Update Test Grinder 3', 'manually_ground_grams': 50},
        headers={'Content-Type': 'application/json'})
    grinder = response.get_json()
    grinder_id = grinder['id']
    
    # Update with invalid string
    response = client.put(f'/api/grinders/{grinder_id}', 
        json={'manually_ground_grams': 'not_a_number'},
        headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 400
    error = response.get_json()
    assert 'Manual ground amount must be a valid number' in error['error']


def test_grinder_update_negative_number(client):
    """Test updating grinder with negative number (should fail)."""
    # Create grinder first
    response = client.post('/api/grinders', 
        json={'name': 'Update Test Grinder 4', 'manually_ground_grams': 50},
        headers={'Content-Type': 'application/json'})
    grinder = response.get_json()
    grinder_id = grinder['id']
    
    # Update with negative number
    response = client.put(f'/api/grinders/{grinder_id}', 
        json={'manually_ground_grams': -25},
        headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 400
    error = response.get_json()
    assert 'Manual ground amount cannot be negative' in error['error']


def test_grinder_update_to_null(client):
    """Test updating grinder to null value (should be allowed)."""
    # Create grinder first
    response = client.post('/api/grinders', 
        json={'name': 'Update Test Grinder 5', 'manually_ground_grams': 50},
        headers={'Content-Type': 'application/json'})
    grinder = response.get_json()
    grinder_id = grinder['id']
    
    # Update to null
    response = client.put(f'/api/grinders/{grinder_id}', 
        json={'manually_ground_grams': None},
        headers={'Content-Type': 'application/json'})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['manually_ground_grams'] is None