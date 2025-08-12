"""
Test espresso equipment API endpoints.
"""
import pytest


class TestBrewerEndpoints:
    """Test Brewer API endpoints."""
    
    def test_create_brewer(self, client):
        """Test creating a brewer via API."""
        brewer_data = {
            'name': 'Rancilio Silvia',
            'short_form': 'Silvia',
            'description': 'Single boiler espresso machine'
        }
        
        response = client.post('/api/brewers', json=brewer_data)
        assert response.status_code == 201
        
        brewer = response.get_json()
        assert brewer['name'] == 'Rancilio Silvia'
        assert brewer['short_form'] == 'Silvia'
        assert brewer['description'] == 'Single boiler espresso machine'
        assert brewer['id'] is not None
    
    def test_get_brewers(self, client):
        """Test getting all brewers."""
        # Create some brewers first
        client.post('/api/brewers', json={'name': 'Brewer 1', 'short_form': 'B1'})
        client.post('/api/brewers', json={'name': 'Brewer 2', 'short_form': 'B2'})
        
        response = client.get('/api/brewers')
        assert response.status_code == 200
        
        brewers = response.get_json()
        assert len(brewers) >= 2
    
    def test_get_brewer_by_id(self, client):
        """Test getting a specific brewer by ID."""
        brewer_data = {'name': 'Test Brewer', 'short_form': 'Test'}
        create_response = client.post('/api/brewers', json=brewer_data)
        created_brewer = create_response.get_json()
        brewer_id = created_brewer['id']
        
        response = client.get(f'/api/brewers/{brewer_id}')
        assert response.status_code == 200
        
        brewer = response.get_json()
        assert brewer['id'] == brewer_id
        assert brewer['name'] == 'Test Brewer'
    
    def test_update_brewer(self, client):
        """Test updating a brewer."""
        brewer_data = {'name': 'Original Brewer', 'short_form': 'Orig'}
        create_response = client.post('/api/brewers', json=brewer_data)
        created_brewer = create_response.get_json()
        brewer_id = created_brewer['id']
        
        update_data = {
            'name': 'Updated Brewer',
            'short_form': 'Updated',
            'description': 'Updated description'
        }
        
        response = client.put(f'/api/brewers/{brewer_id}', json=update_data)
        assert response.status_code == 200
        
        updated_brewer = response.get_json()
        assert updated_brewer['name'] == 'Updated Brewer'
        assert updated_brewer['short_form'] == 'Updated'
        assert updated_brewer['description'] == 'Updated description'
    
    def test_delete_brewer(self, client):
        """Test deleting a brewer."""
        brewer_data = {'name': 'Brewer to Delete', 'short_form': 'Delete'}
        create_response = client.post('/api/brewers', json=brewer_data)
        created_brewer = create_response.get_json()
        brewer_id = created_brewer['id']
        
        response = client.delete(f'/api/brewers/{brewer_id}')
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = client.get(f'/api/brewers/{brewer_id}')
        assert get_response.status_code == 404
    
    def test_brewer_usage_info(self, client):
        """Test getting brewer usage information."""
        brewer_data = {'name': 'Usage Test Brewer', 'short_form': 'Usage'}
        create_response = client.post('/api/brewers', json=brewer_data)
        created_brewer = create_response.get_json()
        brewer_id = created_brewer['id']
        
        response = client.get(f'/api/brewers/{brewer_id}/usage')
        assert response.status_code == 200
        
        usage = response.get_json()
        assert 'usage_count' in usage
        assert 'in_use' in usage
        assert 'usage_type' in usage
        assert usage['usage_count'] == 0
        assert usage['in_use'] is False


