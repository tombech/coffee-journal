"""
Test coffee age integration in API endpoints.
"""

import pytest
from datetime import datetime, timedelta
from coffeejournal import create_app
from coffeejournal.repositories.factory import get_repository_factory


class TestCoffeeAgeAPIIntegration:
    """Test that coffee age is properly calculated and included in API responses."""
    
    @pytest.fixture
    def app(self):
        """Create test app with in-memory storage."""
        app = create_app({'TESTING': True, 'DATA_DIR': ':memory:'})
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    @pytest.fixture
    def test_data(self, app):
        """Create test data for coffee age testing."""
        with app.app_context():
            factory = get_repository_factory()
            user_id = 'test_coffee_age_user'
            
            # Create a product
            product_data = {
                'product_name': 'Test Coffee for Age',
                'bean_type_id': [],
                'country_id': None,
                'region_id': [],
                'roaster_id': None,
                'decaf': False,
                'decaf_method_id': None
            }
            product = factory.get_product_repository(user_id).create(product_data)
            
            # Create a batch with known roast date
            roast_date = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')  # 2 weeks ago
            batch_data = {
                'product_id': product['id'],
                'roast_date': roast_date,
                'amount_grams': 250,
                'purchase_price': 15.99
            }
            batch = factory.get_batch_repository(user_id).create(batch_data)
            
            # Create a brewer for shot testing
            brewer_data = {
                'name': 'Test Espresso Machine',
                'description': 'Test machine for coffee age testing'
            }
            brewer = factory.get_brewer_repository(user_id).create(brewer_data)
            
            # Create a shot session
            session_data = {
                'title': 'Test Session for Coffee Age',
                'product_id': product['id'],
                'product_batch_id': batch['id'],
                'brewer_id': brewer['id']
            }
            shot_session = factory.get_shot_session_repository(user_id).create(session_data)
            
            return {
                'user_id': user_id,
                'product': product,
                'batch': batch,
                'brewer': brewer,
                'shot_session': shot_session,
                'roast_date': roast_date
            }
    
    def test_brew_sessions_include_coffee_age(self, client, test_data):
        """Test that brew sessions API includes coffee_age in response."""
        user_id = test_data['user_id']
        batch_id = test_data['batch']['id']
        
        # Create a brew session
        brew_session_data = {
            'brew_method': 'V60',
            'amount_coffee_grams': 20,
            'amount_water_grams': 320,
            'water_temp_celsius': 93,
            'notes': 'Test brew session for coffee age'
        }
        
        # Create brew session via API
        response = client.post(
            f'/api/batches/{batch_id}/brew_sessions?user_id={user_id}', 
            json=brew_session_data
        )
        assert response.status_code == 201
        
        # Get brew sessions and verify coffee_age is included
        response = client.get(f'/api/brew_sessions?user_id={user_id}&page_size=10')
        assert response.status_code == 200
        
        result = response.get_json()
        assert 'data' in result
        sessions = result['data']
        assert len(sessions) > 0
        
        # Find our test session
        test_session = None
        for session in sessions:
            if session.get('notes') == 'Test brew session for coffee age':
                test_session = session
                break
        
        assert test_session is not None
        assert 'coffee_age' in test_session
        assert test_session['coffee_age'] is not None
        
        # Should be "2 weeks" since we created batch 2 weeks ago
        assert 'week' in test_session['coffee_age']
    
    def test_individual_shots_include_coffee_age(self, client, test_data):
        """Test that individual shots API includes coffee_age in response."""
        user_id = test_data['user_id']
        batch = test_data['batch']
        brewer = test_data['brewer']
        
        # Create a shot
        shot_data = {
            'product_id': batch['product_id'],
            'product_batch_id': batch['id'],
            'brewer_id': brewer['id'],
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'extraction_time_seconds': 28,
            'water_temperature_c': 93,
            'notes': 'Test shot for coffee age'
        }
        
        # Create shot via API
        response = client.post(f'/api/shots?user_id={user_id}', json=shot_data)
        assert response.status_code == 201
        
        created_shot = response.get_json()
        assert 'coffee_age' in created_shot
        assert created_shot['coffee_age'] is not None
        assert 'week' in created_shot['coffee_age']
        
        # Also test getting shots list
        response = client.get(f'/api/shots?user_id={user_id}&page_size=10')
        assert response.status_code == 200
        
        result = response.get_json()
        assert 'data' in result
        shots = result['data']
        assert len(shots) > 0
        
        # Find our test shot
        test_shot = None
        for shot in shots:
            if shot.get('notes') == 'Test shot for coffee age':
                test_shot = shot
                break
        
        assert test_shot is not None
        assert 'coffee_age' in test_shot
        assert test_shot['coffee_age'] is not None
        assert 'week' in test_shot['coffee_age']
    
    def test_shot_sessions_include_coffee_age(self, client, test_data):
        """Test that shot sessions API includes coffee_age in response."""
        user_id = test_data['user_id']
        
        # Get shot sessions and verify coffee_age is included
        response = client.get(f'/api/shot_sessions?user_id={user_id}&page_size=10')
        assert response.status_code == 200
        
        result = response.get_json()
        assert 'data' in result
        sessions = result['data']
        assert len(sessions) > 0
        
        # Find our test session
        test_session = None
        for session in sessions:
            if session.get('title') == 'Test Session for Coffee Age':
                test_session = session
                break
        
        assert test_session is not None
        assert 'coffee_age' in test_session
        assert test_session['coffee_age'] is not None
        
        # Should be "2 weeks" since we created batch 2 weeks ago
        assert 'week' in test_session['coffee_age']
    
    def test_coffee_age_with_missing_batch(self, client, test_data):
        """Test coffee age calculation when batch info is missing."""
        user_id = test_data['user_id']
        brewer = test_data['brewer']
        
        # Create shot without batch
        shot_data = {
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'notes': 'Shot without batch for coffee age testing'
        }
        
        response = client.post(f'/api/shots?user_id={user_id}', json=shot_data)
        assert response.status_code == 201
        
        created_shot = response.get_json()
        # Should have coffee_age as None when no batch is available
        assert created_shot.get('coffee_age') is None
    
    def test_coffee_age_with_missing_roast_date(self, client, test_data):
        """Test coffee age calculation when roast date is missing."""
        user_id = test_data['user_id']
        product = test_data['product']
        brewer = test_data['brewer']
        
        # Create a batch without roast date
        batch_data = {
            'product_id': product['id'],
            'amount_grams': 250,
            'purchase_price': 15.99
            # No roast_date
        }
        
        with client.application.app_context():
            factory = get_repository_factory()
            batch = factory.get_batch_repository(user_id).create(batch_data)
        
        # Create shot with this batch
        shot_data = {
            'product_id': product['id'],
            'product_batch_id': batch['id'],
            'brewer_id': brewer['id'],
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'notes': 'Shot with batch but no roast date'
        }
        
        response = client.post(f'/api/shots?user_id={user_id}', json=shot_data)
        assert response.status_code == 201
        
        created_shot = response.get_json()
        # Should have coffee_age as None when roast date is missing
        assert created_shot.get('coffee_age') is None
    
    def test_coffee_age_formats(self, client, test_data):
        """Test different coffee age formats based on duration."""
        user_id = test_data['user_id']
        product = test_data['product']
        brewer = test_data['brewer']
        
        # Test cases: (days_ago, expected_format)
        test_cases = [
            (0, 'same day'),
            (1, '1 day'),
            (5, '5 days'),
            (7, '1 week'),
            (14, '2 weeks'),
            (35, '5 weeks')  # 35 days = 5 weeks
        ]
        
        for days_ago, expected_format in test_cases:
            # Create batch with specific roast date
            roast_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            batch_data = {
                'product_id': product['id'],
                'roast_date': roast_date,
                'amount_grams': 250,
                'purchase_price': 15.99
            }
            
            with client.application.app_context():
                factory = get_repository_factory()
                batch = factory.get_batch_repository(user_id).create(batch_data)
            
            # Create shot with this batch
            shot_data = {
                'product_id': product['id'],
                'product_batch_id': batch['id'],
                'brewer_id': brewer['id'],
                'dose_grams': 18.0,
                'yield_grams': 36.0,
                'notes': f'Shot for {days_ago} days age testing'
            }
            
            response = client.post(f'/api/shots?user_id={user_id}', json=shot_data)
            assert response.status_code == 201
            
            created_shot = response.get_json()
            coffee_age = created_shot.get('coffee_age')
            
            if expected_format == 'same day':
                assert coffee_age == expected_format
            elif 'day' in expected_format:
                assert expected_format in coffee_age
            elif 'week' in expected_format:
                assert expected_format in coffee_age