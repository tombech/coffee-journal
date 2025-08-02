"""
Tests for regions functionality and API endpoints.
"""
import pytest
from src.coffeejournal import create_app
from src.coffeejournal.repositories.factory import init_repository_factory, get_repository_factory


@pytest.fixture
def app():
    """Create test app with JSON repositories."""
    import tempfile
    test_data_dir = tempfile.mkdtemp()
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'DATA_DIR': test_data_dir
    })
    
    with app.app_context():
        init_repository_factory(storage_type='json', data_dir=test_data_dir)
    
    return app


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def repo_factory(app):
    """Repository factory."""
    with app.app_context():
        return get_repository_factory()


class TestRegionRepository:
    """Test region repository functionality."""
    
    def test_create_region(self, repo_factory):
        """Test creating a new region."""
        country_repo = repo_factory.get_country_repository()
        region_repo = repo_factory.get_region_repository()
        
        # Create a country first
        country = country_repo.create({'name': 'Ethiopia'})
        
        # Create a region
        region_data = {
            'name': 'Yirgacheffe',
            'country_id': country['id']
        }
        region = region_repo.create(region_data)
        
        assert region['id'] is not None
        assert region['name'] == 'Yirgacheffe'
        assert region['country_id'] == country['id']
        assert 'created_at' in region
        assert 'updated_at' in region
    
    def test_find_regions_by_country(self, repo_factory):
        """Test finding regions by country."""
        country_repo = repo_factory.get_country_repository()
        region_repo = repo_factory.get_region_repository()
        
        # Create countries
        ethiopia = country_repo.create({'name': 'Ethiopia'})
        colombia = country_repo.create({'name': 'Colombia'})
        
        # Create regions
        region_repo.create({'name': 'Yirgacheffe', 'country_id': ethiopia['id']})
        region_repo.create({'name': 'Sidamo', 'country_id': ethiopia['id']})
        region_repo.create({'name': 'Huila', 'country_id': colombia['id']})
        
        # Test finding by country
        ethiopia_regions = region_repo.find_by_country(ethiopia['id'])
        colombia_regions = region_repo.find_by_country(colombia['id'])
        
        assert len(ethiopia_regions) == 2
        assert len(colombia_regions) == 1
        
        ethiopia_names = [r['name'] for r in ethiopia_regions]
        assert 'Yirgacheffe' in ethiopia_names
        assert 'Sidamo' in ethiopia_names
        
        assert colombia_regions[0]['name'] == 'Huila'
    
    def test_region_get_or_create(self, repo_factory):
        """Test get_or_create functionality for regions."""
        country_repo = repo_factory.get_country_repository()
        region_repo = repo_factory.get_region_repository()
        
        # Create a country
        country = country_repo.create({'name': 'Kenya'})
        
        # First call should create
        region1 = region_repo.get_or_create('Nyeri', country_id=country['id'])
        assert region1['name'] == 'Nyeri'
        assert region1['country_id'] == country['id']
        
        # Second call should return existing
        region2 = region_repo.get_or_create('Nyeri', country_id=country['id'])
        assert region1['id'] == region2['id']
        
        # Different country should create new region
        country2 = country_repo.create({'name': 'Ethiopia'})
        region3 = region_repo.get_or_create('Nyeri', country_id=country2['id'])
        assert region3['id'] != region1['id']
        assert region3['country_id'] == country2['id']


