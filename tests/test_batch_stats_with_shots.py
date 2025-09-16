"""
Test batch statistics calculations including shots.
Tests that batch detail statistics properly account for coffee used in both brew sessions and shots.
"""
import pytest
import uuid
from datetime import datetime, timedelta


@pytest.fixture
def test_user_id():
    return f'test_batch_stats_{uuid.uuid4().hex[:8]}'


@pytest.fixture
def sample_data(client, test_user_id):
    """Create test data for batch statistics testing."""
    # Create roaster
    roaster_response = client.post(f'/api/roasters?user_id={test_user_id}', json={
        'name': 'Test Roaster Stats',
        'website': 'https://test-roaster.com'
    })
    assert roaster_response.status_code == 201
    roaster = roaster_response.get_json()

    # Create product
    product_response = client.post(f'/api/products?user_id={test_user_id}', json={
        'product_name': 'Test Product Stats',
        'roaster': 'Test Roaster Stats',
        'bean_type': ['Arabica'],
        'country': 'Ethiopia'
    })
    assert product_response.status_code == 201
    product = product_response.get_json()

    # Create batch with 500g of coffee
    batch_response = client.post(f'/api/products/{product["id"]}/batches?user_id={test_user_id}', json={
        'roast_date': '2024-12-01',
        'amount_grams': 500,
        'price': 25.00
    })
    assert batch_response.status_code == 201
    batch = batch_response.get_json()

    # Create equipment for brew sessions
    brewer_response = client.post(f'/api/brewers?user_id={test_user_id}', json={
        'name': 'V60',
        'type': 'Pour Over'
    })
    assert brewer_response.status_code == 201
    brewer = brewer_response.get_json()

    # Create equipment for shots
    espresso_machine_response = client.post(f'/api/brewers?user_id={test_user_id}', json={
        'name': 'Espresso Machine',
        'type': 'Espresso Machine'
    })
    assert espresso_machine_response.status_code == 201
    espresso_machine = espresso_machine_response.get_json()

    # Create grinder for shots
    grinder_response = client.post(f'/api/grinders?user_id={test_user_id}', json={
        'name': 'Test Grinder',
        'type': 'Burr',
        'burr_type': 'Flat'
    })
    assert grinder_response.status_code == 201
    grinder = grinder_response.get_json()

    data = {
        'roaster': roaster,
        'product': product,
        'batch': batch,
        'brewer': brewer,
        'espresso_machine': espresso_machine,
        'grinder': grinder
    }

    yield data

    # Cleanup
    client.delete(f'/api/test/cleanup/{test_user_id}')


def test_batch_stats_with_only_brew_sessions(client, test_user_id, sample_data):
    """Test batch statistics when only brew sessions exist."""
    # Create 2 brew sessions using 30g each (60g total)
    for i in range(2):
        session_data = {
            'datetime': datetime.now().isoformat(),
            'product_id': sample_data['product']['id'],
            'product_batch_id': sample_data['batch']['id'],
            'brewer_id': sample_data['brewer']['id'],
            'amount_coffee_grams': 30,
            'amount_water_grams': 500,
            'notes': f'Brew session {i+1}'
        }
        response = client.post(f'/api/batches/{sample_data["batch"]["id"]}/brew_sessions?user_id={test_user_id}',
                               json=session_data)
        assert response.status_code == 201

    # Get batch detail stats
    stats_response = client.get(f'/api/batches/{sample_data["batch"]["id"]}/detail?user_id={test_user_id}')
    assert stats_response.status_code == 200
    stats = stats_response.get_json()

    # Verify calculations
    assert stats['statistics']['total_brew_sessions'] == 2
    assert stats['statistics']['total_coffee_used'] == 60  # 30g * 2
    assert stats['statistics']['coffee_remaining'] == 440  # 500g - 60g
    assert stats['statistics']['sessions_remaining_estimate'] == 14  # 440g / 30g average


def test_batch_stats_with_only_shots(client, test_user_id, sample_data):
    """Test batch statistics when only shots exist."""
    # Create 5 shots using 18g each (90g total)
    for i in range(5):
        shot_data = {
            'timestamp': datetime.now().isoformat(),
            'product_id': sample_data['product']['id'],
            'product_batch_id': sample_data['batch']['id'],
            'brewer_id': sample_data['espresso_machine']['id'],
            'grinder_id': sample_data['grinder']['id'],
            'dose_grams': 18,
            'yield_grams': 36,
            'extraction_time_seconds': 28,
            'temperature_celsius': 93
        }
        response = client.post(f'/api/shots?user_id={test_user_id}', json=shot_data)
        assert response.status_code == 201

    # Get batch detail stats
    stats_response = client.get(f'/api/batches/{sample_data["batch"]["id"]}/detail?user_id={test_user_id}')
    assert stats_response.status_code == 200
    stats = stats_response.get_json()

    # Verify calculations include shots
    assert stats['statistics']['total_shots'] == 5
    assert stats['statistics']['total_coffee_used'] == 90  # 18g * 5
    assert stats['statistics']['coffee_remaining'] == 410  # 500g - 90g
    assert stats['statistics']['sessions_remaining_estimate'] == 22  # 410g / 18g average


