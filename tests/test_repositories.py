"""
Unit tests for Coffee Journal repositories.
Tests CRUD operations and relationships using the repository pattern.
"""
import pytest
from datetime import date, datetime


class TestRoasterRepository:
    """Tests for the Roaster repository."""
    
    def test_create_roaster(self, repo_factory):
        """Test creating a roaster."""
        roaster_repo = repo_factory.get_roaster_repository()
        
        roaster = roaster_repo.create({'name': 'Blue Bottle Coffee'})
        
        assert roaster['id'] is not None
        assert roaster['name'] == 'Blue Bottle Coffee'
        
        # Verify it's persisted
        found_roaster = roaster_repo.find_by_id(roaster['id'])
        assert found_roaster is not None
        assert found_roaster['name'] == 'Blue Bottle Coffee'
    
    def test_update_roaster(self, repo_factory):
        """Test updating a roaster."""
        roaster_repo = repo_factory.get_roaster_repository()
        
        # Create initial roaster
        roaster = roaster_repo.create({'name': 'Blue Bottle'})
        roaster_id = roaster['id']
        
        # Update the roaster
        updated_roaster = roaster_repo.update(roaster_id, {'name': 'Blue Bottle Coffee'})
        
        assert updated_roaster['name'] == 'Blue Bottle Coffee'
        assert updated_roaster['id'] == roaster_id
        
        # Verify persistence
        fetched_roaster = roaster_repo.find_by_id(roaster_id)
        assert fetched_roaster['name'] == 'Blue Bottle Coffee'
    
    def test_delete_roaster(self, repo_factory):
        """Test deleting a roaster."""
        roaster_repo = repo_factory.get_roaster_repository()
        
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        roaster_id = roaster['id']
        
        # Delete the roaster
        result = roaster_repo.delete(roaster_id)
        assert result is True
        
        # Verify it's deleted
        deleted_roaster = roaster_repo.find_by_id(roaster_id)
        assert deleted_roaster is None
    
    def test_find_by_name(self, repo_factory):
        """Test finding roaster by name."""
        roaster_repo = repo_factory.get_roaster_repository()
        
        roaster = roaster_repo.create({'name': 'Unique Roaster'})
        
        found = roaster_repo.find_by_name('Unique Roaster')
        assert found is not None
        assert found['id'] == roaster['id']
        
        # Test not found
        not_found = roaster_repo.find_by_name('Non-existent')
        assert not_found is None
    
    def test_get_or_create(self, repo_factory):
        """Test get_or_create functionality."""
        roaster_repo = repo_factory.get_roaster_repository()
        
        # Create new
        roaster1 = roaster_repo.get_or_create('New Roaster')
        assert roaster1['name'] == 'New Roaster'
        assert roaster1['id'] is not None
        
        # Get existing
        roaster2 = roaster_repo.get_or_create('New Roaster')
        assert roaster2['id'] == roaster1['id']
        
        # Verify only one exists
        all_roasters = roaster_repo.find_all()
        matching = [r for r in all_roasters if r['name'] == 'New Roaster']
        assert len(matching) == 1


class TestBeanTypeRepository:
    """Tests for the BeanType repository."""
    
    def test_create_bean_type(self, repo_factory):
        """Test creating a bean type."""
        bean_type_repo = repo_factory.get_bean_type_repository()
        
        bean_type = bean_type_repo.create({'name': 'Arabica'})
        
        assert bean_type['id'] is not None
        assert bean_type['name'] == 'Arabica'


class TestCountryRepository:
    """Tests for the Country repository."""
    
    def test_create_country(self, repo_factory):
        """Test creating a country."""
        country_repo = repo_factory.get_country_repository()
        
        country = country_repo.create({'name': 'Ethiopia'})
        
        assert country['id'] is not None
        assert country['name'] == 'Ethiopia'


