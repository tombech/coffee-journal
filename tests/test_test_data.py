"""
Test that the test_data folder works correctly with the application.
"""
import pytest
import os
import tempfile
import shutil
from src.coffeejournal import create_app
from src.coffeejournal.repositories.factory import init_repository_factory, get_repository_factory


@pytest.fixture
def test_data_app():
    """Create app instance using test_data directory."""
    # Get absolute path to test_data directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_data_dir = os.path.join(project_root, 'test_data')
    
    # Ensure test_data directory exists
    if not os.path.exists(test_data_dir):
        pytest.skip("test_data directory not found. Run create_test_data.py first.")
    
    app = create_app({
        'TESTING': True,
        'DATA_DIR': test_data_dir,
        'SECRET_KEY': 'test-secret-key'
    })
    
    # Initialize repository factory with test data directory
    with app.app_context():
        init_repository_factory(
            storage_type='json',
            data_dir=test_data_dir
        )
    
    return app


@pytest.fixture
def test_data_client(test_data_app):
    """Test client using test_data."""
    return test_data_app.test_client()


@pytest.fixture
def test_data_repo_factory(test_data_app):
    """Repository factory using test_data."""
    with test_data_app.app_context():
        return get_repository_factory()


class TestTestDataIntegration:
    """Test that test_data integrates correctly with the application."""
    
    def test_roasters_loaded(self, test_data_repo_factory):
        """Test that roasters are loaded from test_data."""
        roaster_repo = test_data_repo_factory.get_roaster_repository()
        roasters = roaster_repo.find_all()
        
        assert len(roasters) >= 5
        roaster_names = [r['name'] for r in roasters]
        assert 'Blue Bottle Coffee' in roaster_names
        assert 'Intelligentsia Coffee' in roaster_names
        assert 'Stumptown Coffee Roasters' in roaster_names
    
    def test_bean_types_loaded(self, test_data_repo_factory):
        """Test that bean types are loaded from test_data."""
        bean_type_repo = test_data_repo_factory.get_bean_type_repository()
        bean_types = bean_type_repo.find_all()
        
        assert len(bean_types) >= 4
        bean_type_names = [bt['name'] for bt in bean_types]
        assert 'Arabica' in bean_type_names
        assert 'Robusta' in bean_type_names
    
    def test_countries_loaded(self, test_data_repo_factory):
        """Test that countries are loaded from test_data."""
        country_repo = test_data_repo_factory.get_country_repository()
        countries = country_repo.find_all()
        
        assert len(countries) >= 10
        country_names = [c['name'] for c in countries]
        assert 'Ethiopia' in country_names
        assert 'Colombia' in country_names
        assert 'Brazil' in country_names
    
    def test_brew_methods_loaded(self, test_data_repo_factory):
        """Test that brew methods are loaded from test_data."""
        brew_method_repo = test_data_repo_factory.get_brew_method_repository()
        brew_methods = brew_method_repo.find_all()
        
        assert len(brew_methods) >= 8
        brew_method_names = [bm['name'] for bm in brew_methods]
        assert 'V60' in brew_method_names
        assert 'Chemex' in brew_method_names
        assert 'French Press' in brew_method_names
    
    def test_recipes_loaded(self, test_data_repo_factory):
        """Test that recipes are loaded from test_data."""
        recipe_repo = test_data_repo_factory.get_recipe_repository()
        recipes = recipe_repo.find_all()
        
        assert len(recipes) >= 5
        recipe_names = [r['name'] for r in recipes]
        assert 'Standard V60' in recipe_names
        assert 'Tetsu Kasuya 4:6 Method' in recipe_names
    
    def test_products_loaded(self, test_data_repo_factory):
        """Test that products are loaded from test_data."""
        product_repo = test_data_repo_factory.get_product_repository()
        products = product_repo.find_all()
        
        assert len(products) >= 5
        
        # Check specific product details
        yirgacheffe = next((p for p in products if p.get('product_name') == 'Yirgacheffe Single Origin'), None)
        assert yirgacheffe is not None
        # Modern data structure stores only IDs, not names
        assert yirgacheffe['roaster_id'] == 1  # Blue Bottle Coffee
        assert yirgacheffe['bean_type_id'] == [1]  # Arabica
        assert yirgacheffe['country_id'] == 1  # Ethiopia
        assert yirgacheffe['roast_type'] == 3
    
    def test_batches_loaded(self, test_data_repo_factory):
        """Test that batches are loaded from test_data."""
        batch_repo = test_data_repo_factory.get_batch_repository()
        batches = batch_repo.find_all()
        
        assert len(batches) >= 6
        
        # Check that batches have required fields
        for batch in batches:
            assert 'id' in batch
            assert 'product_id' in batch
            assert 'roast_date' in batch
            assert batch['product_id'] is not None
    
    def test_brew_sessions_loaded(self, test_data_repo_factory):
        """Test that brew sessions are loaded from test_data."""
        session_repo = test_data_repo_factory.get_brew_session_repository()
        sessions = session_repo.find_all()
        
        assert len(sessions) >= 6
        
        # Check that sessions have required fields
        for session in sessions:
            assert 'id' in session
            assert 'product_id' in session
            assert 'product_batch_id' in session
            assert 'timestamp' in session
    
    def test_data_relationships(self, test_data_repo_factory):
        """Test that relationships between entities are maintained."""
        product_repo = test_data_repo_factory.get_product_repository()
        batch_repo = test_data_repo_factory.get_batch_repository()
        session_repo = test_data_repo_factory.get_brew_session_repository()
        
        # Get all data
        products = product_repo.find_all()
        batches = batch_repo.find_all()
        sessions = session_repo.find_all()
        
        # Check that all batches reference valid products
        product_ids = {p['id'] for p in products}
        for batch in batches:
            assert batch['product_id'] in product_ids
        
        # Check that all sessions reference valid batches and products
        batch_ids = {b['id'] for b in batches}
        for session in sessions:
            assert session['product_id'] in product_ids
            assert session['product_batch_id'] in batch_ids