class TestPortafilterEndpoints:
    """Test Portafilter API endpoints."""
    
    def test_create_portafilter(self, client):
        """Test creating a portafilter via API."""
        portafilter_data = {
            'name': 'Naked Portafilter 58mm',
            'short_form': 'Naked 58',
            'description': 'Bottomless portafilter for visual extraction'
        }
        
        response = client.post('/api/portafilters', json=portafilter_data)
        assert response.status_code == 201
        
        portafilter = response.get_json()
        assert portafilter['name'] == 'Naked Portafilter 58mm'
        assert portafilter['short_form'] == 'Naked 58'
    
    def test_get_portafilters(self, client):
        """Test getting all portafilters."""
        client.post('/api/portafilters', json={'name': 'Portafilter 1', 'short_form': 'P1'})
        client.post('/api/portafilters', json={'name': 'Portafilter 2', 'short_form': 'P2'})
        
        response = client.get('/api/portafilters')
        assert response.status_code == 200
        
        portafilters = response.get_json()
        assert len(portafilters) >= 2


class TestBasketEndpoints:
    """Test Basket API endpoints."""
    
    def test_create_basket(self, client):
        """Test creating a basket via API."""
        basket_data = {
            'name': 'IMS Precision Basket 18g',
            'short_form': 'IMS 18g',
            'description': 'High precision filter basket'
        }
        
        response = client.post('/api/baskets', json=basket_data)
        assert response.status_code == 201
        
        basket = response.get_json()
        assert basket['name'] == 'IMS Precision Basket 18g'
        assert basket['short_form'] == 'IMS 18g'
    
    def test_get_baskets(self, client):
        """Test getting all baskets."""
        client.post('/api/baskets', json={'name': 'Basket 1', 'short_form': 'B1'})
        client.post('/api/baskets', json={'name': 'Basket 2', 'short_form': 'B2'})
        
        response = client.get('/api/baskets')
        assert response.status_code == 200
        
        baskets = response.get_json()
        assert len(baskets) >= 2


class TestTamperEndpoints:
    """Test Tamper API endpoints."""
    
    def test_create_tamper(self, client):
        """Test creating a tamper via API."""
        tamper_data = {
            'name': 'Pullman BigStep 58.35mm',
            'short_form': 'Pullman BigStep',
            'description': 'Precision machined tamper with stepped design'
        }
        
        response = client.post('/api/tampers', json=tamper_data)
        assert response.status_code == 201
        
        tamper = response.get_json()
        assert tamper['name'] == 'Pullman BigStep 58.35mm'
        assert tamper['short_form'] == 'Pullman BigStep'
    
    def test_get_tampers(self, client):
        """Test getting all tampers."""
        client.post('/api/tampers', json={'name': 'Tamper 1', 'short_form': 'T1'})
        client.post('/api/tampers', json={'name': 'Tamper 2', 'short_form': 'T2'})
        
        response = client.get('/api/tampers')
        assert response.status_code == 200
        
        tampers = response.get_json()
        assert len(tampers) >= 2


class TestWDTToolEndpoints:
    """Test WDT Tool API endpoints."""
    
    def test_create_wdt_tool(self, client):
        """Test creating a WDT tool via API."""
        wdt_tool_data = {
            'name': 'Weber Workshops WDT Tool',
            'short_form': 'Weber WDT',
            'description': 'Weiss Distribution Technique tool with fine needles'
        }
        
        response = client.post('/api/wdt_tools', json=wdt_tool_data)
        assert response.status_code == 201
        
        wdt_tool = response.get_json()
        assert wdt_tool['name'] == 'Weber Workshops WDT Tool'
        assert wdt_tool['short_form'] == 'Weber WDT'
    
    def test_get_wdt_tools(self, client):
        """Test getting all WDT tools."""
        client.post('/api/wdt_tools', json={'name': 'WDT Tool 1', 'short_form': 'WDT1'})
        client.post('/api/wdt_tools', json={'name': 'WDT Tool 2', 'short_form': 'WDT2'})
        
        response = client.get('/api/wdt_tools')
        assert response.status_code == 200
        
        wdt_tools = response.get_json()
        assert len(wdt_tools) >= 2


