"""
Comprehensive tests for multi-user API functionality across all endpoints.
Written in TDD style to identify which endpoints need user_id support.
"""

import pytest
import tempfile
from coffeejournal import create_app


class TestComprehensiveMultiUserAPI:
    """Test multi-user functionality across all API endpoints."""
    
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
    
    def test_roasters_endpoints_support_user_id(self, client):
        """All roasters endpoints should support user_id parameter."""
        # Test basic CRUD with user_id
        # CREATE
        response = client.post('/api/roasters?user_id=test_roaster_user', json={
            'name': 'Test Roaster User1',
            'url': 'https://testroaster.com'
        })
        assert response.status_code == 201
        roaster_data = response.get_json()
        roaster_id = roaster_data['id']
        
        # GET all
        response = client.get('/api/roasters?user_id=test_roaster_user')
        assert response.status_code == 200
        roasters = response.get_json()
        assert len(roasters) == 1
        assert roasters[0]['name'] == 'Test Roaster User1'
        
        # GET specific
        response = client.get(f'/api/roasters/{roaster_id}?user_id=test_roaster_user')
        assert response.status_code == 200
        
        # UPDATE
        response = client.put(f'/api/roasters/{roaster_id}?user_id=test_roaster_user', json={
            'name': 'Updated Test Roaster User1'  
        })
        assert response.status_code == 200
        
        # Usage endpoints
        response = client.get(f'/api/roasters/{roaster_id}/usage?user_id=test_roaster_user')
        assert response.status_code == 200
        
        # Detail endpoint
        response = client.get(f'/api/roasters/{roaster_id}/detail?user_id=test_roaster_user')
        assert response.status_code == 200
        
        # DELETE
        response = client.delete(f'/api/roasters/{roaster_id}?user_id=test_roaster_user')
        assert response.status_code == 204
        
        # Verify isolation - different user shouldn't see the roaster
        response = client.get('/api/roasters?user_id=different_user')
        assert response.status_code == 200
        roasters = response.get_json()
        assert len(roasters) == 0
    
    def test_bean_types_endpoints_support_user_id(self, client):
        """All bean_types endpoints should support user_id parameter."""
        # CREATE
        response = client.post('/api/bean_types?user_id=test_bean_user', json={
            'name': 'Test Bean Type User1'
        })
        assert response.status_code == 201
        bean_type_data = response.get_json()
        bean_type_id = bean_type_data['id']
        
        # GET all
        response = client.get('/api/bean_types?user_id=test_bean_user')
        assert response.status_code == 200
        bean_types = response.get_json()
        assert len(bean_types) == 1
        assert bean_types[0]['name'] == 'Test Bean Type User1'
        
        # GET specific
        response = client.get(f'/api/bean_types/{bean_type_id}?user_id=test_bean_user')
        assert response.status_code == 200
        
        # UPDATE
        response = client.put(f'/api/bean_types/{bean_type_id}?user_id=test_bean_user', json={
            'name': 'Updated Test Bean Type User1'
        })
        assert response.status_code == 200
        
        # Usage endpoints
        response = client.get(f'/api/bean_types/{bean_type_id}/usage?user_id=test_bean_user')
        assert response.status_code == 200
        
        # DELETE
        response = client.delete(f'/api/bean_types/{bean_type_id}?user_id=test_bean_user')
        assert response.status_code == 204
        
        # Verify isolation
        response = client.get('/api/bean_types?user_id=different_user')
        assert response.status_code == 200
        bean_types = response.get_json()
        assert len(bean_types) == 0
    
    def test_countries_endpoints_support_user_id(self, client):
        """All countries endpoints should support user_id parameter."""
        # CREATE
        response = client.post('/api/countries?user_id=test_country_user', json={
            'name': 'Test Country User1'
        })
        assert response.status_code == 201
        country_data = response.get_json()
        country_id = country_data['id']
        
        # GET all
        response = client.get('/api/countries?user_id=test_country_user')
        assert response.status_code == 200
        countries = response.get_json()
        assert len(countries) == 1
        assert countries[0]['name'] == 'Test Country User1'
        
        # GET specific
        response = client.get(f'/api/countries/{country_id}?user_id=test_country_user')
        assert response.status_code == 200
        
        # UPDATE
        response = client.put(f'/api/countries/{country_id}?user_id=test_country_user', json={
            'name': 'Updated Test Country User1'
        })
        assert response.status_code == 200
        
        # Usage endpoints
        response = client.get(f'/api/countries/{country_id}/usage?user_id=test_country_user')
        assert response.status_code == 200
        
        # DELETE
        response = client.delete(f'/api/countries/{country_id}?user_id=test_country_user')
        assert response.status_code == 204
        
        # Verify isolation
        response = client.get('/api/countries?user_id=different_user')
        assert response.status_code == 200
        countries = response.get_json()
        assert len(countries) == 0
    
    def test_regions_endpoints_support_user_id(self, client):
        """All regions endpoints should support user_id parameter."""
        # First create a country
        response = client.post('/api/countries?user_id=test_region_user', json={
            'name': 'Test Country for Regions'
        })
        assert response.status_code == 201
        country_data = response.get_json()
        country_id = country_data['id']
        
        # CREATE region via country endpoint
        response = client.post(f'/api/countries/{country_id}/regions?user_id=test_region_user', json={
            'name': 'Test Region User1'
        })
        assert response.status_code == 201
        region_data = response.get_json()
        region_id = region_data['id']
        
        # GET all regions
        response = client.get('/api/regions?user_id=test_region_user')
        assert response.status_code == 200
        regions = response.get_json()
        assert len(regions) == 1
        assert regions[0]['name'] == 'Test Region User1'
        
        # GET regions for country
        response = client.get(f'/api/countries/{country_id}/regions?user_id=test_region_user')
        assert response.status_code == 200
        regions = response.get_json()
        assert len(regions) == 1
        
        # GET specific region
        response = client.get(f'/api/regions/{region_id}?user_id=test_region_user')
        assert response.status_code == 200
        
        # UPDATE
        response = client.put(f'/api/regions/{region_id}?user_id=test_region_user', json={
            'name': 'Updated Test Region User1'
        })
        assert response.status_code == 200
        
        # Usage endpoints
        response = client.get(f'/api/regions/{region_id}/usage?user_id=test_region_user')
        assert response.status_code == 200
        
        # DELETE
        response = client.delete(f'/api/regions/{region_id}?user_id=test_region_user')
        assert response.status_code == 204
        
        # Verify isolation
        response = client.get('/api/regions?user_id=different_user')
        assert response.status_code == 200
        regions = response.get_json()
        assert len(regions) == 0
    
    def test_brew_methods_endpoints_support_user_id(self, client):
        """All brew_methods endpoints should support user_id parameter."""
        # CREATE
        response = client.post('/api/brew_methods?user_id=test_brew_method_user', json={
            'name': 'Test Brew Method User1'
        })
        assert response.status_code == 201
        brew_method_data = response.get_json()
        brew_method_id = brew_method_data['id']
        
        # GET all
        response = client.get('/api/brew_methods?user_id=test_brew_method_user')
        assert response.status_code == 200
        brew_methods = response.get_json()
        assert len(brew_methods) == 1
        assert brew_methods[0]['name'] == 'Test Brew Method User1'
        
        # GET specific
        response = client.get(f'/api/brew_methods/{brew_method_id}?user_id=test_brew_method_user')
        assert response.status_code == 200
        
        # UPDATE
        response = client.put(f'/api/brew_methods/{brew_method_id}?user_id=test_brew_method_user', json={
            'name': 'Updated Test Brew Method User1'
        })
        assert response.status_code == 200
        
        # Usage endpoints
        response = client.get(f'/api/brew_methods/{brew_method_id}/usage?user_id=test_brew_method_user')
        assert response.status_code == 200
        
        # DELETE
        response = client.delete(f'/api/brew_methods/{brew_method_id}?user_id=test_brew_method_user')
        assert response.status_code == 204
        
        # Verify isolation
        response = client.get('/api/brew_methods?user_id=different_user')
        assert response.status_code == 200
        brew_methods = response.get_json()
        assert len(brew_methods) == 0
    
    def test_recipes_endpoints_support_user_id(self, client):
        """All recipes endpoints should support user_id parameter."""
        # CREATE
        response = client.post('/api/recipes?user_id=test_recipe_user', json={
            'name': 'Test Recipe User1'
        })
        assert response.status_code == 201
        recipe_data = response.get_json()
        recipe_id = recipe_data['id']
        
        # GET all
        response = client.get('/api/recipes?user_id=test_recipe_user')
        assert response.status_code == 200
        recipes = response.get_json()
        assert len(recipes) == 1
        assert recipes[0]['name'] == 'Test Recipe User1'
        
        # GET specific
        response = client.get(f'/api/recipes/{recipe_id}?user_id=test_recipe_user')
        assert response.status_code == 200
        
        # UPDATE
        response = client.put(f'/api/recipes/{recipe_id}?user_id=test_recipe_user', json={
            'name': 'Updated Test Recipe User1'
        })
        assert response.status_code == 200
        
        # Usage endpoints  
        response = client.get(f'/api/recipes/{recipe_id}/usage?user_id=test_recipe_user')
        assert response.status_code == 200
        
        # DELETE
        response = client.delete(f'/api/recipes/{recipe_id}?user_id=test_recipe_user')
        assert response.status_code == 204
        
        # Verify isolation
        response = client.get('/api/recipes?user_id=different_user')
        assert response.status_code == 200
        recipes = response.get_json()
        assert len(recipes) == 0
    
    def test_grinders_endpoints_support_user_id(self, client):
        """All grinders endpoints should support user_id parameter."""
        # CREATE
        response = client.post('/api/grinders?user_id=test_grinder_user', json={
            'name': 'Test Grinder User1'
        })
        assert response.status_code == 201
        grinder_data = response.get_json()
        grinder_id = grinder_data['id']
        
        # GET all
        response = client.get('/api/grinders?user_id=test_grinder_user')
        assert response.status_code == 200
        grinders = response.get_json()
        assert len(grinders) == 1
        assert grinders[0]['name'] == 'Test Grinder User1'
        
        # GET specific
        response = client.get(f'/api/grinders/{grinder_id}?user_id=test_grinder_user')
        assert response.status_code == 200
        
        # UPDATE
        response = client.put(f'/api/grinders/{grinder_id}?user_id=test_grinder_user', json={
            'name': 'Updated Test Grinder User1'
        })
        assert response.status_code == 200
        
        # Usage endpoints
        response = client.get(f'/api/grinders/{grinder_id}/usage?user_id=test_grinder_user')
        assert response.status_code == 200
        
        # Stats endpoint  
        response = client.get(f'/api/grinders/{grinder_id}/stats?user_id=test_grinder_user')
        assert response.status_code == 200
        
        # DELETE
        response = client.delete(f'/api/grinders/{grinder_id}?user_id=test_grinder_user')
        assert response.status_code == 204
        
        # Verify isolation
        response = client.get('/api/grinders?user_id=different_user')
        assert response.status_code == 200
        grinders = response.get_json()
        assert len(grinders) == 0
    
    def test_filters_endpoints_support_user_id(self, client):
        """All filters endpoints should support user_id parameter."""
        # CREATE
        response = client.post('/api/filters?user_id=test_filter_user', json={
            'name': 'Test Filter User1'
        })
        assert response.status_code == 201
        filter_data = response.get_json()
        filter_id = filter_data['id']
        
        # GET all
        response = client.get('/api/filters?user_id=test_filter_user')
        assert response.status_code == 200
        filters = response.get_json()
        assert len(filters) == 1
        assert filters[0]['name'] == 'Test Filter User1'
        
        # GET specific
        response = client.get(f'/api/filters/{filter_id}?user_id=test_filter_user')
        assert response.status_code == 200
        
        # UPDATE
        response = client.put(f'/api/filters/{filter_id}?user_id=test_filter_user', json={
            'name': 'Updated Test Filter User1'
        })
        assert response.status_code == 200
        
        # Usage endpoints
        response = client.get(f'/api/filters/{filter_id}/usage?user_id=test_filter_user')
        assert response.status_code == 200
        
        # DELETE
        response = client.delete(f'/api/filters/{filter_id}?user_id=test_filter_user')
        assert response.status_code == 204
        
        # Verify isolation
        response = client.get('/api/filters?user_id=different_user')
        assert response.status_code == 200
        filters = response.get_json()
        assert len(filters) == 0
    
    def test_kettles_endpoints_support_user_id(self, client):
        """All kettles endpoints should support user_id parameter."""
        # CREATE
        response = client.post('/api/kettles?user_id=test_kettle_user', json={
            'name': 'Test Kettle User1'
        })
        assert response.status_code == 201
        kettle_data = response.get_json()
        kettle_id = kettle_data['id']
        
        # GET all
        response = client.get('/api/kettles?user_id=test_kettle_user')
        assert response.status_code == 200
        kettles = response.get_json()
        assert len(kettles) == 1
        assert kettles[0]['name'] == 'Test Kettle User1'
        
        # GET specific
        response = client.get(f'/api/kettles/{kettle_id}?user_id=test_kettle_user')
        assert response.status_code == 200
        
        # UPDATE
        response = client.put(f'/api/kettles/{kettle_id}?user_id=test_kettle_user', json={
            'name': 'Updated Test Kettle User1'
        })
        assert response.status_code == 200
        
        # Usage endpoints
        response = client.get(f'/api/kettles/{kettle_id}/usage?user_id=test_kettle_user')
        assert response.status_code == 200
        
        # DELETE
        response = client.delete(f'/api/kettles/{kettle_id}?user_id=test_kettle_user')
        assert response.status_code == 204
        
        # Verify isolation
        response = client.get('/api/kettles?user_id=different_user')
        assert response.status_code == 200
        kettles = response.get_json()
        assert len(kettles) == 0
    
    def test_scales_endpoints_support_user_id(self, client):
        """All scales endpoints should support user_id parameter."""
        # CREATE
        response = client.post('/api/scales?user_id=test_scale_user', json={
            'name': 'Test Scale User1'
        })
        assert response.status_code == 201
        scale_data = response.get_json()
        scale_id = scale_data['id']
        
        # GET all
        response = client.get('/api/scales?user_id=test_scale_user')
        assert response.status_code == 200
        scales = response.get_json()
        assert len(scales) == 1
        assert scales[0]['name'] == 'Test Scale User1'
        
        # GET specific
        response = client.get(f'/api/scales/{scale_id}?user_id=test_scale_user')
        assert response.status_code == 200
        
        # UPDATE
        response = client.put(f'/api/scales/{scale_id}?user_id=test_scale_user', json={
            'name': 'Updated Test Scale User1'
        })
        assert response.status_code == 200
        
        # Usage endpoints
        response = client.get(f'/api/scales/{scale_id}/usage?user_id=test_scale_user')
        assert response.status_code == 200
        
        # DELETE
        response = client.delete(f'/api/scales/{scale_id}?user_id=test_scale_user')
        assert response.status_code == 204
        
        # Verify isolation
        response = client.get('/api/scales?user_id=different_user')
        assert response.status_code == 200
        scales = response.get_json()
        assert len(scales) == 0
    
    def test_decaf_methods_endpoints_support_user_id(self, client):
        """All decaf_methods endpoints should support user_id parameter."""
        # CREATE
        response = client.post('/api/decaf_methods?user_id=test_decaf_user', json={
            'name': 'Test Decaf Method User1'
        })
        assert response.status_code == 201
        decaf_method_data = response.get_json()
        decaf_method_id = decaf_method_data['id']
        
        # GET all
        response = client.get('/api/decaf_methods?user_id=test_decaf_user')
        assert response.status_code == 200
        decaf_methods = response.get_json()
        assert len(decaf_methods) == 1
        assert decaf_methods[0]['name'] == 'Test Decaf Method User1'
        
        # GET specific
        response = client.get(f'/api/decaf_methods/{decaf_method_id}?user_id=test_decaf_user')
        assert response.status_code == 200
        
        # UPDATE
        response = client.put(f'/api/decaf_methods/{decaf_method_id}?user_id=test_decaf_user', json={
            'name': 'Updated Test Decaf Method User1'
        })
        assert response.status_code == 200
        
        # Usage endpoints
        response = client.get(f'/api/decaf_methods/{decaf_method_id}/usage?user_id=test_decaf_user')
        assert response.status_code == 200
        
        # DELETE
        response = client.delete(f'/api/decaf_methods/{decaf_method_id}?user_id=test_decaf_user')
        assert response.status_code == 204
        
        # Verify isolation
        response = client.get('/api/decaf_methods?user_id=different_user')
        assert response.status_code == 200
        decaf_methods = response.get_json()
        assert len(decaf_methods) == 0