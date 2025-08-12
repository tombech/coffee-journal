"""
Shared utilities for the Coffee Journal API.

This module contains common functions used across multiple API endpoints,
including validation, data enrichment, and calculation utilities.
"""

from datetime import datetime
from flask import request
from ..repositories.factory import get_repository_factory


def validate_lookup_data(data, item_type="item"):
    """Validate lookup item data."""
    if not data:
        return f"No data provided", 400
    if 'name' not in data:
        return f"Name is required", 400
    if not data['name'] or not data['name'].strip():
        return f"Name cannot be empty", 400
    
    # Validate optional URL fields
    url_fields = ['url', 'image_url']
    for field in url_fields:
        if field in data and data[field]:
            url = data[field].strip()
            if url and not (url.startswith('http://') or url.startswith('https://')):
                return f"{field} must be a valid HTTP or HTTPS URL", 400
    
    # Validate short_form if provided
    if 'short_form' in data and data['short_form']:
        short_form = data['short_form'].strip()
        if len(short_form) > 20:  # Reasonable limit for short form
            return "short_form must be 20 characters or less", 400
    
    return None, None


def calculate_brew_ratio(coffee_grams, water_grams):
    """Calculate brew ratio."""
    if coffee_grams and water_grams:
        try:
            coffee_float = float(coffee_grams)
            water_float = float(water_grams)
            if coffee_float > 0:
                ratio = water_float / coffee_float
                return f"1:{ratio:.1f}"
        except (ValueError, TypeError, ZeroDivisionError):
            return None
    return None


def calculate_total_score(session):
    """
    Calculate total score from individual taste components.
    
    Uses manual score if provided, otherwise calculates from taste components.
    This matches the frontend calculation in BrewSessionTable.js.
    
    Args:
        session: Dictionary containing brew session data
        
    Returns:
        Float score or None if insufficient data
    """
    # Use manual score if available and greater than 0
    manual_score = session.get('score')
    if manual_score is not None and manual_score > 0:
        try:
            return float(manual_score)
        except (ValueError, TypeError):
            pass
    
    # Calculate from taste components (matching frontend logic)
    # Positive components: sweetness, acidity, body, aroma, flavor_profile_match
    positive_components = ['sweetness', 'acidity', 'body', 'aroma', 'flavor_profile_match']
    
    values = []
    for component in positive_components:
        value = session.get(component)
        if value is not None:
            try:
                float_value = float(value)
                if float_value > 0:
                    values.append(float_value)
            except (ValueError, TypeError):
                continue
    
    # Bitterness is inverted (10 - bitterness) like in frontend
    bitterness = session.get('bitterness')
    if bitterness is not None:
        try:
            bitterness_float = float(bitterness)
            bitterness_score = 10 - bitterness_float
            if bitterness_score > 0:
                values.append(bitterness_score)
        except (ValueError, TypeError):
            pass
    
    # Return average if we have any values
    if len(values) > 0:
        return round(sum(values) / len(values), 1)
    
    return None


def calculate_price_per_cup(price, amount_grams):
    """Calculate price per cup based on batch price and amount."""
    if price and amount_grams:
        try:
            price_float = float(price)
            amount_float = float(amount_grams)
            if amount_float > 0:
                cups_per_batch = amount_float / 18.0  # 18g per cup
                if cups_per_batch > 0:
                    return round(price_float / cups_per_batch, 2)
        except (ValueError, TypeError, ZeroDivisionError):
            pass
    return None


def safe_int(value, default=None):
    """Safely convert value to int."""
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=None):
    """Safely convert value to float."""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def validate_tasting_score(score, field_name):
    """Validate that a tasting score is within the 1-10 range."""
    if score is None:
        return None, None
    
    if not isinstance(score, int) or score < 1 or score > 10:
        return None, f"{field_name} must be an integer between 1 and 10"
    
    return score, None


def get_user_id_from_request():
    """Extract user_id from request query parameters."""
    return request.args.get('user_id')


