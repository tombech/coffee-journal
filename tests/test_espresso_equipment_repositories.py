"""
Unit tests for espresso equipment repositories.
Tests CRUD operations for brewer, portafilter, basket, tamper, WDT tool, and leveling tool repositories.
"""
import pytest


class TestBrewerRepository:
    """Tests for the Brewer repository."""
    
    def test_create_brewer(self, repo_factory):
        """Test creating a brewer."""
        brewer_repo = repo_factory.get_brewer_repository()
        
        brewer = brewer_repo.create({
            'name': 'Rancilio Silvia',
            'short_form': 'Silvia',
            'description': 'Single boiler espresso machine'
        })
        
        assert brewer['id'] is not None
        assert brewer['name'] == 'Rancilio Silvia'
        assert brewer['short_form'] == 'Silvia'
        assert brewer['description'] == 'Single boiler espresso machine'
        
        # Verify it's persisted
        found_brewer = brewer_repo.find_by_id(brewer['id'])
        assert found_brewer is not None
        assert found_brewer['name'] == 'Rancilio Silvia'
    
    def test_get_or_create_brewer(self, repo_factory):
        """Test get_or_create functionality for brewer."""
        brewer_repo = repo_factory.get_brewer_repository()
        
        # First call should create
        brewer1 = brewer_repo.get_or_create('Gaggia Classic Pro')
        assert brewer1['name'] == 'Gaggia Classic Pro'
        # short_form might be None or set to the name, both are valid
        
        # Second call should return existing
        brewer2 = brewer_repo.get_or_create('Gaggia Classic Pro')
        assert brewer1['id'] == brewer2['id']
    
    def test_update_brewer(self, repo_factory):
        """Test updating a brewer."""
        brewer_repo = repo_factory.get_brewer_repository()
        
        brewer = brewer_repo.create({
            'name': 'Test Brewer',
            'short_form': 'Test'
        })
        brewer_id = brewer['id']
        
        updated_brewer = brewer_repo.update(brewer_id, {
            'name': 'Updated Test Brewer',
            'short_form': 'Updated',
            'description': 'Updated description'
        })
        
        assert updated_brewer['name'] == 'Updated Test Brewer'
        assert updated_brewer['short_form'] == 'Updated'
        assert updated_brewer['description'] == 'Updated description'


class TestPortafilterRepository:
    """Tests for the Portafilter repository."""
    
    def test_create_portafilter(self, repo_factory):
        """Test creating a portafilter."""
        portafilter_repo = repo_factory.get_portafilter_repository()
        
        portafilter = portafilter_repo.create({
            'name': 'Naked Portafilter 58mm',
            'short_form': 'Naked 58',
            'description': 'Bottomless portafilter for visual extraction'
        })
        
        assert portafilter['id'] is not None
        assert portafilter['name'] == 'Naked Portafilter 58mm'
        assert portafilter['short_form'] == 'Naked 58'
        
        # Verify it's persisted
        found_portafilter = portafilter_repo.find_by_id(portafilter['id'])
        assert found_portafilter is not None
        assert found_portafilter['name'] == 'Naked Portafilter 58mm'
    
    def test_get_or_create_portafilter(self, repo_factory):
        """Test get_or_create functionality for portafilter."""
        portafilter_repo = repo_factory.get_portafilter_repository()
        
        # First call should create
        portafilter1 = portafilter_repo.get_or_create('Standard Portafilter 58mm')
        assert portafilter1['name'] == 'Standard Portafilter 58mm'
        
        # Second call should return existing
        portafilter2 = portafilter_repo.get_or_create('Standard Portafilter 58mm')
        assert portafilter1['id'] == portafilter2['id']


class TestBasketRepository:
    """Tests for the Basket repository."""
    
    def test_create_basket(self, repo_factory):
        """Test creating a basket."""
        basket_repo = repo_factory.get_basket_repository()
        
        basket = basket_repo.create({
            'name': 'IMS Precision Basket 18g',
            'short_form': 'IMS 18g',
            'description': 'High precision filter basket'
        })
        
        assert basket['id'] is not None
        assert basket['name'] == 'IMS Precision Basket 18g'
        assert basket['short_form'] == 'IMS 18g'
        
        # Verify it's persisted
        found_basket = basket_repo.find_by_id(basket['id'])
        assert found_basket is not None
        assert found_basket['name'] == 'IMS Precision Basket 18g'
    
    def test_get_or_create_basket(self, repo_factory):
        """Test get_or_create functionality for basket."""
        basket_repo = repo_factory.get_basket_repository()
        
        # First call should create
        basket1 = basket_repo.get_or_create('Standard Basket 14-18g')
        assert basket1['name'] == 'Standard Basket 14-18g'
        
        # Second call should return existing
        basket2 = basket_repo.get_or_create('Standard Basket 14-18g')
        assert basket1['id'] == basket2['id']