class TestProductRepository:
    """Tests for the Product repository."""
    
    def test_create_product(self, repo_factory):
        """Test creating a product."""
        roaster_repo = repo_factory.get_roaster_repository()
        product_repo = repo_factory.get_product_repository()
        
        # Create roaster first
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        
        product_data = {
            'roaster': 'Test Roaster',
            'roaster_id': roaster['id'],
            'product_name': 'Test Blend',
            'roast_type': 5,
            'description': 'A test coffee blend'
        }
        
        product = product_repo.create(product_data)
        
        assert product['id'] is not None
        assert product['product_name'] == 'Test Blend'
        assert product['roast_type'] == 5
        assert product['roaster_id'] == roaster['id']
    
    def test_update_product(self, repo_factory):
        """Test updating a product."""
        roaster_repo = repo_factory.get_roaster_repository()
        product_repo = repo_factory.get_product_repository()
        
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        
        product = product_repo.create({
            'roaster': 'Test Roaster',
            'roaster_id': roaster['id'],
            'product_name': 'Original Name'
        })
        product_id = product['id']
        
        # Update the product
        updated_data = {
            'roaster': 'Test Roaster',
            'roaster_id': roaster['id'],
            'product_name': 'Updated Name',
            'roast_type': 7
        }
        updated_product = product_repo.update(product_id, updated_data)
        
        assert updated_product['product_name'] == 'Updated Name'
        assert updated_product['roast_type'] == 7
    
    def test_delete_product(self, repo_factory):
        """Test deleting a product."""
        roaster_repo = repo_factory.get_roaster_repository()
        product_repo = repo_factory.get_product_repository()
        
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        product = product_repo.create({
            'roaster': 'Test Roaster',
            'roaster_id': roaster['id']
        })
        product_id = product['id']
        
        result = product_repo.delete(product_id)
        assert result is True
        
        deleted_product = product_repo.find_by_id(product_id)
        assert deleted_product is None
    
    def test_find_by_filters(self, repo_factory):
        """Test finding products by filters."""
        roaster_repo = repo_factory.get_roaster_repository()
        bean_type_repo = repo_factory.get_bean_type_repository()
        product_repo = repo_factory.get_product_repository()
        
        # Create test data
        roaster1 = roaster_repo.create({'name': 'Roaster 1'})
        roaster2 = roaster_repo.create({'name': 'Roaster 2'})
        bean_type = bean_type_repo.create({'name': 'Arabica'})
        
        # Create products
        product1 = product_repo.create({
            'roaster': 'Roaster 1',
            'roaster_id': roaster1['id'],
            'bean_type': 'Arabica',
            'bean_type_id': bean_type['id']
        })
        product2 = product_repo.create({
            'roaster': 'Roaster 2',
            'roaster_id': roaster2['id'],
            'bean_type': 'Arabica',
            'bean_type_id': bean_type['id']
        })
        product3 = product_repo.create({
            'roaster': 'Roaster 1',
            'roaster_id': roaster1['id']
        })
        
        # Test filters
        filtered = product_repo.find_by_filters({'roaster': 'Roaster 1'})
        assert len(filtered) == 2
        
        filtered = product_repo.find_by_filters({'bean_type': 'Arabica'})
        assert len(filtered) == 2
        
        filtered = product_repo.find_by_filters({
            'roaster': 'Roaster 1',
            'bean_type': 'Arabica'
        })
        assert len(filtered) == 1
        assert filtered[0]['id'] == product1['id']


class TestBatchRepository:
    """Tests for the Batch repository."""
    
    def test_create_batch(self, repo_factory):
        """Test creating a batch."""
        roaster_repo = repo_factory.get_roaster_repository()
        product_repo = repo_factory.get_product_repository()
        batch_repo = repo_factory.get_batch_repository()
        
        # Create dependencies
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        product = product_repo.create({
            'roaster': 'Test Roaster',
            'roaster_id': roaster['id']
        })
        
        batch_data = {
            'product_id': product['id'],
            'roast_date': date(2025, 1, 1).isoformat(),
            'amount_grams': 250.0,
            'price': 15.99,
            'seller': 'Local Coffee Shop'
        }
        
        batch = batch_repo.create(batch_data)
        
        assert batch['id'] is not None
        assert batch['roast_date'] == '2025-01-01'
        assert batch['amount_grams'] == 250.0
        assert batch['price'] == 15.99
        assert batch['seller'] == 'Local Coffee Shop'
    
    def test_find_by_product(self, repo_factory):
        """Test finding batches by product."""
        roaster_repo = repo_factory.get_roaster_repository()
        product_repo = repo_factory.get_product_repository()
        batch_repo = repo_factory.get_batch_repository()
        
        # Create test data
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        product1 = product_repo.create({
            'roaster': 'Test Roaster',
            'roaster_id': roaster['id']
        })
        product2 = product_repo.create({
            'roaster': 'Test Roaster',
            'roaster_id': roaster['id']
        })
        
        # Create batches
        batch1 = batch_repo.create({
            'product_id': product1['id'],
            'roast_date': date(2025, 1, 1).isoformat()
        })
        batch2 = batch_repo.create({
            'product_id': product1['id'],
            'roast_date': date(2025, 1, 2).isoformat()
        })
        batch3 = batch_repo.create({
            'product_id': product2['id'],
            'roast_date': date(2025, 1, 3).isoformat()
        })
        
        # Test finding by product
        product1_batches = batch_repo.find_by_product(product1['id'])
        assert len(product1_batches) == 2
        
        product2_batches = batch_repo.find_by_product(product2['id'])
        assert len(product2_batches) == 1
        assert product2_batches[0]['id'] == batch3['id']
    
    def test_delete_by_product(self, repo_factory):
        """Test deleting all batches for a product."""
        roaster_repo = repo_factory.get_roaster_repository()
        product_repo = repo_factory.get_product_repository()
        batch_repo = repo_factory.get_batch_repository()
        
        # Create test data
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        product = product_repo.create({
            'roaster': 'Test Roaster',
            'roaster_id': roaster['id']
        })
        
        # Create batches
        batch1 = batch_repo.create({
            'product_id': product['id'],
            'roast_date': date(2025, 1, 1).isoformat()
        })
        batch2 = batch_repo.create({
            'product_id': product['id'],
            'roast_date': date(2025, 1, 2).isoformat()
        })
        
        # Delete by product
        deleted_count = batch_repo.delete_by_product(product['id'])
        assert deleted_count == 2
        
        # Verify deletion
        remaining_batches = batch_repo.find_by_product(product['id'])
        assert len(remaining_batches) == 0


