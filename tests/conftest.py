"""
Pytest configuration and fixtures for Coffee Journal tests.
"""
import pytest
import tempfile
import os
import shutil
from src.coffeejournal import create_app
from src.coffeejournal.repositories.factory import init_repository_factory


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    # Create a temporary directory for test data
    test_data_dir = tempfile.mkdtemp()
    
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
    
    yield app
    
    # Clean up temporary data directory
    shutil.rmtree(test_data_dir)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def repo_factory(app):
    """Get the repository factory for direct testing."""
    from src.coffeejournal.repositories.factory import get_repository_factory
    with app.app_context():
        return get_repository_factory()