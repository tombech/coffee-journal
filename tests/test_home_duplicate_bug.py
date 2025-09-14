"""Test for Home page duplicate action bug."""
import pytest
from coffeejournal import create_app


class TestHomeDuplicateBug:
    """Test that the duplicate action on Home page works correctly."""
    
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
    def sample_brew_session(self, client):
        """Create a sample brew session for testing."""
        # Create a product first
        product_response = client.post('/api/products', json={
            'product_name': 'Test Coffee',
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
        
        # Create a brew session
        session_response = client.post(f'/api/batches/{batch["id"]}/brew_sessions', json={
            'brew_method': 'V60',
            'amount_coffee_grams': 20.0,
            'amount_water_grams': 320.0,
            'water_temp_celsius': 93,
            'brew_time_seconds': 180,
            'sweetness': 8,
            'acidity': 7,
            'body': 6,
            'aroma': 8,
            'bitterness': 3,
            'score': 7.5
        })
        assert session_response.status_code == 201
        return session_response.get_json()
    
    def test_home_duplicate_endpoint_404(self, client, sample_brew_session):
        """Test that calling the incorrect duplicate endpoint returns 404."""
        # This is what the Home component currently does (incorrect)
        response = client.post(f'/api/brew_sessions/{sample_brew_session["id"]}/duplicate')
        
        # This should fail with 404 because the endpoint doesn't exist
        assert response.status_code == 404, "Expected 404 for incorrect duplicate endpoint"
    
    def test_correct_duplicate_endpoint_works(self, client, sample_brew_session):
        """Test that the correct duplicate endpoint works."""
        # The correct endpoint includes the batch_id
        batch_id = sample_brew_session['product_batch_id']
        session_id = sample_brew_session['id']
        
        response = client.post(f'/api/batches/{batch_id}/brew_sessions/{session_id}/duplicate')
        
        # This should work
        assert response.status_code == 201, f"Expected 201 for correct duplicate endpoint, got {response.status_code}"
        
        duplicated = response.get_json()
        assert duplicated['id'] != sample_brew_session['id']
        assert duplicated['product_batch_id'] == sample_brew_session['product_batch_id']
        # Check the brew_method_id instead since brew_method is an enriched field
        assert duplicated['brew_method_id'] == sample_brew_session['brew_method_id']
    
    def test_home_page_sessions_have_product_batch_id(self, client, sample_brew_session):
        """Test that sessions returned by the home page API have product_batch_id."""
        # This is the endpoint the Home component calls
        response = client.get('/api/brew_sessions?page_size=15')
        assert response.status_code == 200
        
        result = response.get_json()
        sessions = result.get('data', [])
        assert len(sessions) > 0, "Should have at least one session"
        
        session = sessions[0]
        assert 'product_batch_id' in session, "Session should have product_batch_id for duplicate functionality"
        assert session['product_batch_id'] is not None, "product_batch_id should not be None"