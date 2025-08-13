"""
Tests for shot dose-yield ratio and score calculations.
These tests verify the fixes for missing ratio and score display in shots API.
"""

import pytest
from coffeejournal import create_app
from coffeejournal.repositories.factory import get_repository_factory


@pytest.fixture
def app():
    """Create test app."""
    return create_app({'TESTING': True, 'DATA_DIR': '/tmp/test_shot_calcs'})


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def test_user_id():
    """Generate test user ID."""
    import uuid
    return f'test_shot_calcs_{uuid.uuid4().hex[:8]}'


@pytest.fixture
def sample_data(client, test_user_id):
    """Create sample test data."""
    # Create product
    product_response = client.post('/api/products', json={
        'product_name': 'Test Espresso Beans',
        'roaster': 'Test Roaster',
        'bean_type': ['Arabica'],
        'country': 'Colombia'
    }, query_string={'user_id': test_user_id})
    product = product_response.get_json()
    
    # Create batch
    batch_response = client.post(f'/api/products/{product["id"]}/batches', json={
        'roast_date': '2024-01-15',
        'amount_grams': 250,
        'price': 18.50
    }, query_string={'user_id': test_user_id})
    batch = batch_response.get_json()
    
    # Create brewer
    brewer_response = client.post('/api/brewers', json={
        'name': 'Test Espresso Machine',
        'type': 'Semi-automatic'
    }, query_string={'user_id': test_user_id})
    brewer = brewer_response.get_json()
    
    yield {
        'product': product,
        'batch': batch,
        'brewer': brewer,
        'user_id': test_user_id
    }
    
    # Cleanup
    client.delete(f'/api/test/cleanup/{test_user_id}')


class TestShotRatioCalculations:
    """Test dose-yield ratio calculations."""
    
    def test_dose_yield_ratio_calculation(self, client, sample_data):
        """Test that dose-yield ratio is calculated correctly."""
        user_id = sample_data['user_id']
        batch_id = sample_data['batch']['id']
        brewer_id = sample_data['brewer']['id']
        
        # Create shot with known dose and yield
        shot_data = {
            'product_batch_id': batch_id,
            'brewer_id': brewer_id,
            'dose_grams': 18.0,
            'yield_grams': 36.0,  # Should give 1:2.0 ratio
            'extraction_time_seconds': 28,
            'sweetness': 7,
            'acidity': 6,
            'body': 8
        }
        
        response = client.post('/api/shots', json=shot_data, query_string={'user_id': user_id})
        assert response.status_code == 201
        shot = response.get_json()
        
        # Get the shot back to check enrichment
        get_response = client.get(f'/api/shots/{shot["id"]}', query_string={'user_id': user_id})
        assert get_response.status_code == 200
        enriched_shot = get_response.get_json()
        
        # Verify ratio calculation
        assert 'dose_yield_ratio' in enriched_shot
        assert enriched_shot['dose_yield_ratio'] == 2.0  # 36 / 18 = 2.0
    
    def test_dose_yield_ratio_with_decimals(self, client, sample_data):
        """Test ratio calculation with decimal values."""
        user_id = sample_data['user_id']
        batch_id = sample_data['batch']['id']
        brewer_id = sample_data['brewer']['id']
        
        shot_data = {
            'product_batch_id': batch_id,
            'brewer_id': brewer_id,
            'dose_grams': 18.5,
            'yield_grams': 37.8,  # Should give ~2.04 → 2.0 (rounded)
            'extraction_time_seconds': 30
        }
        
        response = client.post('/api/shots', json=shot_data, query_string={'user_id': user_id})
        assert response.status_code == 201
        shot = response.get_json()
        
        get_response = client.get(f'/api/shots/{shot["id"]}', query_string={'user_id': user_id})
        enriched_shot = get_response.get_json()
        
        # 37.8 / 18.5 = 2.043... should round to 2.0
        assert enriched_shot['dose_yield_ratio'] == 2.0
    
    def test_dose_yield_ratio_zero_dose(self, client, sample_data):
        """Test ratio calculation with zero dose (edge case)."""
        user_id = sample_data['user_id']
        batch_id = sample_data['batch']['id']
        brewer_id = sample_data['brewer']['id']
        
        # Shot with zero dose (edge case)
        shot_data = {
            'product_batch_id': batch_id,
            'brewer_id': brewer_id,
            'dose_grams': 0.0,  # Zero dose
            'yield_grams': 36.0,
            'extraction_time_seconds': 28
        }
        
        response = client.post('/api/shots', json=shot_data, query_string={'user_id': user_id})
        assert response.status_code == 201
        shot = response.get_json()
        
        get_response = client.get(f'/api/shots/{shot["id"]}', query_string={'user_id': user_id})
        enriched_shot = get_response.get_json()
        
        # Should be None when dose is zero (can't divide by zero)
        assert enriched_shot['dose_yield_ratio'] is None


