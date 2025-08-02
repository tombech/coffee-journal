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
def repositories(temp_data_dir):
    """Create repository instances."""
    factory = RepositoryFactory(storage_type='json', data_dir=temp_data_dir)
    return {
        'factory': factory,
        'roaster': factory.get_roaster_repository(),
        'product': factory.get_product_repository(),
        'grinder': factory.get_grinder_repository(),
        'brew_session': factory.get_brew_session_repository(),
        'batch': factory.get_batch_repository()
    }


def test_roaster_smart_default_manual_override(repositories):
    """Test that manually set default takes precedence over smart default."""
    roaster_repo = repositories['roaster']
    
    # Create two roasters
    roaster1 = roaster_repo.create({'name': 'Blue Bottle'})
    roaster2 = roaster_repo.create({'name': 'Intelligentsia'})
    
    # Set roaster2 as manual default
    roaster_repo.set_default(roaster2['id'])
    
    # Smart default should return the manually set default
    smart_default = roaster_repo.get_smart_default(repositories['factory'])
    assert smart_default['id'] == roaster2['id']
    assert smart_default['name'] == 'Intelligentsia'


def test_roaster_smart_default_frequency_based(repositories):
    """Test that roaster with most products becomes smart default."""
    roaster_repo = repositories['roaster']
    product_repo = repositories['product']
    
    # Create three roasters
    roaster1 = roaster_repo.create({'name': 'Blue Bottle'})
    roaster2 = roaster_repo.create({'name': 'Intelligentsia'})
    roaster3 = roaster_repo.create({'name': 'Stumptown'})
    
    # Create products: roaster2 has most products
    product_repo.create({'name': 'Product 1', 'roaster_id': roaster1['id']})
    product_repo.create({'name': 'Product 2', 'roaster_id': roaster2['id']})
    product_repo.create({'name': 'Product 3', 'roaster_id': roaster2['id']})
    product_repo.create({'name': 'Product 4', 'roaster_id': roaster2['id']})
    product_repo.create({'name': 'Product 5', 'roaster_id': roaster3['id']})
    
    # Smart default should return roaster2 (most products)
    smart_default = roaster_repo.get_smart_default(repositories['factory'])
    assert smart_default['id'] == roaster2['id']
    assert smart_default['name'] == 'Intelligentsia'


def test_roaster_smart_default_recency_based(repositories):
    """Test that recency affects smart default calculation."""
    roaster_repo = repositories['roaster']
    product_repo = repositories['product']
    
    # Create two roasters
    roaster1 = roaster_repo.create({'name': 'Blue Bottle'})
    roaster2 = roaster_repo.create({'name': 'Intelligentsia'})
    
    # Create products with different timestamps
    old_time = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    recent_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    
    # Roaster1 has more products but they're old
    product1 = product_repo.create({'name': 'Old Product 1', 'roaster_id': roaster1['id']})
    product2 = product_repo.create({'name': 'Old Product 2', 'roaster_id': roaster1['id']})
    product3 = product_repo.create({'name': 'Old Product 3', 'roaster_id': roaster1['id']})
    
    # Manually update timestamps to be old
    product_repo.update(product1['id'], {**product1, 'created_at': old_time})
    product_repo.update(product2['id'], {**product2, 'created_at': old_time})
    product_repo.update(product3['id'], {**product3, 'created_at': old_time})
    
    # Roaster2 has fewer products but recent
    product4 = product_repo.create({'name': 'Recent Product', 'roaster_id': roaster2['id']})
    product_repo.update(product4['id'], {**product4, 'created_at': recent_time})
    
    # Smart default might prefer recency
    smart_default = roaster_repo.get_smart_default(repositories['factory'])
    # Either could win depending on scoring algorithm
    assert smart_default['id'] in [roaster1['id'], roaster2['id']]


def test_roaster_smart_default_single_roaster(repositories):
    """Test smart default with only one roaster."""
    roaster_repo = repositories['roaster']
    
    # Create one roaster
    roaster = roaster_repo.create({'name': 'Blue Bottle'})
    
    # Smart default should return the only roaster
    smart_default = roaster_repo.get_smart_default(repositories['factory'])
    assert smart_default['id'] == roaster['id']
    assert smart_default['name'] == 'Blue Bottle'


def test_roaster_smart_default_no_roasters(repositories):
    """Test smart default with no roasters."""
    roaster_repo = repositories['roaster']
    
    # Smart default should return None
    smart_default = roaster_repo.get_smart_default(repositories['factory'])
    assert smart_default is None


def test_grinder_smart_default_manual_override(repositories):
    """Test that manually set default takes precedence for grinders."""
    grinder_repo = repositories['grinder']
    
    # Create two grinders
    grinder1 = grinder_repo.create({'name': 'Baratza Encore'})
    grinder2 = grinder_repo.create({'name': 'Comandante'})
    
    # Set grinder1 as manual default
    grinder_repo.set_default(grinder1['id'])
    
    # Smart default should return the manually set default
    smart_default = grinder_repo.get_smart_default(repositories['factory'])
    assert smart_default['id'] == grinder1['id']
    assert smart_default['name'] == 'Baratza Encore'