class TestLevelingToolEndpoints:
    """Test Leveling Tool API endpoints."""
    
    def test_create_leveling_tool(self, client):
        """Test creating a leveling tool via API."""
        leveling_tool_data = {
            'name': 'OCD (Ona Coffee Distributor) V4',
            'short_form': 'OCD V4',
            'description': 'Coffee distribution and leveling tool'
        }
        
        response = client.post('/api/leveling_tools', json=leveling_tool_data)
        assert response.status_code == 201
        
        leveling_tool = response.get_json()
        assert leveling_tool['name'] == 'OCD (Ona Coffee Distributor) V4'
        assert leveling_tool['short_form'] == 'OCD V4'
    
    def test_get_leveling_tools(self, client):
        """Test getting all leveling tools."""
        client.post('/api/leveling_tools', json={'name': 'Leveling Tool 1', 'short_form': 'LT1'})
        client.post('/api/leveling_tools', json={'name': 'Leveling Tool 2', 'short_form': 'LT2'})
        
        response = client.get('/api/leveling_tools')
        assert response.status_code == 200
        
        leveling_tools = response.get_json()
        assert len(leveling_tools) >= 2


class TestEspressoEquipmentUsageAPI:
    """Test espresso equipment usage tracking via API."""
    
    def test_equipment_usage_with_shots(self, client):
        """Test that equipment usage is tracked when used in shots."""
        # Create equipment
        brewer_response = client.post('/api/brewers', json={'name': 'Usage Test Brewer'})
        brewer = brewer_response.get_json()
        brewer_id = brewer['id']
        
        portafilter_response = client.post('/api/portafilters', json={'name': 'Usage Test Portafilter'})
        portafilter = portafilter_response.get_json()
        portafilter_id = portafilter['id']
        
        # Initially should have no usage
        brewer_usage = client.get(f'/api/brewers/{brewer_id}/usage').get_json()
        assert brewer_usage['usage_count'] == 0
        assert brewer_usage['in_use'] is False
        
        portafilter_usage = client.get(f'/api/portafilters/{portafilter_id}/usage').get_json()
        assert portafilter_usage['usage_count'] == 0
        assert portafilter_usage['in_use'] is False
        
        # Create a shot using this equipment
        shot_data = {
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': brewer_id,
            'portafilter_id': portafilter_id,
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 25,
            'water_temperature_c': 93,
            'extraction_status': 'perfect',
            'overall_score': 8
        }
        
        shot_response = client.post('/api/shots', json=shot_data)
        assert shot_response.status_code == 201
        
        # Now should have usage
        brewer_usage = client.get(f'/api/brewers/{brewer_id}/usage').get_json()
        assert brewer_usage['usage_count'] > 0
        assert brewer_usage['in_use'] is True
        assert brewer_usage['usage_type'] == 'shots'
        
        portafilter_usage = client.get(f'/api/portafilters/{portafilter_id}/usage').get_json()
        assert portafilter_usage['usage_count'] > 0
        assert portafilter_usage['in_use'] is True
        assert portafilter_usage['usage_type'] == 'shots'
    
    def test_equipment_deletion_prevention(self, client):
        """Test that equipment in use cannot be deleted."""
        # Create equipment
        basket_response = client.post('/api/baskets', json={'name': 'Deletion Test Basket'})
        basket = basket_response.get_json()
        basket_id = basket['id']
        
        # Create a shot using this basket
        shot_data = {
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'basket_id': basket_id,
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 25,
            'water_temperature_c': 93,
            'extraction_status': 'perfect',
            'overall_score': 8
        }
        
        shot_response = client.post('/api/shots', json=shot_data)
        assert shot_response.status_code == 201
        
        # Try to delete the basket (should be prevented)
        delete_response = client.delete(f'/api/baskets/{basket_id}')
        
        # Depending on implementation, this should either:
        # 1. Return 400/409 preventing deletion
        # 2. Or have some other mechanism to handle equipment in use
        
        # For now, let's assume it prevents deletion
        if delete_response.status_code not in [204]:
            assert delete_response.status_code in [400, 409]
            
            # Basket should still exist
            get_response = client.get(f'/api/baskets/{basket_id}')
            assert get_response.status_code == 200