def validate_user_id(user_id):
    """Validate user_id for security. Returns (is_valid, error_message)."""
    if user_id is None:
        return True, None  # None is valid (uses default)
    
    if user_id == '':
        return False, 'Invalid user_id: empty string'  # Empty string is invalid
    
    factory = get_repository_factory()
    try:
        factory._validate_user_id(user_id)
        return True, None
    except ValueError as e:
        return False, str(e)


def enrich_product_with_lookups(product, factory, user_id=None):
    """Enrich product with lookup objects instead of just names."""
    if not product:
        return product
    
    # Get repositories for the specific user
    roaster_repo = factory.get_roaster_repository(user_id)
    bean_type_repo = factory.get_bean_type_repository(user_id)
    country_repo = factory.get_country_repository(user_id)
    decaf_method_repo = factory.get_decaf_method_repository(user_id)
    
    # Enrich roaster
    if product.get('roaster_id'):
        roaster = roaster_repo.find_by_id(product['roaster_id'])
        product['roaster'] = roaster if roaster else None
    else:
        product['roaster'] = None
    
    # Enrich bean types (handle both single ID and array formats for backwards compatibility)
    bean_type_ids = product.get('bean_type_id', [])
    if isinstance(bean_type_ids, int):
        bean_type_ids = [bean_type_ids]  # Convert single int to array
    elif bean_type_ids is None:
        bean_type_ids = []
    
    bean_types = []
    for bt_id in bean_type_ids:
        bt = bean_type_repo.find_by_id(bt_id)
        if bt:
            bean_types.append(bt)
    product['bean_type'] = bean_types
    
    # Enrich country
    if product.get('country_id'):
        country = country_repo.find_by_id(product['country_id'])
        product['country'] = country if country else None
    else:
        product['country'] = None
    
    # Enrich regions (handle both single ID and array formats for backwards compatibility)
    region_ids = product.get('region_id', [])
    if isinstance(region_ids, int):
        region_ids = [region_ids]  # Convert single int to array
    elif region_ids is None:
        region_ids = []
    
    regions = []
    region_repo = factory.get_region_repository(user_id)
    for r_id in region_ids:
        # Regions are now in their own table (v1.3)
        region = region_repo.find_by_id(r_id)
        if region:
            regions.append(region)
    product['region'] = regions
    
    # Enrich decaf method
    if product.get('decaf_method_id'):
        decaf_method = decaf_method_repo.find_by_id(product['decaf_method_id'])
        product['decaf_method'] = decaf_method if decaf_method else None
    else:
        product['decaf_method'] = None
    
    return product


def resolve_lookup_field(data, field_name, repository, allow_multiple=False):
    """
    Resolve lookup field from either ID or name submission.
    
    Args:
        data: Request data containing lookup info
        field_name: Base field name (e.g., 'roaster', 'bean_type')
        repository: Repository to use for lookup operations
        allow_multiple: If True, handle arrays of lookups
    
    Returns:
        dict: Contains resolved 'name', 'id', and optionally 'names'/'ids' for multiple
    """
    id_field = f"{field_name}_id"
    name_field = f"{field_name}_name" if f"{field_name}_name" in data else field_name
    
    if allow_multiple:
        # Handle multiple values (like bean_type)
        ids = data.get(id_field, [])
        names = data.get(name_field, [])
        
        resolved_items = []
        resolved_ids = []
        resolved_names = []
        
        # Process IDs first
        if ids:
            for lookup_id in ids:
                if lookup_id:  # Skip null/empty IDs
                    item = repository.find_by_id(lookup_id)
                    if item:
                        resolved_items.append(item)
                        resolved_ids.append(item['id'])
                        resolved_names.append(item['name'])
        
        # Process names (for new items or when ID is null)
        if names:
            # Convert single string to list if needed
            if isinstance(names, str):
                names = [names]
            for name in names:
                if name and not any(item['name'] == name for item in resolved_items):
                    item = repository.get_or_create(name)
                    resolved_items.append(item)
                    resolved_ids.append(item['id'])
                    resolved_names.append(item['name'])
        
        return {
            'items': resolved_items,
            'ids': resolved_ids,
            'names': resolved_names
        }
    else:
        # Handle single value
        lookup_id = data.get(id_field)
        lookup_name = data.get(name_field)
        
        if lookup_id:
            # Use existing item by ID
            item = repository.find_by_id(lookup_id)
            if item:
                return {
                    'item': item,
                    'id': item['id'],
                    'name': item['name']
                }
        
        if lookup_name:
            # Create or get item by name
            item = repository.get_or_create(lookup_name)
            return {
                'item': item,
                'id': item['id'],
                'name': item['name']
            }
        
        return {
            'item': None,
            'id': None,
            'name': None
        }