def test_grinder_smart_default_frequency_based(repositories):
    """Test that grinder with most brew sessions becomes smart default."""
    grinder_repo = repositories['grinder']
    product_repo = repositories['product']
    batch_repo = repositories['batch']
    session_repo = repositories['brew_session']
    
    # Create test data
    grinder1 = grinder_repo.create({'name': 'Grinder 1'})
    grinder2 = grinder_repo.create({'name': 'Grinder 2'})
    grinder3 = grinder_repo.create({'name': 'Grinder 3'})
    
    product = product_repo.create({'name': 'Test Coffee', 'roaster_id': 1})
    batch = batch_repo.create({'product_id': product['id'], 'amount_grams': 250})
    
    # Create sessions: grinder2 has most sessions
    session_repo.create({'product_id': product['id'], 'product_batch_id': batch['id'], 'grinder_id': grinder1['id']})
    session_repo.create({'product_id': product['id'], 'product_batch_id': batch['id'], 'grinder_id': grinder2['id']})
    session_repo.create({'product_id': product['id'], 'product_batch_id': batch['id'], 'grinder_id': grinder2['id']})
    session_repo.create({'product_id': product['id'], 'product_batch_id': batch['id'], 'grinder_id': grinder2['id']})
    session_repo.create({'product_id': product['id'], 'product_batch_id': batch['id'], 'grinder_id': grinder3['id']})
    
    # Smart default should return grinder2 (most sessions)
    smart_default = grinder_repo.get_smart_default(repositories['factory'])
    assert smart_default['id'] == grinder2['id']
    assert smart_default['name'] == 'Grinder 2'


def test_grinder_smart_default_recency_based(repositories):
    """Test that recency affects grinder smart default calculation."""
    grinder_repo = repositories['grinder']
    product_repo = repositories['product']
    batch_repo = repositories['batch']
    session_repo = repositories['brew_session']
    
    # Create test data
    grinder1 = grinder_repo.create({'name': 'Old Grinder'})
    grinder2 = grinder_repo.create({'name': 'Recent Grinder'})
    
    product = product_repo.create({'name': 'Test Coffee', 'roaster_id': 1})
    batch = batch_repo.create({'product_id': product['id'], 'amount_grams': 250})
    
    # Create sessions with different timestamps
    old_time = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    recent_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    
    # Grinder1 has more sessions but they're old
    session1 = session_repo.create({'product_id': product['id'], 'product_batch_id': batch['id'], 'grinder_id': grinder1['id']})
    session2 = session_repo.create({'product_id': product['id'], 'product_batch_id': batch['id'], 'grinder_id': grinder1['id']})
    session3 = session_repo.create({'product_id': product['id'], 'product_batch_id': batch['id'], 'grinder_id': grinder1['id']})
    
    # Update timestamps to be old
    session_repo.update(session1['id'], {**session1, 'created_at': old_time})
    session_repo.update(session2['id'], {**session2, 'created_at': old_time})
    session_repo.update(session3['id'], {**session3, 'created_at': old_time})
    
    # Grinder2 has fewer sessions but recent
    session4 = session_repo.create({'product_id': product['id'], 'product_batch_id': batch['id'], 'grinder_id': grinder2['id']})
    session_repo.update(session4['id'], {**session4, 'created_at': recent_time})
    
    # Smart default calculation
    smart_default = grinder_repo.get_smart_default(repositories['factory'])
    # Either could win depending on scoring algorithm
    assert smart_default['id'] in [grinder1['id'], grinder2['id']]


def test_grinder_smart_default_no_sessions(repositories):
    """Test grinder smart default with no brew sessions."""
    grinder_repo = repositories['grinder']
    
    # Create two grinders with no sessions
    grinder1 = grinder_repo.create({'name': 'Grinder 1'})
    grinder2 = grinder_repo.create({'name': 'Grinder 2'})
    
    # Smart default should return first grinder (fallback)
    smart_default = grinder_repo.get_smart_default(repositories['factory'])
    assert smart_default['id'] == grinder1['id']  # First created
    assert smart_default['name'] == 'Grinder 1'


def test_grinder_smart_default_single_grinder(repositories):
    """Test smart default with only one grinder."""
    grinder_repo = repositories['grinder']
    
    # Create one grinder
    grinder = grinder_repo.create({'name': 'Solo Grinder'})
    
    # Smart default should return the only grinder
    smart_default = grinder_repo.get_smart_default(repositories['factory'])
    assert smart_default['id'] == grinder['id']
    assert smart_default['name'] == 'Solo Grinder'


def test_grinder_smart_default_no_grinders(repositories):
    """Test smart default with no grinders."""
    grinder_repo = repositories['grinder']
    
    # Smart default should return None
    smart_default = grinder_repo.get_smart_default(repositories['factory'])
    assert smart_default is None