class TestBrewSessionRepository:
    """Tests for the BrewSession repository."""
    
    def test_create_brew_session(self, repo_factory):
        """Test creating a brew session."""
        roaster_repo = repo_factory.get_roaster_repository()
        product_repo = repo_factory.get_product_repository()
        batch_repo = repo_factory.get_batch_repository()
        brew_method_repo = repo_factory.get_brew_method_repository()
        session_repo = repo_factory.get_brew_session_repository()
        
        # Create dependencies
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        product = product_repo.create({
            'roaster': 'Test Roaster',
            'roaster_id': roaster['id']
        })
        batch = batch_repo.create({
            'product_id': product['id'],
            'roast_date': date(2025, 1, 1).isoformat()
        })
        brew_method = brew_method_repo.create({'name': 'V60'})
        
        session_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'product_batch_id': batch['id'],
            'product_id': product['id'],
            'brew_method_id': brew_method['id'],
            'amount_coffee_grams': 18.0,
            'amount_water_grams': 300.0,
            'brew_temperature_c': 93.0,
            'sweetness': 8,
            'notes': 'Great cup!'
        }
        
        session = session_repo.create(session_data)
        
        assert session['id'] is not None
        assert session['amount_coffee_grams'] == 18.0
        assert session['amount_water_grams'] == 300.0
        assert session['sweetness'] == 8
        assert session['notes'] == 'Great cup!'
    
    def test_find_by_product(self, repo_factory):
        """Test finding brew sessions by product."""
        roaster_repo = repo_factory.get_roaster_repository()
        product_repo = repo_factory.get_product_repository()
        batch_repo = repo_factory.get_batch_repository()
        session_repo = repo_factory.get_brew_session_repository()
        
        # Create test data
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        product1 = product_repo.create({
            'roaster': 'Test Roaster',
            'roaster_id': roaster['id']
        })
        product2 = product_repo.create({
            'roaster': 'Test Roaster',
            'roaster_id': roaster['id']
        })
        batch1 = batch_repo.create({
            'product_id': product1['id'],
            'roast_date': date(2025, 1, 1).isoformat()
        })
        batch2 = batch_repo.create({
            'product_id': product2['id'],
            'roast_date': date(2025, 1, 2).isoformat()
        })
        
        # Create sessions
        session1 = session_repo.create({
            'timestamp': datetime.utcnow().isoformat(),
            'product_batch_id': batch1['id'],
            'product_id': product1['id']
        })
        session2 = session_repo.create({
            'timestamp': datetime.utcnow().isoformat(),
            'product_batch_id': batch1['id'],
            'product_id': product1['id']
        })
        session3 = session_repo.create({
            'timestamp': datetime.utcnow().isoformat(),
            'product_batch_id': batch2['id'],
            'product_id': product2['id']
        })
        
        # Test finding by product
        product1_sessions = session_repo.find_by_product(product1['id'])
        assert len(product1_sessions) == 2
        
        product2_sessions = session_repo.find_by_product(product2['id'])
        assert len(product2_sessions) == 1
        assert product2_sessions[0]['id'] == session3['id']
    
    def test_find_by_batch(self, repo_factory):
        """Test finding brew sessions by batch."""
        roaster_repo = repo_factory.get_roaster_repository()
        product_repo = repo_factory.get_product_repository()
        batch_repo = repo_factory.get_batch_repository()
        session_repo = repo_factory.get_brew_session_repository()
        
        # Create test data
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        product = product_repo.create({
            'roaster': 'Test Roaster',
            'roaster_id': roaster['id']
        })
        batch1 = batch_repo.create({
            'product_id': product['id'],
            'roast_date': date(2025, 1, 1).isoformat()
        })
        batch2 = batch_repo.create({
            'product_id': product['id'],
            'roast_date': date(2025, 1, 2).isoformat()
        })
        
        # Create sessions
        session1 = session_repo.create({
            'timestamp': datetime.utcnow().isoformat(),
            'product_batch_id': batch1['id'],
            'product_id': product['id']
        })
        session2 = session_repo.create({
            'timestamp': datetime.utcnow().isoformat(),
            'product_batch_id': batch2['id'],
            'product_id': product['id']
        })
        
        # Test finding by batch
        batch1_sessions = session_repo.find_by_batch(batch1['id'])
        assert len(batch1_sessions) == 1
        assert batch1_sessions[0]['id'] == session1['id']
        
        batch2_sessions = session_repo.find_by_batch(batch2['id'])
        assert len(batch2_sessions) == 1
        assert batch2_sessions[0]['id'] == session2['id']