def enrich_brew_session_with_lookups(session, factory, user_id=None):
    """Enrich brew session with lookup objects."""
    if not session:
        return session
    
    # Get repositories for the specific user
    brew_method_repo = factory.get_brew_method_repository(user_id)
    recipe_repo = factory.get_recipe_repository(user_id)
    grinder_repo = factory.get_grinder_repository(user_id)
    filter_repo = factory.get_filter_repository(user_id)
    kettle_repo = factory.get_kettle_repository(user_id)
    scale_repo = factory.get_scale_repository(user_id)
    
    # Enrich equipment lookups
    if session.get('brew_method_id'):
        brew_method = brew_method_repo.find_by_id(session['brew_method_id'])
        session['brew_method'] = brew_method if brew_method else None
    else:
        session['brew_method'] = None
        
    if session.get('recipe_id'):
        recipe = recipe_repo.find_by_id(session['recipe_id'])
        session['recipe'] = recipe if recipe else None
    else:
        session['recipe'] = None
        
    if session.get('grinder_id'):
        grinder = grinder_repo.find_by_id(session['grinder_id'])
        session['grinder'] = grinder if grinder else None
    else:
        session['grinder'] = None
        
    if session.get('filter_id'):
        filter_item = filter_repo.find_by_id(session['filter_id'])
        session['filter'] = filter_item if filter_item else None
    else:
        session['filter'] = None
        
    if session.get('kettle_id'):
        kettle = kettle_repo.find_by_id(session['kettle_id'])
        session['kettle'] = kettle if kettle else None
    else:
        session['kettle'] = None
        
    if session.get('scale_id'):
        scale = scale_repo.find_by_id(session['scale_id'])
        session['scale'] = scale if scale else None
    else:
        session['scale'] = None
    
    # Add calculated score as a computed property
    session['calculated_score'] = calculate_total_score(session)
    
    return session

def check_required_fields(data, required_fields):
    """Check if required fields are present in data."""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing_fields.append(field)
    return missing_fields


def validate_score_fields(data, score_fields):
    """Validate that score fields are integers between 1 and 10."""
    errors = []
    for field in score_fields:
        if field in data and data[field] is not None:
            try:
                score = int(data[field])
                if score < 1 or score > 10:
                    errors.append(f'{field} must be between 1 and 10')
                data[field] = score
            except (ValueError, TypeError):
                errors.append(f'{field} must be an integer')
    return errors


def enrich_with_lookups(item, factory, user_id):
    """General function to enrich an item with lookup data."""
    if not item:
        return item
    
    # This is a simplified version of the product enrichment
    if 'roaster_id' in item and item['roaster_id']:
        roaster = factory.get_roaster_repository(user_id).find_by_id(item['roaster_id'])
        if roaster:
            item['roaster'] = roaster
    
    if 'country_id' in item and item['country_id']:
        country = factory.get_country_repository(user_id).find_by_id(item['country_id'])
        if country:
            item['country'] = country
    
    # Add more lookup enrichments as needed
    return item
