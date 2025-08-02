import pytest
import tempfile
import os
from src.coffeejournal.repositories.factory import RepositoryFactory
from src.coffeejournal.repositories.json_repository import (
    GrinderRepository, BrewSessionRepository, ProductRepository, BatchRepository
)


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def repositories(temp_data_dir):
    """Create repository instances."""
    factory = RepositoryFactory(storage_type='json', data_dir=temp_data_dir)
    return {
        'factory': factory,
        'grinder': factory.get_grinder_repository(),
        'product': factory.get_product_repository(),
        'batch': factory.get_batch_repository(),
        'brew_session': factory.get_brew_session_repository()
    }


def test_grinder_stats_no_sessions(repositories):
    """Test grinder stats with no brew sessions."""
    grinder_repo = repositories['grinder']
    
    # Create a grinder
    grinder = grinder_repo.create({
        'name': 'Test Grinder',
        'manually_ground_grams': 50
    })
    
    # Get stats
    stats = grinder_repo.get_usage_stats(grinder['id'], repositories['factory'])
    
    assert stats['total_brews'] == 0
    assert stats['total_grams_ground'] == 0
    assert stats['manually_ground_grams'] == 50
    assert stats['total_grams_with_manual'] == 50
    assert stats['total_kilos'] == 0  # Less than 1000g


def test_grinder_stats_with_sessions(repositories):
    """Test grinder stats with brew sessions."""
    grinder_repo = repositories['grinder']
    product_repo = repositories['product']
    batch_repo = repositories['batch']
    session_repo = repositories['brew_session']
    
    # Create test data
    grinder = grinder_repo.create({
        'name': 'Test Grinder',
        'manually_ground_grams': 100
    })
    
    product = product_repo.create({
        'name': 'Test Coffee',
        'roaster_id': 1
    })
    
    batch = batch_repo.create({
        'product_id': product['id'],
        'amount_grams': 250,
        'price': 15.00
    })
    
    # Create brew sessions with this grinder
    session1 = session_repo.create({
        'product_id': product['id'],
        'product_batch_id': batch['id'],
        'grinder_id': grinder['id'],
        'amount_coffee_grams': 20,
        'amount_water_grams': 300
    })
    
    session2 = session_repo.create({
        'product_id': product['id'],
        'product_batch_id': batch['id'],
        'grinder_id': grinder['id'],
        'amount_coffee_grams': 25,
        'amount_water_grams': 375
    })
    
    # Get stats
    stats = grinder_repo.get_usage_stats(grinder['id'], repositories['factory'])
    
    assert stats['total_brews'] == 2
    assert stats['total_grams_ground'] == 45  # 20 + 25
    assert stats['manually_ground_grams'] == 100
    assert stats['total_grams_with_manual'] == 145  # 45 + 100
    assert stats['total_kilos'] == 0  # Less than 1000g


def test_grinder_stats_over_1kg(repositories):
    """Test grinder stats with over 1kg total."""
    grinder_repo = repositories['grinder']
    product_repo = repositories['product']
    batch_repo = repositories['batch']
    session_repo = repositories['brew_session']
    
    # Create test data
    grinder = grinder_repo.create({
        'name': 'Heavy Use Grinder',
        'manually_ground_grams': 800
    })
    
    product = product_repo.create({
        'name': 'Test Coffee',
        'roaster_id': 1
    })
    
    batch = batch_repo.create({
        'product_id': product['id'],
        'amount_grams': 250,
        'price': 15.00
    })
    
    # Create sessions totaling over 1kg when combined with manual offset
    for i in range(10):
        session_repo.create({
            'product_id': product['id'],
            'product_batch_id': batch['id'],
            'grinder_id': grinder['id'],
            'amount_coffee_grams': 30,  # 10 * 30 = 300g
            'amount_water_grams': 450
        })
    
    # Get stats
    stats = grinder_repo.get_usage_stats(grinder['id'], repositories['factory'])
    
    assert stats['total_brews'] == 10
    assert stats['total_grams_ground'] == 300  # 10 * 30
    assert stats['manually_ground_grams'] == 800
    assert stats['total_grams_with_manual'] == 1100  # 300 + 800
    assert stats['total_kilos'] == 1.1  # 1100g = 1.1kg


def test_grinder_stats_no_manual_offset(repositories):
    """Test grinder stats with no manual offset."""
    grinder_repo = repositories['grinder']
    product_repo = repositories['product']
    batch_repo = repositories['batch']
    session_repo = repositories['brew_session']
    
    # Create grinder without manually_ground_grams field
    grinder = grinder_repo.create({
        'name': 'Clean Grinder'
        # No manually_ground_grams field
    })
    
    product = product_repo.create({
        'name': 'Test Coffee',
        'roaster_id': 1
    })
    
    batch = batch_repo.create({
        'product_id': product['id'],
        'amount_grams': 250,
        'price': 15.00
    })
    
    session_repo.create({
        'product_id': product['id'],
        'product_batch_id': batch['id'],
        'grinder_id': grinder['id'],
        'amount_coffee_grams': 20,
        'amount_water_grams': 300
    })
    
    # Get stats
    stats = grinder_repo.get_usage_stats(grinder['id'], repositories['factory'])
    
    assert stats['total_brews'] == 1
    assert stats['total_grams_ground'] == 20
    assert stats['manually_ground_grams'] == 0  # Default when field missing
    assert stats['total_grams_with_manual'] == 20
    assert stats['total_kilos'] == 0