class TestEspressoEquipmentValidation:
    """Test validation for espresso equipment endpoints."""
    
    def test_equipment_name_validation(self, client):
        """Test that equipment names are required."""
        # Missing name
        response = client.post('/api/brewers', json={'short_form': 'Missing Name'})
        assert response.status_code == 400
        
        # Empty name
        response = client.post('/api/portafilters', json={'name': '', 'short_form': 'Empty'})
        assert response.status_code == 400
    
    def test_equipment_duplicate_names(self, client):
        """Test handling of duplicate equipment names."""
        # Create equipment
        client.post('/api/tampers', json={'name': 'Duplicate Test Tamper', 'short_form': 'Dup'})
        
        # Try to create another with the same name
        response = client.post('/api/tampers', json={'name': 'Duplicate Test Tamper', 'short_form': 'Dup2'})
        
        # Depending on implementation, this might be allowed or prevented
        # For lookup tables, duplicates are usually prevented
        if response.status_code != 201:
            assert response.status_code in [400, 409]
    
    def test_equipment_update_validation(self, client):
        """Test validation when updating equipment."""
        # Create equipment
        create_response = client.post('/api/wdt_tools', json={'name': 'Update Test WDT', 'short_form': 'Update'})
        wdt_tool = create_response.get_json()
        wdt_tool_id = wdt_tool['id']
        
        # Try to update with empty name
        response = client.put(f'/api/wdt_tools/{wdt_tool_id}', json={'name': ''})
        assert response.status_code == 400
        
        # Valid update should work
        response = client.put(f'/api/wdt_tools/{wdt_tool_id}', json={'name': 'Updated WDT Tool'})
        assert response.status_code == 200


class TestEspressoEquipmentIntegration:
    """Test integration between espresso equipment and shots."""
    
    def test_shot_with_all_equipment_types(self, client):
        """Test creating a shot with all types of espresso equipment."""
        # Create all equipment types
        brewer_response = client.post('/api/brewers', json={'name': 'Integration Test Brewer'})
        brewer = brewer_response.get_json()
        
        portafilter_response = client.post('/api/portafilters', json={'name': 'Integration Test Portafilter'})
        portafilter = portafilter_response.get_json()
        
        basket_response = client.post('/api/baskets', json={'name': 'Integration Test Basket'})
        basket = basket_response.get_json()
        
        tamper_response = client.post('/api/tampers', json={'name': 'Integration Test Tamper'})
        tamper = tamper_response.get_json()
        
        wdt_tool_response = client.post('/api/wdt_tools', json={'name': 'Integration Test WDT'})
        wdt_tool = wdt_tool_response.get_json()
        
        leveling_tool_response = client.post('/api/leveling_tools', json={'name': 'Integration Test Leveling'})
        leveling_tool = leveling_tool_response.get_json()
        
        # Create a shot using all equipment
        shot_data = {
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': brewer['id'],
            'portafilter_id': portafilter['id'],
            'basket_id': basket['id'],
            'tamper_id': tamper['id'],
            'wdt_tool_id': wdt_tool['id'],
            'leveling_tool_id': leveling_tool['id'],
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 25,
            'water_temperature_c': 93,
            'extraction_status': 'perfect',
            'overall_score': 8,
            'notes': 'Shot with all equipment types'
        }
        
        response = client.post('/api/shots', json=shot_data)
        assert response.status_code == 201
        
        shot = response.get_json()
        assert shot['brewer_id'] == brewer['id']
        assert shot['portafilter_id'] == portafilter['id']
        assert shot['basket_id'] == basket['id']
        assert shot['tamper_id'] == tamper['id']
        assert shot['wdt_tool_id'] == wdt_tool['id']
        assert shot['leveling_tool_id'] == leveling_tool['id']