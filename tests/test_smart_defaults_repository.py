import pytest
import tempfile
from datetime import datetime, timezone, timedelta
from src.coffeejournal.repositories.factory import RepositoryFactory


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def factory(temp_data_dir):
    """Create repository factory."""
    return RepositoryFactory(storage_type='json', data_dir=temp_data_dir)


class TestEquipmentSmartDefaults:
    """Test smart default calculations for equipment repositories."""
    
    def test_brew_method_smart_default_edge_cases(self, factory):
        """Test brew method smart default edge cases."""
        brew_method_repo = factory.get_brew_method_repository()
        
        # Edge case: Very old usage should have minimal impact
        method1 = brew_method_repo.create({'name': 'Ancient Method'})
        method2 = brew_method_repo.create({'name': 'Modern Method'})
        
        product = factory.get_product_repository().create({'product_name': 'Test', 'roaster_id': 1})
        batch = factory.get_batch_repository().create({'product_id': product['id'], 'roast_date': '2024-01-01', 'amount_grams': 250})
        
        # Create very old sessions for method1
        very_old = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
        for i in range(20):
            session = factory.get_brew_session_repository().create({
                'product_id': product['id'],
                'product_batch_id': batch['id'],
                'brew_method_id': method1['id'],
                'amount_coffee_grams': 20,
                'amount_water_grams': 300
            })
            factory.get_brew_session_repository().update(session['id'], {
                **session,
                'created_at': very_old
            })
        
        # Create one recent session for method2
        recent = datetime.now(timezone.utc).isoformat()
        session = factory.get_brew_session_repository().create({
            'product_id': product['id'],
            'product_batch_id': batch['id'],
            'brew_method_id': method2['id'],
            'amount_coffee_grams': 20,
            'amount_water_grams': 300,
            'created_at': recent
        })
        
        # Despite method1 having 20 uses, they're so old that method2 might win
        smart_default = brew_method_repo.get_smart_default(factory)
        assert smart_default is not None
        # The algorithm should heavily penalize very old entries
    
    def test_grinder_smart_default_with_manual_grams(self, factory):
        """Test grinder smart default doesn't consider manually ground grams."""
        grinder_repo = factory.get_grinder_repository()
        
        # Create grinders with manual grams
        grinder1 = grinder_repo.create({
            'name': 'Manual Heavy',
            'manually_ground_grams': 10000  # 10kg manually ground
        })
        grinder2 = grinder_repo.create({
            'name': 'Session Heavy'
        })
        
        product = factory.get_product_repository().create({'product_name': 'Test', 'roaster_id': 1})
        batch = factory.get_batch_repository().create({'product_id': product['id'], 'roast_date': '2024-01-01', 'amount_grams': 250})
        
        # Create sessions only for grinder2
        now = datetime.now(timezone.utc)
        for i in range(5):
            factory.get_brew_session_repository().create({
                'product_id': product['id'],
                'product_batch_id': batch['id'],
                'grinder_id': grinder2['id'],
                'amount_coffee_grams': 20,
                'amount_water_grams': 300,
                'created_at': now.isoformat()
            })
        
        # Smart default should be grinder2 despite grinder1's manual grams
        smart_default = grinder_repo.get_smart_default(factory)
        assert smart_default['id'] == grinder2['id']
    
    def test_recipe_smart_default_without_sessions(self, factory):
        """Test recipe smart default behavior with no sessions."""
        recipe_repo = factory.get_recipe_repository()
        
        # Create multiple recipes
        recipes = []
        for i in range(5):
            recipe = recipe_repo.create({'name': f'Recipe {i+1}'})
            recipes.append(recipe)
        
        # With no sessions, should return first recipe
        smart_default = recipe_repo.get_smart_default(factory)
        assert smart_default['id'] == recipes[0]['id']
        assert smart_default['name'] == 'Recipe 1'
    
    def test_filter_smart_default_tie_breaking(self, factory):
        """Test filter smart default when multiple items have same score."""
        filter_repo = factory.get_filter_repository()
        
        filter1 = filter_repo.create({'name': 'Filter A'})
        filter2 = filter_repo.create({'name': 'Filter B'})
        
        product = factory.get_product_repository().create({'product_name': 'Test', 'roaster_id': 1})
        batch = factory.get_batch_repository().create({'product_id': product['id'], 'roast_date': '2024-01-01', 'amount_grams': 250})
        
        # Create equal usage for both filters
        now = datetime.now(timezone.utc)
        for filter_id in [filter1['id'], filter2['id']]:
            for i in range(3):
                factory.get_brew_session_repository().create({
                    'product_id': product['id'],
                    'product_batch_id': batch['id'],
                    'filter_id': filter_id,
                    'amount_coffee_grams': 20,
                    'amount_water_grams': 300,
                    'created_at': now.isoformat()
                })
        
        # When tied, should return the first one
        smart_default = filter_repo.get_smart_default(factory)
        assert smart_default['id'] == filter1['id']
    
    def test_kettle_smart_default_recent_within_week(self, factory):
        """Test kettle smart default with all usage within past week."""
        kettle_repo = factory.get_kettle_repository()
        
        kettle1 = kettle_repo.create({'name': 'Yesterday Kettle'})
        kettle2 = kettle_repo.create({'name': 'Today Kettle'})
        
        product = factory.get_product_repository().create({'product_name': 'Test', 'roaster_id': 1})
        batch = factory.get_batch_repository().create({'product_id': product['id'], 'roast_date': '2024-01-01', 'amount_grams': 250})
        
        # Create sessions from yesterday
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        for i in range(3):
            session = factory.get_brew_session_repository().create({
                'product_id': product['id'],
                'product_batch_id': batch['id'],
                'kettle_id': kettle1['id'],
                'amount_coffee_grams': 20,
                'amount_water_grams': 300
            })
            factory.get_brew_session_repository().update(session['id'], {
                **session,
                'created_at': yesterday
            })
        
        # Create one session from today
        today = datetime.now(timezone.utc).isoformat()
        session = factory.get_brew_session_repository().create({
            'product_id': product['id'],
            'product_batch_id': batch['id'],
            'kettle_id': kettle2['id'],
            'amount_coffee_grams': 20,
            'amount_water_grams': 300,
            'created_at': today
        })
        
        # Both are recent, so frequency should dominate
        smart_default = kettle_repo.get_smart_default(factory)
        assert smart_default['id'] == kettle1['id']  # 3 uses vs 1
    
    def test_scale_smart_default_invalid_timestamps(self, factory):
        """Test scale smart default handles invalid timestamps gracefully."""
        scale_repo = factory.get_scale_repository()
        
        scale1 = scale_repo.create({'name': 'Scale 1'})
        scale2 = scale_repo.create({'name': 'Scale 2'})
        
        product = factory.get_product_repository().create({'product_name': 'Test', 'roaster_id': 1})
        batch = factory.get_batch_repository().create({'product_id': product['id'], 'roast_date': '2024-01-01', 'amount_grams': 250})
        
        # Create sessions with various timestamp issues
        session1 = factory.get_brew_session_repository().create({
            'product_id': product['id'],
            'product_batch_id': batch['id'],
            'scale_id': scale1['id'],
            'amount_coffee_grams': 20,
            'amount_water_grams': 300
        })
        # Corrupt the timestamp
        factory.get_brew_session_repository().update(session1['id'], {
            **session1,
            'created_at': 'invalid-timestamp'
        })
        
        # Create valid session for scale2
        factory.get_brew_session_repository().create({
            'product_id': product['id'],
            'product_batch_id': batch['id'],
            'scale_id': scale2['id'],
            'amount_coffee_grams': 20,
            'amount_water_grams': 300,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
        
        # Should handle invalid timestamp gracefully and still calculate
        smart_default = scale_repo.get_smart_default(factory)
        assert smart_default is not None


class TestRoasterSmartDefaults:
    """Test smart default calculations specific to roasters."""
    
    def test_roaster_smart_default_based_on_products(self, factory):
        """Test roaster smart default based on product count."""
        roaster_repo = factory.get_roaster_repository()
        product_repo = factory.get_product_repository()
        
        roaster1 = roaster_repo.create({'name': 'Popular Roaster'})
        roaster2 = roaster_repo.create({'name': 'Occasional Roaster'})
        
        # Create more products for roaster1
        for i in range(5):
            product_repo.create({
                'product_name': f'Coffee {i}',
                'roaster_id': roaster1['id']
            })
        
        # Fewer for roaster2
        product_repo.create({
            'product_name': 'Single Coffee',
            'roaster_id': roaster2['id']
        })
        
        smart_default = roaster_repo.get_smart_default(factory)
        assert smart_default['id'] == roaster1['id']
    
    def test_roaster_smart_default_recent_products(self, factory):
        """Test roaster smart default considers product recency."""
        roaster_repo = factory.get_roaster_repository()
        product_repo = factory.get_product_repository()
        
        roaster1 = roaster_repo.create({'name': 'Old Favorite'})
        roaster2 = roaster_repo.create({'name': 'New Discovery'})
        
        # Create old products for roaster1
        old_time = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
        for i in range(10):
            product = product_repo.create({
                'product_name': f'Old Coffee {i}',
                'roaster_id': roaster1['id']
            })
            product_repo.update(product['id'], {
                **product,
                'created_at': old_time
            })
        
        # Create recent product for roaster2
        recent_product = product_repo.create({
            'product_name': 'Fresh Coffee',
            'roaster_id': roaster2['id'],
            'created_at': datetime.now(timezone.utc).isoformat()
        })
        
        # Algorithm should balance frequency vs recency
        smart_default = roaster_repo.get_smart_default(factory)
        assert smart_default is not None


class TestSmartDefaultEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_repositories(self, factory):
        """Test smart defaults with completely empty repositories."""
        assert factory.get_brew_method_repository().get_smart_default(factory) is None
        assert factory.get_recipe_repository().get_smart_default(factory) is None
        assert factory.get_grinder_repository().get_smart_default(factory) is None
        assert factory.get_filter_repository().get_smart_default(factory) is None
        assert factory.get_kettle_repository().get_smart_default(factory) is None
        assert factory.get_scale_repository().get_smart_default(factory) is None
        assert factory.get_roaster_repository().get_smart_default(factory) is None
    
    def test_smart_default_after_deletion(self, factory):
        """Test smart defaults update correctly after item deletion."""
        grinder_repo = factory.get_grinder_repository()
        
        grinder1 = grinder_repo.create({'name': 'Grinder 1'})
        grinder2 = grinder_repo.create({'name': 'Grinder 2'})
        
        # Set grinder1 as default
        grinder_repo.set_default(grinder1['id'])
        
        # Verify it's the smart default
        assert grinder_repo.get_smart_default(factory)['id'] == grinder1['id']
        
        # Delete grinder1
        grinder_repo.delete(grinder1['id'])
        
        # Smart default should now be grinder2
        smart_default = grinder_repo.get_smart_default(factory)
        assert smart_default['id'] == grinder2['id']
    
    def test_recency_score_boundary(self, factory):
        """Test recency score calculation at 7-day boundary."""
        method_repo = factory.get_brew_method_repository()
        
        method1 = method_repo.create({'name': 'Week Old'})
        method2 = method_repo.create({'name': 'Week Plus'})
        
        product = factory.get_product_repository().create({'product_name': 'Test', 'roaster_id': 1})
        batch = factory.get_batch_repository().create({'product_id': product['id'], 'roast_date': '2024-01-01', 'amount_grams': 250})
        
        # Create session exactly 7 days old (should have recency score of 0)
        week_old = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        session1 = factory.get_brew_session_repository().create({
            'product_id': product['id'],
            'product_batch_id': batch['id'],
            'brew_method_id': method1['id'],
            'amount_coffee_grams': 20,
            'amount_water_grams': 300
        })
        factory.get_brew_session_repository().update(session1['id'], {
            **session1,
            'created_at': week_old
        })
        
        # Create session 8 days old (should also have recency score of 0)
        week_plus = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
        session2 = factory.get_brew_session_repository().create({
            'product_id': product['id'],
            'product_batch_id': batch['id'],
            'brew_method_id': method2['id'],
            'amount_coffee_grams': 20,
            'amount_water_grams': 300
        })
        factory.get_brew_session_repository().update(session2['id'], {
            **session2,
            'created_at': week_plus
        })
        
        # Both have zero recency score, so frequency (1 each) determines
        # Should fall back to first created
        smart_default = method_repo.get_smart_default(factory)
        assert smart_default['id'] == method1['id']