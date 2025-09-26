"""
Test grinder scores over time endpoint.
"""

import pytest
import uuid
import tempfile
from datetime import datetime, timedelta
from coffeejournal import create_app


class TestGrinderScoresEndpoint:
    """Test grinder scores over time endpoint."""

    @pytest.fixture
    def app(self):
        """Create app with test configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            app = create_app({
                'TESTING': True,
                'DATA_DIR': temp_dir
            })
            with app.app_context():
                yield app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @pytest.fixture
    def test_user_id(self):
        """Generate a unique test user ID."""
        return f'test_user_{uuid.uuid4().hex[:8]}'

    @pytest.fixture
    def sample_grinder(self, client, test_user_id):
        """Create a sample grinder."""
        grinder_data = {
            'name': 'Test Grinder',
            'brand': 'Test Brand',
            'grinder_type': 'Flat Burr'
        }
        response = client.post(
            f'/api/grinders?user_id={test_user_id}',
            json=grinder_data
        )
        assert response.status_code == 201
        return response.get_json()

    @pytest.fixture
    def sample_product(self, client, test_user_id):
        """Create a sample product."""
        # Create required lookups first
        roaster_response = client.post(
            f'/api/roasters?user_id={test_user_id}',
            json={'name': 'Test Roaster'}
        )
        assert roaster_response.status_code == 201
        roaster_id = roaster_response.get_json()['id']

        bean_type_response = client.post(
            f'/api/bean_types?user_id={test_user_id}',
            json={'name': 'Arabica'}
        )
        assert bean_type_response.status_code == 201
        bean_type_id = bean_type_response.get_json()['id']

        country_response = client.post(
            f'/api/countries?user_id={test_user_id}',
            json={'name': 'Ethiopia'}
        )
        assert country_response.status_code == 201
        country_id = country_response.get_json()['id']

        product_data = {
            'name': 'Test Coffee',
            'roaster_id': roaster_id,
            'bean_type_id': [bean_type_id],
            'country_id': country_id,
            'region_id': [],
        }
        response = client.post(
            f'/api/products?user_id={test_user_id}',
            json=product_data
        )
        assert response.status_code == 201
        return response.get_json()

    @pytest.fixture
    def sample_batch(self, client, sample_product, test_user_id):
        """Create a sample batch."""
        batch_data = {
            'roast_date': '2024-01-01',
            'price': 15.00,
            'weight_grams': 250
        }
        response = client.post(
            f'/api/products/{sample_product["id"]}/batches?user_id={test_user_id}',
            json=batch_data
        )
        assert response.status_code == 201
        return response.get_json()

    def test_grinder_scores_over_time_no_sessions(self, client, sample_grinder, test_user_id):
        """Test getting scores when there are no brew sessions."""
        response = client.get(
            f'/api/grinders/{sample_grinder["id"]}/scores-over-time?user_id={test_user_id}'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'grinder_name' in data
        assert data['grinder_name'] == 'Test Grinder'
        assert 'data' in data
        assert data['data'] == []

    def test_grinder_scores_over_time_with_sessions(self, client, sample_grinder, sample_batch, test_user_id):
        """Test getting scores with multiple brew sessions."""
        # Create brew method first
        brew_method_response = client.post(
            f'/api/brew_methods?user_id={test_user_id}',
            json={'name': 'V60'}
        )
        assert brew_method_response.status_code == 201
        brew_method_id = brew_method_response.get_json()['id']

        # Create several brew sessions with different scores
        base_date = datetime.now() - timedelta(days=10)
        scores = [7.5, 8.0, 6.5, 9.0, 8.5, 7.0, 9.5]

        for i, score in enumerate(scores):
            session_data = {
                'timestamp': (base_date + timedelta(days=i)).isoformat(),
                'grinder_id': sample_grinder['id'],
                'grinder_setting': 15,
                'brew_method_id': brew_method_id,
                'water_grams': 200,
                'coffee_grams': 12,
                'water_temp': 93,
                'total_time': 180,
                'score': score,
                'notes': f'Test session {i+1}'
            }
            response = client.post(
                f'/api/batches/{sample_batch["id"]}/brew_sessions?user_id={test_user_id}',
                json=session_data
            )
            assert response.status_code == 201

        # Get the scores over time
        response = client.get(
            f'/api/grinders/{sample_grinder["id"]}/scores-over-time?user_id={test_user_id}'
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify the response structure
        assert 'grinder_name' in data
        assert data['grinder_name'] == 'Test Grinder'
        assert 'data' in data
        assert len(data['data']) == 7

        # Verify the sessions are in chronological order
        for i, session_data in enumerate(data['data']):
            assert 'date' in session_data
            assert 'timestamp' in session_data
            assert 'score' in session_data
            assert 'product_name' in session_data
            assert 'brew_method' in session_data
            assert session_data['score'] == scores[i]

        # Verify timestamps are in ascending order
        timestamps = [s['timestamp'] for s in data['data']]
        assert timestamps == sorted(timestamps)

    def test_grinder_scores_over_time_filter_nulls(self, client, sample_grinder, sample_batch, test_user_id):
        """Test that sessions without scores are filtered out."""
        # Create brew method first
        brew_method_response = client.post(
            f'/api/brew_methods?user_id={test_user_id}',
            json={'name': 'V60'}
        )
        assert brew_method_response.status_code == 201
        brew_method_id = brew_method_response.get_json()['id']

        # Create sessions with and without scores
        sessions_data = [
            {'score': 8.0, 'notes': 'Session with score'},
            {'score': None, 'notes': 'Session without score'},
            {'score': 7.5, 'notes': 'Another scored session'}
        ]

        for i, session_info in enumerate(sessions_data):
            session_data = {
                'timestamp': (datetime.now() - timedelta(days=len(sessions_data) - i)).isoformat(),
                'grinder_id': sample_grinder['id'],
                'grinder_setting': 15,
                'brew_method_id': brew_method_id,
                'water_grams': 200,
                'coffee_grams': 12,
                'water_temp': 93,
                'total_time': 180,
                'notes': session_info['notes']
            }
            if session_info['score'] is not None:
                session_data['score'] = session_info['score']

            response = client.post(
                f'/api/batches/{sample_batch["id"]}/brew_sessions?user_id={test_user_id}',
                json=session_data
            )
            assert response.status_code == 201

        # Get the scores over time
        response = client.get(
            f'/api/grinders/{sample_grinder["id"]}/scores-over-time?user_id={test_user_id}'
        )

        assert response.status_code == 200
        data = response.get_json()

        # Should only have 2 sessions (the ones with scores)
        assert len(data['data']) == 2
        assert data['data'][0]['score'] == 8.0
        assert data['data'][1]['score'] == 7.5

    def test_grinder_scores_over_time_invalid_grinder(self, client, test_user_id):
        """Test getting scores for a non-existent grinder."""
        response = client.get(
            f'/api/grinders/999999/scores-over-time?user_id={test_user_id}'
        )

        assert response.status_code == 404
        assert 'error' in response.get_json()
        assert 'Grinder not found' in response.get_json()['error']

    def test_grinder_scores_over_time_different_grinders(self, client, test_user_id, sample_batch):
        """Test that scores are properly filtered by grinder."""
        # Create brew method first
        brew_method_response = client.post(
            f'/api/brew_methods?user_id={test_user_id}',
            json={'name': 'V60'}
        )
        assert brew_method_response.status_code == 201
        brew_method_id = brew_method_response.get_json()['id']

        # Create two grinders
        grinder1_data = {'name': 'Grinder 1'}
        grinder2_data = {'name': 'Grinder 2'}

        response1 = client.post(
            f'/api/grinders?user_id={test_user_id}',
            json=grinder1_data
        )
        response2 = client.post(
            f'/api/grinders?user_id={test_user_id}',
            json=grinder2_data
        )

        grinder1 = response1.get_json()
        grinder2 = response2.get_json()

        # Create sessions for both grinders
        base_timestamp = datetime.now() - timedelta(days=3)
        for idx, (grinder_id, score) in enumerate([(grinder1['id'], 8.0), (grinder2['id'], 7.0), (grinder1['id'], 9.0)]):
            session_data = {
                'timestamp': (base_timestamp + timedelta(days=idx)).isoformat(),
                'grinder_id': grinder_id,
                'grinder_setting': 15,
                'brew_method_id': brew_method_id,
                'water_grams': 200,
                'coffee_grams': 12,
                'water_temp': 93,
                'total_time': 180,
                'score': score
            }
            response = client.post(
                f'/api/batches/{sample_batch["id"]}/brew_sessions?user_id={test_user_id}',
                json=session_data
            )
            assert response.status_code == 201

        # Get scores for grinder 1
        response = client.get(
            f'/api/grinders/{grinder1["id"]}/scores-over-time?user_id={test_user_id}'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 2
        assert data['data'][0]['score'] == 8.0
        assert data['data'][1]['score'] == 9.0

        # Get scores for grinder 2
        response = client.get(
            f'/api/grinders/{grinder2["id"]}/scores-over-time?user_id={test_user_id}'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['data']) == 1
        assert data['data'][0]['score'] == 7.0