class TestTamperRepository:
    """Tests for the Tamper repository."""
    
    def test_create_tamper(self, repo_factory):
        """Test creating a tamper."""
        tamper_repo = repo_factory.get_tamper_repository()
        
        tamper = tamper_repo.create({
            'name': 'Pullman BigStep 58.35mm',
            'short_form': 'Pullman BigStep',
            'description': 'Precision machined tamper with stepped design'
        })
        
        assert tamper['id'] is not None
        assert tamper['name'] == 'Pullman BigStep 58.35mm'
        assert tamper['short_form'] == 'Pullman BigStep'
        
        # Verify it's persisted
        found_tamper = tamper_repo.find_by_id(tamper['id'])
        assert found_tamper is not None
        assert found_tamper['name'] == 'Pullman BigStep 58.35mm'
    
    def test_get_or_create_tamper(self, repo_factory):
        """Test get_or_create functionality for tamper."""
        tamper_repo = repo_factory.get_tamper_repository()
        
        # First call should create
        tamper1 = tamper_repo.get_or_create('Standard Flat Tamper 58mm')
        assert tamper1['name'] == 'Standard Flat Tamper 58mm'
        
        # Second call should return existing
        tamper2 = tamper_repo.get_or_create('Standard Flat Tamper 58mm')
        assert tamper1['id'] == tamper2['id']


class TestWDTToolRepository:
    """Tests for the WDT Tool repository."""
    
    def test_create_wdt_tool(self, repo_factory):
        """Test creating a WDT tool."""
        wdt_tool_repo = repo_factory.get_wdt_tool_repository()
        
        wdt_tool = wdt_tool_repo.create({
            'name': 'Weber Workshops WDT Tool',
            'short_form': 'Weber WDT',
            'description': 'Weiss Distribution Technique tool with fine needles'
        })
        
        assert wdt_tool['id'] is not None
        assert wdt_tool['name'] == 'Weber Workshops WDT Tool'
        assert wdt_tool['short_form'] == 'Weber WDT'
        
        # Verify it's persisted
        found_wdt_tool = wdt_tool_repo.find_by_id(wdt_tool['id'])
        assert found_wdt_tool is not None
        assert found_wdt_tool['name'] == 'Weber Workshops WDT Tool'
    
    def test_get_or_create_wdt_tool(self, repo_factory):
        """Test get_or_create functionality for WDT tool."""
        wdt_tool_repo = repo_factory.get_wdt_tool_repository()
        
        # First call should create
        wdt_tool1 = wdt_tool_repo.get_or_create('DIY WDT Tool')
        assert wdt_tool1['name'] == 'DIY WDT Tool'
        
        # Second call should return existing
        wdt_tool2 = wdt_tool_repo.get_or_create('DIY WDT Tool')
        assert wdt_tool1['id'] == wdt_tool2['id']


class TestLevelingToolRepository:
    """Tests for the Leveling Tool repository."""
    
    def test_create_leveling_tool(self, repo_factory):
        """Test creating a leveling tool."""
        leveling_tool_repo = repo_factory.get_leveling_tool_repository()
        
        leveling_tool = leveling_tool_repo.create({
            'name': 'OCD (Ona Coffee Distributor) V4',
            'short_form': 'OCD V4',
            'description': 'Coffee distribution and leveling tool'
        })
        
        assert leveling_tool['id'] is not None
        assert leveling_tool['name'] == 'OCD (Ona Coffee Distributor) V4'
        assert leveling_tool['short_form'] == 'OCD V4'
        
        # Verify it's persisted
        found_leveling_tool = leveling_tool_repo.find_by_id(leveling_tool['id'])
        assert found_leveling_tool is not None
        assert found_leveling_tool['name'] == 'OCD (Ona Coffee Distributor) V4'
    
    def test_get_or_create_leveling_tool(self, repo_factory):
        """Test get_or_create functionality for leveling tool."""
        leveling_tool_repo = repo_factory.get_leveling_tool_repository()
        
        # First call should create
        leveling_tool1 = leveling_tool_repo.get_or_create('Basic Distribution Tool')
        assert leveling_tool1['name'] == 'Basic Distribution Tool'
        
        # Second call should return existing
        leveling_tool2 = leveling_tool_repo.get_or_create('Basic Distribution Tool')
        assert leveling_tool1['id'] == leveling_tool2['id']


class TestEspressoEquipmentIntegration:
    """Test integration between espresso equipment and shots."""
    
    def test_shot_with_espresso_equipment(self, repo_factory):
        """Test creating a shot with espresso equipment."""
        brewer_repo = repo_factory.get_brewer_repository()
        portafilter_repo = repo_factory.get_portafilter_repository()
        basket_repo = repo_factory.get_basket_repository()
        shot_repo = repo_factory.get_shot_repository()
        
        # Create equipment
        brewer = brewer_repo.create({'name': 'Test Brewer Integration'})
        portafilter = portafilter_repo.create({'name': 'Test Portafilter Integration'})
        basket = basket_repo.create({'name': 'Test Basket Integration'})
        
        # Create a shot using this equipment
        shot = shot_repo.create({
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': brewer['id'],
            'portafilter_id': portafilter['id'],
            'basket_id': basket['id'],
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 25,
            'water_temperature_c': 93,
            'extraction_status': 'perfect',
            'overall_score': 8
        })
        
        # Verify the shot references the equipment
        assert shot['brewer_id'] == brewer['id']
        assert shot['portafilter_id'] == portafilter['id']
        assert shot['basket_id'] == basket['id']
        
        # Verify the shot can be retrieved
        found_shot = shot_repo.find_by_id(shot['id'])
        assert found_shot is not None
        assert found_shot['brewer_id'] == brewer['id']