"""
Test to reproduce the shot session product batch not saving bug.
This test verifies the exact scenario described in the bug report.
"""
import pytest
import uuid
from coffeejournal.repositories.factory import get_repository_factory


@pytest.fixture
def test_user_id():
    return f'test_batch_bug_{uuid.uuid4().hex[:8]}'


@pytest.fixture  
def sample_data(client, test_user_id):
    """Create test data for the shot session batch bug reproduction."""
    # Create roaster
    roaster_response = client.post(f'/api/roasters?user_id={test_user_id}', json={
        'name': 'Test Roaster Batch Bug',
        'website': 'https://test-roaster.com'
    })
    assert roaster_response.status_code == 201
    roaster = roaster_response.get_json()
    
    # Create product
    product_response = client.post(f'/api/products?user_id={test_user_id}', json={
        'product_name': 'Test Product Batch Bug',
        'roaster': 'Test Roaster Batch Bug',
        'bean_type': ['Arabica'],
        'country': 'Ethiopia'
    })
    assert product_response.status_code == 201
    product = product_response.get_json()
    
    # Create two batches for this product
    batch1_response = client.post(f'/api/products/{product["id"]}/batches?user_id={test_user_id}', json={
        'roast_date': '2024-12-01',
        'amount_grams': 250,
        'price': 15.99
    })
    assert batch1_response.status_code == 201
    batch1 = batch1_response.get_json()
    
    batch2_response = client.post(f'/api/products/{product["id"]}/batches?user_id={test_user_id}', json={
        'roast_date': '2024-12-15', 
        'amount_grams': 250,
        'price': 16.99
    })
    assert batch2_response.status_code == 201
    batch2 = batch2_response.get_json()
    
    # Create brewer
    brewer_response = client.post(f'/api/brewers?user_id={test_user_id}', json={
        'name': 'Test Brewer Batch Bug',
        'type': 'Espresso Machine'
    })
    assert brewer_response.status_code == 201
    brewer = brewer_response.get_json()
    
    data = {
        'roaster': roaster,
        'product': product,
        'batch1': batch1,
        'batch2': batch2,
        'brewer': brewer
    }
    
    yield data
    
    # Cleanup
    client.delete(f'/api/test/cleanup/{test_user_id}')


def test_shot_session_create_with_batch_persistence(client, test_user_id, sample_data):
    """Test that creating a shot session with a product batch persists correctly."""
    # Create shot session with batch1
    session_data = {
        'title': 'Test Session With Batch1',
        'product_id': sample_data['product']['id'],
        'product_batch_id': sample_data['batch1']['id'],
        'brewer_id': sample_data['brewer']['id'],
        'notes': 'Initial session with batch1'
    }
    
    response = client.post(f'/api/shot_sessions?user_id={test_user_id}', json=session_data)
    assert response.status_code == 201
    
    created_session = response.get_json()
    assert created_session['product_batch_id'] == sample_data['batch1']['id']
    
    # Verify by fetching the session
    get_response = client.get(f'/api/shot_sessions/{created_session["id"]}?user_id={test_user_id}')
    assert get_response.status_code == 200
    
    retrieved_session = get_response.get_json()
    assert retrieved_session['product_batch_id'] == sample_data['batch1']['id']
    assert retrieved_session['product_batch']['id'] == sample_data['batch1']['id']
    assert retrieved_session['product_batch']['roast_date'] == '2024-12-01'


def test_shot_session_edit_change_batch_persistence(client, test_user_id, sample_data):
    """Test that editing a shot session and changing the batch persists correctly."""
    # Create shot session with batch1
    session_data = {
        'title': 'Test Session Initial Batch',
        'product_id': sample_data['product']['id'],
        'product_batch_id': sample_data['batch1']['id'],
        'brewer_id': sample_data['brewer']['id'],
        'notes': 'Initial session with batch1'
    }
    
    create_response = client.post(f'/api/shot_sessions?user_id={test_user_id}', json=session_data)
    assert create_response.status_code == 201
    created_session = create_response.get_json()
    
    # Verify initial batch
    assert created_session['product_batch_id'] == sample_data['batch1']['id']
    
    # Edit the session to change to batch2
    update_data = {
        'title': 'Test Session Updated Batch',
        'product_id': sample_data['product']['id'],
        'product_batch_id': sample_data['batch2']['id'],  # Change to batch2
        'brewer_id': sample_data['brewer']['id'],
        'notes': 'Updated session with batch2'
    }
    
    update_response = client.put(
        f'/api/shot_sessions/{created_session["id"]}?user_id={test_user_id}', 
        json=update_data
    )
    assert update_response.status_code == 200
    
    updated_session = update_response.get_json()
    
    # Verify the batch was changed to batch2
    assert updated_session['product_batch_id'] == sample_data['batch2']['id']
    
    # Verify by fetching the session again
    get_response = client.get(f'/api/shot_sessions/{created_session["id"]}?user_id={test_user_id}')
    assert get_response.status_code == 200
    
    final_session = get_response.get_json()
    assert final_session['product_batch_id'] == sample_data['batch2']['id']
    assert final_session['product_batch']['id'] == sample_data['batch2']['id']
    assert final_session['product_batch']['roast_date'] == '2024-12-15'  # batch2's date
    assert final_session['title'] == 'Test Session Updated Batch'


def test_shot_session_edit_partial_update_preserves_batch(client, test_user_id, sample_data):
    """Test that partial updates (not including product_batch_id) preserve the existing batch."""
    # Create shot session with batch1
    session_data = {
        'title': 'Test Session Partial Update',
        'product_id': sample_data['product']['id'],
        'product_batch_id': sample_data['batch1']['id'],
        'brewer_id': sample_data['brewer']['id'],
        'notes': 'Initial session'
    }
    
    create_response = client.post(f'/api/shot_sessions?user_id={test_user_id}', json=session_data)
    assert create_response.status_code == 201
    created_session = create_response.get_json()
    
    # Update only title and notes, not including product_batch_id
    partial_update = {
        'title': 'Updated Title Only',
        'notes': 'Updated notes only'
    }
    
    update_response = client.put(
        f'/api/shot_sessions/{created_session["id"]}?user_id={test_user_id}', 
        json=partial_update
    )
    assert update_response.status_code == 200
    
    updated_session = update_response.get_json()
    
    # The batch should still be preserved even though it wasn't included in the update
    assert updated_session['product_batch_id'] == sample_data['batch1']['id']
    assert updated_session['title'] == 'Updated Title Only'
    assert updated_session['notes'] == 'Updated notes only'