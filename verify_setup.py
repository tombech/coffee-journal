#!/usr/bin/env python3
"""
Verify the Coffee Journal setup works correctly.
"""
import os
import sys
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from coffeejournal import create_app
from coffeejournal.repositories.factory import get_repository_factory

def test_default_configuration():
    """Test that default configuration works."""
    print("Testing default configuration...")
    
    app = create_app()
    print(f"✓ App created successfully")
    print(f"✓ DATA_DIR: {app.config['DATA_DIR']}")
    
    # Verify test_data directory exists
    if not os.path.exists(app.config['DATA_DIR']):
        print("✗ test_data directory not found")
        return False
    
    print(f"✓ Data directory exists")
    
    # Test API endpoints
    with app.test_client() as client:
        response = client.get('/api/products')
        if response.status_code != 200:
            print(f"✗ Products API failed: {response.status_code}")
            return False
        
        products = response.get_json()
        print(f"✓ Found {len(products)} products")
        
        if len(products) < 5:
            print("✗ Expected at least 5 products in test data")
            return False
    
    print("✓ Default configuration works correctly")
    return True

def test_custom_data_directory():
    """Test that custom data directory works."""
    print("\nTesting custom data directory...")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Set environment variable
        os.environ['DATA_DIR'] = temp_dir
        
        app = create_app()
        print(f"✓ App created with custom DATA_DIR: {app.config['DATA_DIR']}")
        
        if app.config['DATA_DIR'] != temp_dir:
            print(f"✗ Expected DATA_DIR to be {temp_dir}, got {app.config['DATA_DIR']}")
            return False
        
        # Test with empty directory (should create empty files)
        with app.test_client() as client:
            response = client.get('/api/products')
            if response.status_code != 200:
                print(f"✗ Products API failed: {response.status_code}")
                return False
            
            products = response.get_json()
            print(f"✓ Found {len(products)} products (empty directory)")
            
            if len(products) != 0:
                print("✗ Expected 0 products in empty directory")
                return False
        
        print("✓ Custom data directory works correctly")
        return True
        
    finally:
        # Clean up
        if 'DATA_DIR' in os.environ:
            del os.environ['DATA_DIR']
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_repository_functionality():
    """Test that repository functionality works."""
    print("\nTesting repository functionality...")
    
    app = create_app()
    
    with app.app_context():
        factory = get_repository_factory()
        
        # Test roaster repository
        roaster_repo = factory.get_roaster_repository()
        roasters = roaster_repo.find_all()
        print(f"✓ Found {len(roasters)} roasters")
        
        # Test product repository
        product_repo = factory.get_product_repository()
        products = product_repo.find_all()
        print(f"✓ Found {len(products)} products")
        
        # Test batch repository
        batch_repo = factory.get_batch_repository()
        batches = batch_repo.find_all()
        print(f"✓ Found {len(batches)} batches")
        
        # Test brew session repository
        session_repo = factory.get_brew_session_repository()
        sessions = session_repo.find_all()
        print(f"✓ Found {len(sessions)} brew sessions")
        
        print("✓ Repository functionality works correctly")
        return True

def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Coffee Journal Setup Verification")
    print("=" * 60)
    
    tests = [
        test_default_configuration,
        test_custom_data_directory,
        test_repository_functionality
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed! The Coffee Journal setup is working correctly.")
        print("\nTo start the application:")
        print("  PYTHONPATH=src uv run python3 -m coffeejournal.wsgi")
        print("\nTo use a custom data directory:")
        print("  DATA_DIR=/path/to/data PYTHONPATH=src uv run python3 -m coffeejournal.wsgi")
        return True
    else:
        print("❌ Some tests failed. Please check the output above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)