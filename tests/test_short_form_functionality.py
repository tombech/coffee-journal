"""
Test short_form functionality for lookup repositories.
"""
import pytest
import tempfile
import os
from coffeejournal.repositories.json_repository import RoasterRepository, BrewMethodRepository


class TestShortFormRepository:
    """Test short_form functionality in lookup repositories."""
    
    def setup_method(self):
        """Set up test data directory."""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up test data directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_find_by_short_form(self):
        """Test finding lookup items by short_form."""
        repo = RoasterRepository(self.temp_dir)
        
        # Create item with short_form
        item = repo.create({
            'name': 'Blue Bottle Coffee',
            'short_form': 'BB',
            'description': 'Premium coffee roaster'
        })
        
        # Test finding by short_form
        found = repo.find_by_short_form('BB')
        assert found is not None
        assert found['name'] == 'Blue Bottle Coffee'
        assert found['short_form'] == 'BB'
        assert found['id'] == item['id']
        
        # Test finding non-existent short_form
        not_found = repo.find_by_short_form('XYZ')
        assert not_found is None
    
    def test_find_by_name_or_short_form(self):
        """Test finding lookup items by name or short_form."""
        repo = BrewMethodRepository(self.temp_dir)
        
        # Create item with short_form
        item = repo.create({
            'name': 'French Press',
            'short_form': 'FP'
        })
        
        # Test finding by name
        found_by_name = repo.find_by_name_or_short_form('French Press')
        assert found_by_name is not None
        assert found_by_name['id'] == item['id']
        
        # Test finding by short_form
        found_by_short = repo.find_by_name_or_short_form('FP')
        assert found_by_short is not None
        assert found_by_short['id'] == item['id']
        
        # Test finding non-existent identifier
        not_found = repo.find_by_name_or_short_form('NonExistent')
        assert not_found is None
    
    def test_get_or_create_by_identifier_existing_name(self):
        """Test get_or_create_by_identifier with existing item found by name."""
        repo = RoasterRepository(self.temp_dir)
        
        # Create item
        original = repo.create({
            'name': 'Intelligentsia',
            'short_form': 'INT',
            'description': 'Chicago-based roaster'
        })
        
        # Get by name should return existing item
        result = repo.get_or_create_by_identifier('Intelligentsia')
        assert result['id'] == original['id']
        assert result['name'] == 'Intelligentsia'
        assert result['short_form'] == 'INT'
        
        # Verify no new item was created
        all_items = repo.find_all()
        assert len(all_items) == 1
    
    def test_get_or_create_by_identifier_existing_short_form(self):
        """Test get_or_create_by_identifier with existing item found by short_form."""
        repo = BrewMethodRepository(self.temp_dir)
        
        # Create item
        original = repo.create({
            'name': 'AeroPress',
            'short_form': 'AP',
            'description': 'Immersion brewing method'
        })
        
        # Get by short_form should return existing item
        result = repo.get_or_create_by_identifier('AP')
        assert result['id'] == original['id']
        assert result['name'] == 'AeroPress'
        assert result['short_form'] == 'AP'
        
        # Verify no new item was created
        all_items = repo.find_all()
        assert len(all_items) == 1
    
    def test_get_or_create_by_identifier_new_item(self):
        """Test get_or_create_by_identifier creating new item."""
        repo = RoasterRepository(self.temp_dir)
        
        # Create new item by identifier
        result = repo.get_or_create_by_identifier('Stumptown Coffee')
        assert result['name'] == 'Stumptown Coffee'
        assert result['id'] is not None
        
        # Verify item was created
        found = repo.find_by_name('Stumptown Coffee')
        assert found is not None
        assert found['id'] == result['id']
    
    def test_get_or_create_by_identifier_with_kwargs(self):
        """Test get_or_create_by_identifier with additional kwargs."""
        repo = BrewMethodRepository(self.temp_dir)
        
        # Create new item with additional data
        result = repo.get_or_create_by_identifier(
            'Chemex',
            short_form='CMX',
            description='Pour-over brewing method'
        )
        
        assert result['name'] == 'Chemex'
        assert result['short_form'] == 'CMX'
        assert result['description'] == 'Pour-over brewing method'
        
        # Verify additional data was saved
        found = repo.find_by_name('Chemex')
        assert found['short_form'] == 'CMX'
        assert found['description'] == 'Pour-over brewing method'
    
    def test_short_form_case_sensitivity(self):
        """Test that short_form searches are case sensitive."""
        repo = RoasterRepository(self.temp_dir)
        
        # Create item with uppercase short_form
        repo.create({
            'name': 'La Colombe',
            'short_form': 'LC'
        })
        
        # Test exact case match
        found_exact = repo.find_by_short_form('LC')
        assert found_exact is not None
        
        # Test different case (should not match)
        found_lower = repo.find_by_short_form('lc')
        assert found_lower is None
        
        found_mixed = repo.find_by_short_form('Lc')
        assert found_mixed is None
    
    def test_empty_short_form_handling(self):
        """Test handling of empty or None short_form values."""
        repo = BrewMethodRepository(self.temp_dir)
        
        # Create item without short_form
        item1 = repo.create({'name': 'V60'})
        
        # Create item with empty short_form
        item2 = repo.create({
            'name': 'Espresso',
            'short_form': ''
        })
        
        # Create item with None short_form
        item3 = repo.create({
            'name': 'Cold Brew',
            'short_form': None
        })
        
        # Test that empty/None short_forms don't match searches
        assert repo.find_by_short_form('') is None
        assert repo.find_by_short_form(None) is None
        
        # Test that items can still be found by name
        assert repo.find_by_name('V60')['id'] == item1['id']
        assert repo.find_by_name('Espresso')['id'] == item2['id']
        assert repo.find_by_name('Cold Brew')['id'] == item3['id']
    
    def test_duplicate_short_forms_not_enforced(self):
        """Test that duplicate short_forms are not prevented (business logic choice)."""
        repo = RoasterRepository(self.temp_dir)
        
        # Create first item with short_form
        item1 = repo.create({
            'name': 'Blue Bottle',
            'short_form': 'BB'
        })
        
        # Create second item with same short_form (should be allowed)
        item2 = repo.create({
            'name': 'Black Bear',
            'short_form': 'BB'
        })
        
        # Both items should exist
        assert item1['id'] != item2['id']
        all_items = repo.find_all()
        assert len(all_items) == 2
        
        # find_by_short_form should return the first match
        found = repo.find_by_short_form('BB')
        assert found['id'] == item1['id']  # Should return first match