class TestTestDataAPI:
    """Test API endpoints with test_data."""
    
    def test_get_products_api(self, test_data_client):
        """Test getting products via API."""
        response = test_data_client.get('/api/products')
        assert response.status_code == 200
        
        products = response.get_json()
        assert len(products) >= 5
        
        # Check that Blue Bottle Yirgacheffe is in the results
        yirgacheffe = next((p for p in products if p.get('product_name') == 'Yirgacheffe Single Origin'), None)
        assert yirgacheffe is not None
        assert yirgacheffe['roaster']['name'] == 'Blue Bottle Coffee'
    
    def test_get_batches_api(self, test_data_client):
        """Test getting batches via API using product endpoint."""
        # First get a product
        products_response = test_data_client.get('/api/products')
        assert products_response.status_code == 200
        products = products_response.get_json()
        assert len(products) > 0
        
        product_id = products[0]['id']
        response = test_data_client.get(f'/api/products/{product_id}/batches')
        assert response.status_code == 200
        
        batches = response.get_json()
        # Check that price_per_cup is calculated
        for batch in batches:
            if batch.get('price') and batch.get('amount_grams'):
                assert 'price_per_cup' in batch
    
    def test_get_brew_sessions_api(self, test_data_client):
        """Test getting brew sessions via API."""
        response = test_data_client.get('/api/brew_sessions')
        assert response.status_code == 200
        
        sessions = response.get_json()
        assert len(sessions) >= 6
        
        # Check that brew_ratio is calculated and product_details are included
        for session in sessions:
            if session.get('amount_coffee_grams') and session.get('amount_water_grams'):
                assert 'brew_ratio' in session
            assert 'product_details' in session
    
    def test_lookups_api(self, test_data_client):
        """Test lookup endpoints."""
        endpoints = [
            '/api/roasters',
            '/api/bean_types',
            '/api/countries',
            '/api/brew_methods',
            '/api/recipes'
        ]
        
        for endpoint in endpoints:
            response = test_data_client.get(endpoint)
            assert response.status_code == 200
            data = response.get_json()
            assert len(data) > 0
    
    def test_product_filtering(self, test_data_client):
        """Test product filtering with test data."""
        # Get all products first to find actual roasters
        all_response = test_data_client.get('/api/products')
        all_products = all_response.get_json()
        
        # Find a roaster that exists in the data
        if all_products:
            test_roaster = all_products[0]['roaster']['name']
            
            # Test roaster filter with existing roaster
            response = test_data_client.get(f'/api/products?roaster={test_roaster}')
            assert response.status_code == 200
            products = response.get_json()
            assert len(products) >= 1
            assert all(p['roaster']['name'] == test_roaster for p in products)
        
        # Test bean type filter
        response = test_data_client.get('/api/products?bean_type=Arabica')
        assert response.status_code == 200
        products = response.get_json()
        # Bean type filter should work correctly
        if products:
            assert all(any(bt['name'] == 'Arabica' for bt in p.get('bean_type', [])) for p in products)
    
    def test_product_batches_relationship(self, test_data_client):
        """Test getting batches for a specific product."""
        # First get a product ID
        response = test_data_client.get('/api/products')
        products = response.get_json()
        product_id = products[0]['id']
        
        # Get batches for this product
        response = test_data_client.get(f'/api/products/{product_id}/batches')
        assert response.status_code == 200
        batches = response.get_json()
        
        # All batches should belong to this product
        for batch in batches:
            assert batch['product_id'] == product_id


class TestDefaultConfiguration:
    """Test that the default configuration uses test_data."""
    
    def test_default_data_dir(self):
        """Test that the default DATA_DIR points to test_data."""
        # Clear any existing DATA_DIR environment variable to test default behavior
        original_data_dir = os.environ.get('DATA_DIR')
        if 'DATA_DIR' in os.environ:
            del os.environ['DATA_DIR']
        
        try:
            # Create app without explicit config
            app = create_app()
            
            # Check that DATA_DIR ends with test_data
            assert app.config['DATA_DIR'].endswith('test_data')
            
            # Check that the directory exists
            assert os.path.exists(app.config['DATA_DIR'])
        finally:
            # Restore original environment variable if it existed
            if original_data_dir is not None:
                os.environ['DATA_DIR'] = original_data_dir
    
    def test_env_var_override(self):
        """Test that DATA_DIR environment variable overrides default."""
        # Set environment variable
        test_dir = tempfile.mkdtemp()
        
        try:
            os.environ['DATA_DIR'] = test_dir
            
            # Create app
            app = create_app()
            
            # Check that DATA_DIR uses environment variable
            assert app.config['DATA_DIR'] == test_dir
            
        finally:
            # Clean up
            if 'DATA_DIR' in os.environ:
                del os.environ['DATA_DIR']
            shutil.rmtree(test_dir, ignore_errors=True)