class TestRegionAPI:
    """Test region API endpoints."""
    
    def test_get_all_regions(self, client, repo_factory):
        """Test getting all regions."""
        country_repo = repo_factory.get_country_repository()
        region_repo = repo_factory.get_region_repository()
        
        # Create test data
        ethiopia = country_repo.create({'name': 'Ethiopia'})
        region_repo.create({'name': 'Yirgacheffe', 'country_id': ethiopia['id']})
        region_repo.create({'name': 'Sidamo', 'country_id': ethiopia['id']})
        
        response = client.get('/api/regions')
        assert response.status_code == 200
        
        regions = response.get_json()
        assert len(regions) == 2
        region_names = [r['name'] for r in regions]
        assert 'Yirgacheffe' in region_names
        assert 'Sidamo' in region_names
    
    def test_get_regions_by_country(self, client, repo_factory):
        """Test getting regions for a specific country."""
        country_repo = repo_factory.get_country_repository()
        region_repo = repo_factory.get_region_repository()
        
        # Create test data
        ethiopia = country_repo.create({'name': 'Ethiopia'})
        colombia = country_repo.create({'name': 'Colombia'})
        
        region_repo.create({'name': 'Yirgacheffe', 'country_id': ethiopia['id']})
        region_repo.create({'name': 'Sidamo', 'country_id': ethiopia['id']})
        region_repo.create({'name': 'Huila', 'country_id': colombia['id']})
        
        response = client.get(f'/api/countries/{ethiopia["id"]}/regions')
        assert response.status_code == 200
        
        regions = response.get_json()
        assert len(regions) == 2
        region_names = [r['name'] for r in regions]
        assert 'Yirgacheffe' in region_names
        assert 'Sidamo' in region_names
        assert 'Huila' not in region_names
    
    def test_create_region_via_country(self, client, repo_factory):
        """Test creating a region via country endpoint."""
        country_repo = repo_factory.get_country_repository()
        country = country_repo.create({'name': 'Brazil'})
        
        region_data = {'name': 'Cerrado'}
        response = client.post(f'/api/countries/{country["id"]}/regions', 
                             json=region_data)
        assert response.status_code == 201
        
        region = response.get_json()
        assert region['name'] == 'Cerrado'
        assert region['country_id'] == country['id']
    
    def test_update_region(self, client, repo_factory):
        """Test updating a region."""
        country_repo = repo_factory.get_country_repository()
        region_repo = repo_factory.get_region_repository()
        
        country = country_repo.create({'name': 'Guatemala'})
        region = region_repo.create({'name': 'Antigua', 'country_id': country['id']})
        
        update_data = {
            'name': 'Antigua Valley',
            'description': 'Famous volcanic region'
        }
        response = client.put(f'/api/regions/{region["id"]}', json=update_data)
        assert response.status_code == 200
        
        updated_region = response.get_json()
        assert updated_region['name'] == 'Antigua Valley'
        assert updated_region['description'] == 'Famous volcanic region'
        assert updated_region['country_id'] == country['id']
    
    def test_delete_region(self, client, repo_factory):
        """Test deleting a region."""
        country_repo = repo_factory.get_country_repository()
        region_repo = repo_factory.get_region_repository()
        
        country = country_repo.create({'name': 'Costa Rica'})
        region = region_repo.create({'name': 'Tarrazú', 'country_id': country['id']})
        
        response = client.delete(f'/api/regions/{region["id"]}')
        assert response.status_code == 204
        
        # Verify deletion
        response = client.get(f'/api/regions/{region["id"]}')
        assert response.status_code == 404
    
    def test_region_usage_tracking(self, client, repo_factory):
        """Test region usage tracking in products."""
        country_repo = repo_factory.get_country_repository()
        region_repo = repo_factory.get_region_repository()
        product_repo = repo_factory.get_product_repository()
        roaster_repo = repo_factory.get_roaster_repository()
        
        # Create test data
        country = country_repo.create({'name': 'Ethiopia'})
        region = region_repo.create({'name': 'Yirgacheffe', 'country_id': country['id']})
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        
        # Create product using the region
        product_repo.create({
            'product_name': 'Test Coffee',
            'roaster_id': roaster['id'],
            'bean_type_id': [],
            'country_id': country['id'],
            'region_id': [region['id']]
        })
        
        # Check usage
        response = client.get(f'/api/regions/{region["id"]}/usage')
        assert response.status_code == 200
        
        usage = response.get_json()
        assert usage['in_use'] == True
        assert usage['usage_count'] == 1
        assert usage['usage_type'] == 'products'
    
    def test_region_reference_update(self, client, repo_factory):
        """Test updating region references in products."""
        country_repo = repo_factory.get_country_repository()
        region_repo = repo_factory.get_region_repository()
        product_repo = repo_factory.get_product_repository()
        roaster_repo = repo_factory.get_roaster_repository()
        
        # Create test data
        country = country_repo.create({'name': 'Ethiopia'})
        region1 = region_repo.create({'name': 'Yirgacheffe', 'country_id': country['id']})
        region2 = region_repo.create({'name': 'Yirgacheffe Proper', 'country_id': country['id']})
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        
        # Create product using region1
        product = product_repo.create({
            'product_name': 'Test Coffee',
            'roaster_id': roaster['id'],
            'bean_type_id': [],
            'country_id': country['id'],
            'region_id': [region1['id']]
        })
        
        # Replace region1 with region2
        update_data = {
            'action': 'replace',
            'replacement_id': region2['id']
        }
        response = client.post(f'/api/regions/{region1["id"]}/update_references',
                             json=update_data)
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['updated_count'] == 1
        
        # Verify the product was updated
        updated_product = product_repo.find_by_id(product['id'])
        assert region2['id'] in updated_product['region_id']
        assert region1['id'] not in updated_product['region_id']