def test_grinder_stats_sessions_without_coffee_amount(repositories):
    """Test grinder stats with sessions missing coffee amount."""
    grinder_repo = repositories['grinder']
    product_repo = repositories['product']
    batch_repo = repositories['batch']
    session_repo = repositories['brew_session']
    
    # Create test data
    grinder = grinder_repo.create({
        'name': 'Test Grinder',
        'manually_ground_grams': 0
    })
    
    product = product_repo.create({
        'name': 'Test Coffee',
        'roaster_id': 1
    })
    
    batch = batch_repo.create({
        'product_id': product['id'],
        'amount_grams': 250,
        'price': 15.00
    })
    
    # Create sessions with missing or zero coffee amounts
    session1 = session_repo.create({
        'product_id': product['id'],
        'product_batch_id': batch['id'],
        'grinder_id': grinder['id'],
        # No amount_coffee_grams field
        'amount_water_grams': 300
    })
    
    session2 = session_repo.create({
        'product_id': product['id'],
        'product_batch_id': batch['id'],
        'grinder_id': grinder['id'],
        'amount_coffee_grams': 0,  # Zero amount
        'amount_water_grams': 300
    })
    
    session3 = session_repo.create({
        'product_id': product['id'],
        'product_batch_id': batch['id'],
        'grinder_id': grinder['id'],
        'amount_coffee_grams': 18,  # Valid amount
        'amount_water_grams': 270
    })
    
    # Get stats
    stats = grinder_repo.get_usage_stats(grinder['id'], repositories['factory'])
    
    assert stats['total_brews'] == 3  # All sessions counted for brew count
    assert stats['total_grams_ground'] == 18  # Only session3 contributes
    assert stats['manually_ground_grams'] == 0
    assert stats['total_grams_with_manual'] == 18
    assert stats['total_kilos'] == 0


def test_grinder_stats_different_grinders(repositories):
    """Test that stats are isolated per grinder."""
    grinder_repo = repositories['grinder']
    product_repo = repositories['product']
    batch_repo = repositories['batch']
    session_repo = repositories['brew_session']
    
    # Create two grinders
    grinder1 = grinder_repo.create({
        'name': 'Grinder 1',
        'manually_ground_grams': 50
    })
    
    grinder2 = grinder_repo.create({
        'name': 'Grinder 2',
        'manually_ground_grams': 100
    })
    
    product = product_repo.create({
        'name': 'Test Coffee',
        'roaster_id': 1
    })
    
    batch = batch_repo.create({
        'product_id': product['id'],
        'amount_grams': 250,
        'price': 15.00
    })
    
    # Create sessions for grinder 1
    session_repo.create({
        'product_id': product['id'],
        'product_batch_id': batch['id'],
        'grinder_id': grinder1['id'],
        'amount_coffee_grams': 20,
        'amount_water_grams': 300
    })
    
    # Create sessions for grinder 2
    session_repo.create({
        'product_id': product['id'],
        'product_batch_id': batch['id'],
        'grinder_id': grinder2['id'],
        'amount_coffee_grams': 25,
        'amount_water_grams': 375
    })
    
    session_repo.create({
        'product_id': product['id'],
        'product_batch_id': batch['id'],
        'grinder_id': grinder2['id'],
        'amount_coffee_grams': 30,
        'amount_water_grams': 450
    })
    
    # Get stats for each grinder
    stats1 = grinder_repo.get_usage_stats(grinder1['id'], repositories['factory'])
    stats2 = grinder_repo.get_usage_stats(grinder2['id'], repositories['factory'])
    
    # Grinder 1 stats
    assert stats1['total_brews'] == 1
    assert stats1['total_grams_ground'] == 20
    assert stats1['manually_ground_grams'] == 50
    assert stats1['total_grams_with_manual'] == 70
    
    # Grinder 2 stats
    assert stats2['total_brews'] == 2
    assert stats2['total_grams_ground'] == 55  # 25 + 30
    assert stats2['manually_ground_grams'] == 100
    assert stats2['total_grams_with_manual'] == 155


def test_grinder_stats_nonexistent_grinder(repositories):
    """Test grinder stats for nonexistent grinder."""
    grinder_repo = repositories['grinder']
    
    # Get stats for nonexistent grinder
    stats = grinder_repo.get_usage_stats(999, repositories['factory'])
    
    assert stats['total_brews'] == 0
    assert stats['total_grams_ground'] == 0
    assert stats['manually_ground_grams'] == 0  # Default when grinder not found
    assert stats['total_grams_with_manual'] == 0
    assert stats['total_kilos'] == 0