class TestShotScoreCalculations:
    """Test shot score calculations."""
    
    def test_calculated_score_from_components(self, client, sample_data):
        """Test that calculated_score is computed from taste components."""
        user_id = sample_data['user_id']
        batch_id = sample_data['batch']['id']
        brewer_id = sample_data['brewer']['id']
        
        # Create shot with known taste components
        shot_data = {
            'product_batch_id': batch_id,
            'brewer_id': brewer_id,
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'sweetness': 8,
            'acidity': 7,
            'body': 6,
            'aroma': 9,
            'bitterness': 2,  # Will be inverted to 8 (10-2)
            'flavor_profile_match': 7
        }
        
        response = client.post('/api/shots', json=shot_data, query_string={'user_id': user_id})
        assert response.status_code == 201
        shot = response.get_json()
        
        get_response = client.get(f'/api/shots/{shot["id"]}', query_string={'user_id': user_id})
        enriched_shot = get_response.get_json()
        
        # Verify calculated score
        assert 'calculated_score' in enriched_shot
        
        # Manual calculation: (8+7+6+9+8+7)/6 = 45/6 = 7.5
        expected_score = 7.5
        assert enriched_shot['calculated_score'] == expected_score
    
    def test_calculated_score_with_manual_score(self, client, sample_data):
        """Test that manual score takes precedence over calculated."""
        user_id = sample_data['user_id']
        batch_id = sample_data['batch']['id']
        brewer_id = sample_data['brewer']['id']
        
        shot_data = {
            'product_batch_id': batch_id,
            'brewer_id': brewer_id,
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'score': 8.5,  # Manual score
            'sweetness': 5,  # Lower taste components
            'acidity': 4
        }
        
        response = client.post('/api/shots', json=shot_data, query_string={'user_id': user_id})
        shot = response.get_json()
        
        get_response = client.get(f'/api/shots/{shot["id"]}', query_string={'user_id': user_id})
        enriched_shot = get_response.get_json()
        
        # Should use manual score, not calculated from components
        assert enriched_shot['calculated_score'] == 8.5


class TestShotsListAPI:
    """Test shots list API includes ratio and score."""
    
    def test_shots_list_includes_calculations(self, client, sample_data):
        """Test that shots list API includes ratio and score calculations."""
        user_id = sample_data['user_id']
        batch_id = sample_data['batch']['id']
        brewer_id = sample_data['brewer']['id']
        
        # Create multiple shots with different ratios
        shots_data = [
            {
                'product_batch_id': batch_id,
                'brewer_id': brewer_id,
                'dose_grams': 18.0,
                'yield_grams': 36.0,  # 1:2.0
                'sweetness': 8,
                'acidity': 7
            },
            {
                'product_batch_id': batch_id,
                'brewer_id': brewer_id,
                'dose_grams': 20.0,
                'yield_grams': 50.0,  # 1:2.5
                'sweetness': 6,
                'acidity': 5
            }
        ]
        
        for shot_data in shots_data:
            response = client.post('/api/shots', json=shot_data, query_string={'user_id': user_id})
            assert response.status_code == 201
        
        # Get shots list
        list_response = client.get('/api/shots', query_string={'user_id': user_id})
        assert list_response.status_code == 200
        
        result = list_response.get_json()
        shots = result.get('data', [])
        assert len(shots) >= 2
        
        # Check that all shots have ratio and score
        for shot in shots:
            assert 'dose_yield_ratio' in shot
            assert 'calculated_score' in shot
            if shot.get('dose_grams') and shot.get('yield_grams'):
                assert shot['dose_yield_ratio'] is not None
            assert shot['calculated_score'] is not None
    
    def test_shots_filter_options_api(self, client, sample_data):
        """Test that shots filter options API works."""
        user_id = sample_data['user_id']
        
        response = client.get('/api/shots/filter_options', query_string={'user_id': user_id})
        assert response.status_code == 200
        
        options = response.get_json()
        assert isinstance(options, dict)
        # Should have filter categories
        assert 'products' in options or 'brewers' in options