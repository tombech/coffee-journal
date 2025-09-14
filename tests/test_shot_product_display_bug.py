"""Test for shot product display bug in ShotTable."""
import pytest
from coffeejournal import create_app


class TestShotProductDisplayBug:
    """Test that shot product information is displayed correctly."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        import tempfile
        temp_dir = tempfile.mkdtemp()
        app = create_app({
            'TESTING': True,
            'DATA_DIR': temp_dir,
            'SECRET_KEY': 'test-secret'
        })
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def sample_shot(self, client):
        """Create a sample shot for testing."""
        # Create a product first
        product_response = client.post('/api/products', json={
            'product_name': 'Test Espresso',
            'roaster': 'Test Roaster',
            'bean_type': ['Arabica'],
            'country': 'Ethiopia'
        })
        assert product_response.status_code == 201
        product = product_response.get_json()
        
        # Create a batch
        batch_response = client.post(f'/api/products/{product["id"]}/batches', json={
            'roast_date': '2025-01-01',
            'amount_grams': 250,
            'price': 15.99
        })
        assert batch_response.status_code == 201
        batch = batch_response.get_json()
        
        # Create a brewer
        brewer_response = client.post('/api/brewers', json={
            'name': 'Test Machine',
            'manufacturer': 'Test Manufacturer'
        })
        assert brewer_response.status_code == 201
        brewer = brewer_response.get_json()
        
        # Create a shot session
        session_response = client.post('/api/shot_sessions', json={
            'title': 'Test Session',
            'product_id': product['id'],
            'product_batch_id': batch['id'],
            'brewer_id': brewer['id']
        })
        assert session_response.status_code == 201
        session = session_response.get_json()
        
        # Create a shot
        shot_response = client.post('/api/shots', json={
            'shot_session_id': session['id'],
            'product_id': product['id'],
            'product_batch_id': batch['id'],
            'brewer_id': brewer['id'],
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'extraction_time_seconds': 28,
            'water_temperature_c': 93,
            'overall_score': 8.0
        })
        assert shot_response.status_code == 201
        return shot_response.get_json()
    
    def test_shot_api_returns_product_field(self, client, sample_shot):
        """Test that the shots API returns product field correctly."""
        # Get the shot via API
        response = client.get(f'/api/shots?page_size=5&sort=overall_score&sort_direction=desc')
        assert response.status_code == 200
        
        result = response.get_json()
        assert 'data' in result
        assert len(result['data']) > 0
        
        shot = result['data'][0]
        
        # Check that product field exists
        assert 'product' in shot, "Shot should have 'product' field"
        assert 'product_name' in shot, "Shot should have 'product_name' field"
        
        # Check that product has the expected structure
        assert shot['product'] is not None
        assert 'product_name' in shot['product']
        assert shot['product']['product_name'] == 'Test Espresso'
        
        # Check that product_name is also available at top level
        assert shot['product_name'] == 'Test Espresso'
    
    def test_shot_product_details_field_present(self, client, sample_shot):
        """Test that product_details field is now present for frontend compatibility."""
        # Get the shot via API
        response = client.get(f'/api/shots?page_size=5&sort=overall_score&sort_direction=desc')
        assert response.status_code == 200
        
        result = response.get_json()
        shot = result['data'][0]
        
        # Both fields should now be present
        assert 'product' in shot, "Shot should have 'product' field"
        assert 'product_details' in shot, "Shot should have 'product_details' field for frontend"
        
        # They should be the same object
        assert shot['product'] == shot['product_details'], "Both fields should contain the same product data"