def test_batch_stats_with_sessions_and_shots(client, test_user_id, sample_data):
    """Test batch statistics when both brew sessions and shots exist."""
    # Create 2 brew sessions using 30g each (60g total)
    for i in range(2):
        session_data = {
            'datetime': datetime.now().isoformat(),
            'product_id': sample_data['product']['id'],
            'product_batch_id': sample_data['batch']['id'],
            'brewer_id': sample_data['brewer']['id'],
            'amount_coffee_grams': 30,
            'amount_water_grams': 500,
            'notes': f'Brew session {i+1}'
        }
        response = client.post(f'/api/batches/{sample_data["batch"]["id"]}/brew_sessions?user_id={test_user_id}',
                               json=session_data)
        assert response.status_code == 201

    # Create 3 shots using 18g each (54g total)
    for i in range(3):
        shot_data = {
            'timestamp': datetime.now().isoformat(),
            'product_id': sample_data['product']['id'],
            'product_batch_id': sample_data['batch']['id'],
            'brewer_id': sample_data['espresso_machine']['id'],
            'grinder_id': sample_data['grinder']['id'],
            'dose_grams': 18,
            'yield_grams': 36,
            'extraction_time_seconds': 28,
            'temperature_celsius': 93
        }
        response = client.post(f'/api/shots?user_id={test_user_id}', json=shot_data)
        assert response.status_code == 201

    # Get batch detail stats
    stats_response = client.get(f'/api/batches/{sample_data["batch"]["id"]}/detail?user_id={test_user_id}')
    assert stats_response.status_code == 200
    stats = stats_response.get_json()

    # Verify calculations include both
    assert stats['statistics']['total_brew_sessions'] == 2
    assert stats['statistics']['total_shots'] == 3
    assert stats['statistics']['total_coffee_used'] == 114  # 60g + 54g
    assert stats['statistics']['coffee_remaining'] == 386  # 500g - 114g
    # Average per use: 114g / 5 uses = 22.8g, sessions remaining: 386 / 22.8 ≈ 16
    assert stats['statistics']['sessions_remaining_estimate'] == 16


def test_batch_stats_coffee_fully_used(client, test_user_id, sample_data):
    """Test batch statistics when all coffee has been used."""
    # Use all 500g through a combination of sessions and shots
    # 10 brew sessions at 30g = 300g
    for i in range(10):
        session_data = {
            'datetime': datetime.now().isoformat(),
            'product_id': sample_data['product']['id'],
            'product_batch_id': sample_data['batch']['id'],
            'brewer_id': sample_data['brewer']['id'],
            'amount_coffee_grams': 30,
            'amount_water_grams': 500,
            'notes': f'Brew session {i+1}'
        }
        response = client.post(f'/api/batches/{sample_data["batch"]["id"]}/brew_sessions?user_id={test_user_id}',
                               json=session_data)
        assert response.status_code == 201

    # 11 shots at 18g = 198g (plus 2g from an extra shot)
    for i in range(11):
        dose = 20 if i == 10 else 18  # Last shot uses 20g to reach 500g total
        shot_data = {
            'timestamp': datetime.now().isoformat(),
            'product_id': sample_data['product']['id'],
            'product_batch_id': sample_data['batch']['id'],
            'brewer_id': sample_data['espresso_machine']['id'],
            'grinder_id': sample_data['grinder']['id'],
            'dose_grams': dose,
            'yield_grams': dose * 2,
            'extraction_time_seconds': 28,
            'temperature_celsius': 93
        }
        response = client.post(f'/api/shots?user_id={test_user_id}', json=shot_data)
        assert response.status_code == 201

    # Get batch detail stats
    stats_response = client.get(f'/api/batches/{sample_data["batch"]["id"]}/detail?user_id={test_user_id}')
    assert stats_response.status_code == 200
    stats = stats_response.get_json()

    # Verify calculations
    assert stats['statistics']['total_brew_sessions'] == 10
    assert stats['statistics']['total_shots'] == 11
    assert stats['statistics']['total_coffee_used'] == 500  # All used
    assert stats['statistics']['coffee_remaining'] == 0  # Nothing left
    assert stats['statistics']['sessions_remaining_estimate'] == 0  # No sessions left