class TestArrayStandardization:
    """Test array standardization for bean_type_id and region_id."""
    
    def test_product_creation_with_arrays(self, client, repo_factory):
        """Test that products are created with array fields."""
        roaster_repo = repo_factory.get_roaster_repository()
        bean_type_repo = repo_factory.get_bean_type_repository()
        country_repo = repo_factory.get_country_repository()
        region_repo = repo_factory.get_region_repository()
        
        # Create test lookups
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        bean_type1 = bean_type_repo.create({'name': 'Arabica'})
        bean_type2 = bean_type_repo.create({'name': 'Bourbon'})
        country = country_repo.create({'name': 'Ethiopia'})
        region1 = region_repo.create({'name': 'Yirgacheffe', 'country_id': country['id']})
        region2 = region_repo.create({'name': 'Sidamo', 'country_id': country['id']})
        
        product_data = {
            'product_name': 'Multi Bean Coffee',
            'roaster_id': roaster['id'],
            'bean_type_id': [bean_type1['id'], bean_type2['id']],
            'country_id': country['id'],
            'region_id': [region1['id'], region2['id']]
        }
        
        response = client.post('/api/products', json=product_data)
        assert response.status_code == 201
        
        product = response.get_json()
        
        # Verify arrays in response
        assert isinstance(product['bean_type'], list)
        assert len(product['bean_type']) == 2
        assert isinstance(product['region'], list)
        assert len(product['region']) == 2
        
        bean_type_names = [bt['name'] for bt in product['bean_type']]
        assert 'Arabica' in bean_type_names
        assert 'Bourbon' in bean_type_names
        
        region_names = [r['name'] for r in product['region']]
        assert 'Yirgacheffe' in region_names
        assert 'Sidamo' in region_names
    
    def test_empty_arrays_for_null_values(self, client, repo_factory):
        """Test that null/missing values become empty arrays."""
        roaster_repo = repo_factory.get_roaster_repository()
        country_repo = repo_factory.get_country_repository()
        
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        country = country_repo.create({'name': 'Brazil'})
        
        product_data = {
            'product_name': 'Simple Coffee',
            'roaster_id': roaster['id'],
            'country_id': country['id']
            # No bean_type_id or region_id specified
        }
        
        response = client.post('/api/products', json=product_data)
        assert response.status_code == 201
        
        product = response.get_json()
        
        # Should have empty arrays, not null
        assert product['bean_type'] == []
        assert product['region'] == []
    
    def test_bean_type_reference_updates_with_arrays(self, client, repo_factory):
        """Test that bean type reference updates work with arrays."""
        roaster_repo = repo_factory.get_roaster_repository()
        bean_type_repo = repo_factory.get_bean_type_repository()
        product_repo = repo_factory.get_product_repository()
        
        # Create test data
        roaster = roaster_repo.create({'name': 'Test Roaster'})
        arabica = bean_type_repo.create({'name': 'Arabica'})
        robusta = bean_type_repo.create({'name': 'Robusta'})
        typica = bean_type_repo.create({'name': 'Typica'})
        
        # Create product with multiple bean types
        product = product_repo.create({
            'product_name': 'Blend',
            'roaster_id': roaster['id'],
            'bean_type_id': [arabica['id'], robusta['id']],  # Array with both
            'country_id': None,
            'region_id': []
        })
        
        # Replace Arabica with Typica
        update_data = {
            'action': 'replace',
            'replacement_id': typica['id']
        }
        response = client.post(f'/api/bean_types/{arabica["id"]}/update_references',
                             json=update_data)
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['updated_count'] == 1
        
        # Verify the update
        updated_product = product_repo.find_by_id(product['id'])
        assert typica['id'] in updated_product['bean_type_id']
        assert robusta['id'] in updated_product['bean_type_id']
        assert arabica['id'] not in updated_product['bean_type_id']
        assert len(updated_product['bean_type_id']) == 2