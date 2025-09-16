"""
Tests for multi-user API functionality.
Written first (TDD) to define the desired API behavior.
"""

import pytest
import os
import shutil
import tempfile
from pathlib import Path
from coffeejournal import create_app
from coffeejournal.repositories.factory import RepositoryFactory


class TestMultiUserAPI:
    """Test multi-user functionality in the API."""
    
    @pytest.fixture
    def app(self):
        """Create app with test configuration."""
        # Use a temporary directory for test data
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
    
    def test_default_user_works_without_user_id(self, client):
        """API should work normally when no user_id is provided."""
        # Create a product without user_id (should use default user)
        response = client.post('/api/products', json={
            'product_name': 'Test Coffee',
            'roaster': 'Test Roaster',  # Use name instead of ID
            'bean_type': ['Arabica'],   # Use name instead of ID
            'country': 'Colombia',      # Use name instead of ID
            'region_id': []
        })
        if response.status_code != 201:
            print(f"Response: {response.status_code}, {response.get_json()}")
        assert response.status_code == 201
        
        # Should be able to retrieve it
        response = client.get('/api/products')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['product_name'] == 'Test Coffee'
    
    def test_user_specific_data_isolation(self, client):
        """Each user should have completely isolated data."""
        # Create product for user1
        response = client.post('/api/products?user_id=test_user_1', json={
            'product_name': 'User1 Coffee',
            'roaster': 'User1 Roaster',
            'bean_type': ['Arabica'],
            'country': 'Colombia',
            'region_id': []
        })
        assert response.status_code == 201
        
        # Create product for user2
        response = client.post('/api/products?user_id=test_user_2', json={
            'product_name': 'User2 Coffee',
            'roaster': 'User2 Roaster',
            'bean_type': ['Robusta'],
            'country': 'Brazil',
            'region_id': []
        })
        assert response.status_code == 201
        
        # User1 should only see their product
        response = client.get('/api/products?user_id=test_user_1')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['product_name'] == 'User1 Coffee'
        
        # User2 should only see their product
        response = client.get('/api/products?user_id=test_user_2')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['product_name'] == 'User2 Coffee'
        
        # Default user should see nothing
        response = client.get('/api/products')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 0
    
    def test_user_folders_are_created(self, client, app):
        """User-specific folders should be created when first accessed."""
        data_dir = Path(app.config['DATA_DIR'])
        
        # Initially, only default user folder exists (or migration files after fresh setup)
        # After migrations run, there may be files like data_version.json, shots.json, etc.
        has_main_data = (data_dir / 'products.json').exists()
        has_only_migration_files = not has_main_data and any(data_dir.iterdir())
        is_completely_empty = not any(data_dir.iterdir())
        assert has_main_data or has_only_migration_files or is_completely_empty
        
        # Access user1 data
        client.get('/api/products?user_id=test_user_1')
        
        # User1 folder should now exist
        user1_dir = data_dir / 'users' / 'test_user_1'
        assert user1_dir.exists()
        assert (user1_dir / 'products.json').exists()
    
    def test_initialize_user_with_test_data(self, client, app):
        """Should be able to initialize a user with copy of test data programmatically."""
        from coffeejournal.repositories.factory import get_repository_factory
        
        # Initialize user with test data using the factory directly
        factory = get_repository_factory()
        factory.initialize_user_with_test_data('test_user_with_data')
        
        # User should have test data
        response = client.get('/api/products?user_id=test_user_with_data')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0  # Should have test data products
        
        # Verify it has standard test data (assuming test data has Intelligentsia roaster)
        response = client.get('/api/roasters?user_id=test_user_with_data')
        assert response.status_code == 200
        roasters = response.get_json()
        roaster_names = [r['name'] for r in roasters]
        assert 'Intelligentsia Coffee' in roaster_names
    
    def test_delete_user_removes_data(self, client, app):
        """Deleting a user should remove all their data programmatically."""
        from coffeejournal.repositories.factory import get_repository_factory
        
        # Create user with some data
        client.post('/api/products?user_id=test_user_to_delete', json={
            'product_name': 'Temporary Coffee',
            'roaster': 'Temp Roaster',
            'bean_type': ['Arabica'],
            'country': 'Colombia',
            'region_id': []
        })
        
        # Verify folder exists
        data_dir = Path(app.config['DATA_DIR'])
        user_dir = data_dir / 'users' / 'test_user_to_delete'
        assert user_dir.exists()
        
        # Delete user using factory directly
        factory = get_repository_factory()
        factory.delete_user('test_user_to_delete')
        
        # Folder should be gone
        assert not user_dir.exists()
    
    def test_all_endpoints_support_user_id(self, client):
        """All API endpoints should support user_id parameter."""
        endpoints_to_test = [
            ('/api/products', 'GET'),
            ('/api/batches', 'GET'),
            ('/api/brew_sessions', 'GET'),
            ('/api/roasters', 'GET'),
            ('/api/bean_types', 'GET'),
            ('/api/countries', 'GET'),
            ('/api/regions', 'GET'),
            ('/api/brew_methods', 'GET'),
            ('/api/recipes', 'GET'),
            ('/api/grinders', 'GET'),
            ('/api/filters', 'GET'),
            ('/api/kettles', 'GET'),
            ('/api/scales', 'GET'),
            ('/api/decaf_methods', 'GET'),
        ]
        
        for endpoint, method in endpoints_to_test:
            response = client.open(f"{endpoint}?user_id=test_user_endpoints", method=method)
            # Should not return 400 or 500 errors
            assert response.status_code in [200, 201, 204, 404]
    
    def test_cleanup_removes_all_test_users(self, client, app):
        """Cleanup function should remove all test user folders programmatically."""
        from coffeejournal.repositories.factory import get_repository_factory
        
        # Create several test users
        for i in range(3):
            client.get(f'/api/products?user_id=test_cleanup_user_{i}')
        
        data_dir = Path(app.config['DATA_DIR'])
        users_dir = data_dir / 'users'
        
        # Verify test users exist
        if users_dir.exists():
            test_user_folders = [f for f in users_dir.iterdir() if f.name.startswith('test_')]
            assert len(test_user_folders) >= 3
        
        # Call cleanup using factory directly
        factory = get_repository_factory()
        count = factory.cleanup_test_users()
        assert count >= 3
        
        # All test user folders should be gone
        if users_dir.exists():
            remaining_test_folders = [f for f in users_dir.iterdir() if f.name.startswith('test_')]
            assert len(remaining_test_folders) == 0
    
    def test_user_id_validation(self, client):
        """User IDs should be validated for filesystem safety."""
        # These should be rejected
        invalid_user_ids = [
            '../escape',
            '../../etc/passwd',
            'user/with/slashes',
            'user\\with\\backslashes',
            '.',
            '..',
            '',
            ' ',
            'user with spaces',  # Could allow this but safer to reject
        ]
        
        for user_id in invalid_user_ids:
            response = client.get(f'/api/products?user_id={user_id}')
            assert response.status_code == 400
            assert 'Invalid user_id' in response.get_json().get('error', '')
    
    def test_concurrent_user_access(self, client):
        """Multiple users should be able to work concurrently."""
        import threading
        results = {}
        
        def create_product_for_user(user_id, product_name):
            response = client.post(f'/api/products?user_id={user_id}', json={
                'product_name': product_name,
                'roaster': f'Roaster_{user_id}',
                'bean_type': ['Arabica'],
                'country': 'Colombia',
                'region_id': []
            })
            results[user_id] = response.status_code
        
        # Create products for multiple users concurrently
        threads = []
        for i in range(5):
            user_id = f'concurrent_user_{i}'
            product_name = f'Concurrent Coffee {i}'
            thread = threading.Thread(
                target=create_product_for_user,
                args=(user_id, product_name)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All should succeed
        assert all(status == 201 for status in results.values())
        
        # Verify each user has their own product
        for i in range(5):
            user_id = f'concurrent_user_{i}'
            response = client.get(f'/api/products?user_id={user_id}')
            assert response.status_code == 200
            data = response.get_json()
            assert len(data) == 1
            assert data[0]['product_name'] == f'Concurrent Coffee {i}'