class TestCalculatedProperties:
    """Tests for calculated properties in the API."""
    
    def test_price_per_cup_calculation(self, client, repo_factory):
        """Test price per cup calculation in batch API."""
        # Create test data
        roaster_repo = repo_factory.get_roaster_repository()
        product_repo = repo_factory.get_product_repository()
        
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        product = product_repo.create({
            'roaster': 'Test Roaster',
            'roaster_id': roaster['id']
        })
        
        # Create batch via API
        batch_data = {
            'roast_date': '2025-01-01',
            'amount_grams': 180.0,  # Exactly 10 cups worth
            'price': 10.0
        }
        
        response = client.post(f'/api/products/{product["id"]}/batches', json=batch_data)
        assert response.status_code == 201
        
        batch = response.get_json()
        assert batch['price_per_cup'] == 1.0  # 10.0 / 10 cups = 1.0
    
    def test_brew_ratio_calculation(self, client, repo_factory):
        """Test brew ratio calculation in session API."""
        # Create test data
        roaster_repo = repo_factory.get_roaster_repository()
        product_repo = repo_factory.get_product_repository()
        batch_repo = repo_factory.get_batch_repository()
        
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        product = product_repo.create({
            'roaster': 'Test Roaster',
            'roaster_id': roaster['id']
        })
        batch = batch_repo.create({
            'product_id': product['id'],
            'roast_date': date(2025, 1, 1).isoformat()
        })
        
        # Create session via API
        session_data = {
            'amount_coffee_grams': 18.0,
            'amount_water_grams': 300.0
        }
        
        response = client.post(f'/api/batches/{batch["id"]}/brew_sessions', json=session_data)
        assert response.status_code == 201
        
        session = response.get_json()
        # 300/18 = 16.67, should be "1:16.7"
        assert session['brew_ratio'] == '1:16.7'
    
    def test_price_per_cup_with_string_inputs(self, client, repo_factory):
        """Test price per cup calculation with string inputs from forms."""
        # Create test data
        roaster_repo = repo_factory.get_roaster_repository()
        product_repo = repo_factory.get_product_repository()
        
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        product = product_repo.create({
            'roaster': 'Test Roaster',
            'roaster_id': roaster['id']
        })
        
        # Create batch via API with string inputs (like from HTML form)
        batch_data = {
            'roast_date': '2025-01-01',
            'amount_grams': '180.0',  # String input
            'price': '10.0'           # String input
        }
        
        response = client.post(f'/api/products/{product["id"]}/batches', json=batch_data)
        assert response.status_code == 201
        
        batch = response.get_json()
        assert batch['price_per_cup'] == 1.0  # Should handle string conversion
    
    def test_brew_ratio_with_string_inputs(self, client, repo_factory):
        """Test brew ratio calculation with string inputs from forms."""
        # Create test data
        roaster_repo = repo_factory.get_roaster_repository()
        product_repo = repo_factory.get_product_repository()
        batch_repo = repo_factory.get_batch_repository()
        
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        product = product_repo.create({
            'roaster': 'Test Roaster',
            'roaster_id': roaster['id']
        })
        batch = batch_repo.create({
            'product_id': product['id'],
            'roast_date': date(2025, 1, 1).isoformat()
        })
        
        # Create session via API with string inputs (like from HTML form)
        session_data = {
            'amount_coffee_grams': '18.0',  # String input
            'amount_water_grams': '300.0'   # String input
        }
        
        response = client.post(f'/api/batches/{batch["id"]}/brew_sessions', json=session_data)
        assert response.status_code == 201
        
        session = response.get_json()
        # 300/18 = 16.67, should be "1:16.7" - should handle string conversion
        assert session['brew_ratio'] == '1:16.7'