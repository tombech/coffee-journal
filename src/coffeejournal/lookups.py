from flask import Blueprint, jsonify, request
from functools import wraps
from .repositories.factory import get_repository_factory
from .api.utils import get_user_id_from_request, validate_user_id


def validate_lookup_data(data, item_type="item"):
    """Validate lookup item data."""
    if not data:
        return f"No data provided", 400
    if 'name' not in data:
        return f"Name is required", 400
    if not data['name'] or not data['name'].strip():
        return f"Name cannot be empty", 400
    return None, None


def validate_user_context(f):
    """Decorator to validate user_id and pass it to the function."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        return f(user_id, *args, **kwargs)
    return decorated_function


lookups = Blueprint('lookups', __name__)


# --- Lookup Endpoints ---

# Roasters
@lookups.route('/roasters', methods=['GET'])
def get_roasters():
    """Get all roasters."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    roasters = factory.get_roaster_repository(user_id).find_all()
    return jsonify(roasters)

@lookups.route('/roasters/search', methods=['GET'])
def search_roasters():
    """Search roasters by name."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    factory = get_repository_factory()
    results = factory.get_roaster_repository(user_id).search(query)
    return jsonify(results)

@lookups.route('/roasters/<int:roaster_id>', methods=['GET'])
def get_roaster(roaster_id):
    """Get a specific roaster."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        roaster = factory.get_roaster_repository(user_id).find_by_id(roaster_id)
        if not roaster:
            return jsonify({'error': 'Roaster not found'}), 404
        return jsonify(roaster)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/roasters/<int:roaster_id>/detail', methods=['GET'])
def get_roaster_detail(roaster_id):
    """Get detailed information about a roaster including usage statistics."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        roaster_repo = factory.get_roaster_repository(user_id)
        product_repo = factory.get_product_repository(user_id)
        batch_repo = factory.get_batch_repository(user_id)
        session_repo = factory.get_brew_session_repository(user_id)
        
        roaster = roaster_repo.find_by_id(roaster_id)
        if not roaster:
            return jsonify({'error': 'Roaster not found'}), 404
        
        # Get products for this roaster (more efficient filtering)
        all_products = product_repo.find_all()
        products = [p for p in all_products if p.get('roaster_id') == roaster_id]
        
        # Quick return if no products to avoid unnecessary queries
        if not products:
            return jsonify({
                'roaster': roaster,
                'statistics': {'total_products': 0, 'total_batches': 0, 'total_brew_sessions': 0, 
                             'total_coffee_amount': 0, 'active_batches': 0, 'total_spent': 0, 'avg_rating': None},
                'recent_products': [],
                'recent_sessions': []
            })
        
        # Get batches for these products (more efficient filtering)
        product_ids = [p['id'] for p in products]
        all_batches = batch_repo.find_all()
        batches = [b for b in all_batches if b.get('product_id') in product_ids]
        
        # Get brew sessions for these batches (more efficient filtering)
        batch_ids = [b['id'] for b in batches] if batches else []
        sessions = []
        if batch_ids:
            all_sessions = session_repo.find_all()
            sessions = [s for s in all_sessions if s.get('product_batch_id') in batch_ids]
        
        # Calculate statistics
        stats = {
            'total_products': len(products),
            'total_batches': len(batches),
            'total_brew_sessions': len(sessions),
            'total_coffee_amount': sum(b.get('amount_grams', 0) for b in batches),
            'active_batches': len([b for b in batches if b.get('is_active', True)]),
            'total_spent': sum(b.get('price', 0) for b in batches if b.get('price')),
            'avg_rating': None
        }
        
        # Calculate average rating from sessions with ratings
        rated_sessions = [s for s in sessions if s.get('rating_overall')]
        if rated_sessions:
            stats['avg_rating'] = round(sum(s['rating_overall'] for s in rated_sessions) / len(rated_sessions), 1)
        
        return jsonify({
            'roaster': roaster,
            'statistics': stats,
            'recent_products': products[-5:] if products else [],  # Last 5 products
            'recent_sessions': sessions[-10:] if sessions else []   # Last 10 sessions
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/roasters', methods=['POST'])
def create_roaster():
    """Create a new roaster."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data, "roaster")
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        
        factory = get_repository_factory()
        repo = factory.get_roaster_repository(user_id)
        
        # Handle is_default flag
        is_default = data.get('is_default', False)
        if is_default:
            # If setting as default, clear the flag from data before creating
            # We'll set it properly after creation
            data_copy = data.copy()
            data_copy.pop('is_default', None)
            roaster = repo.create(data_copy)
            # Now set as default (this will clear any existing default)
            roaster = repo.set_default(roaster['id'])
        else:
            # Ensure is_default field is present in data (defaults to False)
            if 'is_default' not in data:
                data['is_default'] = False
            roaster = repo.create(data)
        
        return jsonify(roaster), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/roasters/<int:roaster_id>', methods=['PUT'])
def update_roaster(roaster_id):
    """Update an existing roaster."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        factory = get_repository_factory()
        repo = factory.get_roaster_repository(user_id)
        
        # Handle is_default flag
        is_default = data.get('is_default')
        if is_default is not None:
            # Remove is_default from data for normal update
            data_copy = data.copy()
            data_copy.pop('is_default', None)
            
            # Update other fields first
            roaster = repo.update(roaster_id, data_copy)
            if not roaster:
                return jsonify({'error': 'Roaster not found'}), 404
            
            # Handle default setting
            if is_default:
                roaster = repo.set_default(roaster_id)
            else:
                roaster = repo.clear_default(roaster_id)
        else:
            # Normal update without default handling
            roaster = repo.update(roaster_id, data)
            if not roaster:
                return jsonify({'error': 'Roaster not found'}), 404
        
        return jsonify(roaster)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/roasters/<int:roaster_id>', methods=['DELETE'])
def delete_roaster(roaster_id):
    """Delete a roaster."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        success = factory.get_roaster_repository(user_id).delete(roaster_id)
        if not success:
            return jsonify({'error': 'Roaster not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/roasters/default', methods=['GET'])
def get_default_roaster():
    """Get the default roaster."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        default_roaster = factory.get_roaster_repository(user_id).find_default()
        if not default_roaster:
            return jsonify({'error': 'No default roaster set'}), 404
        return jsonify(default_roaster)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/roasters/smart_default', methods=['GET'])
def get_smart_default_roaster():
    """Get the smart default roaster based on usage patterns."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        smart_default = factory.get_roaster_repository(user_id).get_smart_default()
        if not smart_default:
            return jsonify({'error': 'No roasters available'}), 404
        return jsonify(smart_default)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/roasters/<int:roaster_id>/set_default', methods=['POST'])
def set_default_roaster(roaster_id):
    """Set a roaster as the default."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        repo = factory.get_roaster_repository(user_id)
        roaster = repo.set_default(roaster_id)
        return jsonify(roaster)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/roasters/<int:roaster_id>/clear_default', methods=['POST'])
def clear_default_roaster(roaster_id):
    """Clear the default flag from a roaster."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        repo = factory.get_roaster_repository(user_id)
        roaster = repo.clear_default(roaster_id)
        return jsonify(roaster)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/roasters/<int:roaster_id>/usage', methods=['GET'])
def check_roaster_usage(roaster_id):
    """Check if roaster is in use by products."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        roaster = factory.get_roaster_repository(user_id).find_by_id(roaster_id)
        if not roaster:
            return jsonify({'error': 'Roaster not found'}), 404
        
        products = factory.get_product_repository(user_id).find_all()
        usage_count = sum(1 for p in products if p.get('roaster_id') == roaster_id)
        
        return jsonify({
            'in_use': usage_count > 0,
            'usage_count': usage_count,
            'usage_type': 'products'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/roasters/<int:roaster_id>/update_references', methods=['POST'])
def update_roaster_references(roaster_id):
    """Update or remove roaster references in products."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        action = data.get('action')
        replacement_id = data.get('replacement_id')
        
        factory = get_repository_factory()
        roaster = factory.get_roaster_repository(user_id).find_by_id(roaster_id)
        if not roaster:
            return jsonify({'error': 'Roaster not found'}), 404
        
        products = factory.get_product_repository(user_id).find_all()
        updated_count = 0
        
        for product in products:
            if product.get('roaster_id') == roaster_id:
                if action == 'remove':
                    product['roaster_id'] = None
                elif action == 'replace' and replacement_id:
                    product['roaster_id'] = replacement_id
                
                factory.get_product_repository(user_id).update(product['id'], product)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Bean Types
@lookups.route('/bean_types', methods=['GET'])
def get_bean_types():
    """Get all bean types."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    bean_types = factory.get_bean_type_repository(user_id).find_all()
    return jsonify(bean_types)

@lookups.route('/bean_types/search', methods=['GET'])
def search_bean_types():
    """Search bean types by name."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    factory = get_repository_factory()
    results = factory.get_bean_type_repository(user_id).search(query)
    return jsonify(results)

@lookups.route('/bean_types/<int:bean_type_id>', methods=['GET'])
def get_bean_type(bean_type_id):
    """Get a specific bean type."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        bean_type = factory.get_bean_type_repository(user_id).find_by_id(bean_type_id)
        if not bean_type:
            return jsonify({'error': 'Bean type not found'}), 404
        return jsonify(bean_type)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/bean_types', methods=['POST'])
def create_bean_type():
    """Create a new bean type."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data, "bean type")
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        
        factory = get_repository_factory()
        bean_type = factory.get_bean_type_repository(user_id).create(data)
        return jsonify(bean_type), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/bean_types/<int:bean_type_id>', methods=['PUT'])
def update_bean_type(bean_type_id):
    """Update an existing bean type."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        factory = get_repository_factory()
        bean_type = factory.get_bean_type_repository(user_id).update(bean_type_id, data)
        if not bean_type:
            return jsonify({'error': 'Bean type not found'}), 404
        return jsonify(bean_type)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/bean_types/<int:bean_type_id>', methods=['DELETE'])
def delete_bean_type(bean_type_id):
    """Delete a bean type."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        success = factory.get_bean_type_repository(user_id).delete(bean_type_id)
        if not success:
            return jsonify({'error': 'Bean type not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/bean_types/<int:bean_type_id>/usage', methods=['GET'])
def check_bean_type_usage(bean_type_id):
    """Check if bean type is in use by products."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        bean_type = factory.get_bean_type_repository(user_id).find_by_id(bean_type_id)
        if not bean_type:
            return jsonify({'error': 'Bean type not found'}), 404
        
        products = factory.get_product_repository(user_id).find_all()
        usage_count = 0
        
        for product in products:
            bean_type_ids = product.get('bean_type_id', [])
            # bean_type_id is always an array after v1.3 standardization
            if bean_type_id in bean_type_ids:
                usage_count += 1
        
        return jsonify({
            'in_use': usage_count > 0,
            'usage_count': usage_count,
            'usage_type': 'products'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/bean_types/<int:bean_type_id>/update_references', methods=['POST'])
def update_bean_type_references(bean_type_id):
    """Update or remove bean type references in products."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        action = data.get('action')
        replacement_id = data.get('replacement_id')
        
        factory = get_repository_factory()
        bean_type = factory.get_bean_type_repository(user_id).find_by_id(bean_type_id)
        if not bean_type:
            return jsonify({'error': 'Bean type not found'}), 404
        
        products = factory.get_product_repository(user_id).find_all()
        updated_count = 0
        
        for product in products:
            bean_type_ids = product.get('bean_type_id', [])
            updated = False
            
            # bean_type_id is always an array after v1.3 standardization
            if bean_type_id in bean_type_ids:
                if action == 'remove':
                    product['bean_type_id'] = [bt_id for bt_id in bean_type_ids if bt_id != bean_type_id]
                    updated = True
                elif action == 'replace' and replacement_id:
                    product['bean_type_id'] = [replacement_id if bt_id == bean_type_id else bt_id for bt_id in bean_type_ids]
                    updated = True
            
            if updated:
                factory.get_product_repository(user_id).update(product['id'], product)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Countries
@lookups.route('/countries', methods=['GET'])
def get_countries():
    """Get all countries."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    countries = factory.get_country_repository(user_id).find_all()
    return jsonify(countries)

@lookups.route('/countries/search', methods=['GET'])
def search_countries():
    """Search countries by name."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    factory = get_repository_factory()
    results = factory.get_country_repository(user_id).search(query)
    return jsonify(results)

@lookups.route('/countries/<int:country_id>', methods=['GET'])
def get_country(country_id):
    """Get a specific country."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        country = factory.get_country_repository(user_id).find_by_id(country_id)
        if not country:
            return jsonify({'error': 'Country not found'}), 404
        return jsonify(country)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/countries', methods=['POST'])
def create_country():
    """Create a new country."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        factory = get_repository_factory()
        country = factory.get_country_repository(user_id).create(data)
        return jsonify(country), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/countries/<int:country_id>', methods=['PUT'])
def update_country(country_id):
    """Update an existing country."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        factory = get_repository_factory()
        country = factory.get_country_repository(user_id).update(country_id, data)
        if not country:
            return jsonify({'error': 'Country not found'}), 404
        return jsonify(country)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/countries/<int:country_id>', methods=['DELETE'])
def delete_country(country_id):
    """Delete a country."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        success = factory.get_country_repository(user_id).delete(country_id)
        if not success:
            return jsonify({'error': 'Country not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/countries/<int:country_id>/usage', methods=['GET'])
def check_country_usage(country_id):
    """Check if country is in use by products."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        country = factory.get_country_repository(user_id).find_by_id(country_id)
        if not country:
            return jsonify({'error': 'Country not found'}), 404
        
        products = factory.get_product_repository(user_id).find_all()
        usage_count = 0
        
        for product in products:
            # Check if this product uses the country
            if product.get('country_id') == country_id:
                usage_count += 1
        
        return jsonify({
            'in_use': usage_count > 0,
            'usage_count': usage_count,
            'usage_type': 'products'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/countries/<int:country_id>/update_references', methods=['POST'])
def update_country_references(country_id):
    """Update or remove country references in products."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        action = data.get('action')
        replacement_id = data.get('replacement_id')
        
        factory = get_repository_factory()
        country = factory.get_country_repository(user_id).find_by_id(country_id)
        if not country:
            return jsonify({'error': 'Country not found'}), 404
        
        products = factory.get_product_repository(user_id).find_all()
        updated_count = 0
        
        for product in products:
            # Check if this product uses the country being deleted
            if product.get('country_id') == country_id:
                if action == 'remove':
                    product['country_id'] = None
                    updated = True
                elif action == 'replace' and replacement_id:
                    product['country_id'] = replacement_id
                    updated = True
                else:
                    updated = False
                
                if updated:
                    factory.get_product_repository(user_id).update(product['id'], product)
                    updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Regions
@lookups.route('/regions', methods=['GET'])
def get_regions():
    """Get all regions."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    regions = factory.get_region_repository(user_id).find_all()
    return jsonify(regions)

@lookups.route('/regions/search', methods=['GET'])
def search_regions():
    """Search regions by name."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    factory = get_repository_factory()
    results = factory.get_region_repository(user_id).search(query)
    return jsonify(results)

@lookups.route('/regions/<int:region_id>', methods=['GET'])
def get_region(region_id):
    """Get a specific region."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        region = factory.get_region_repository(user_id).find_by_id(region_id)
        if region:
            return jsonify(region)
        return jsonify({'error': 'Region not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/regions', methods=['POST'])
def create_region():
    """Create a new region."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        factory = get_repository_factory()
        region = factory.get_region_repository(user_id).create(data)
        return jsonify(region), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/regions/<int:region_id>', methods=['PUT'])
def update_region(region_id):
    """Update a region."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        factory = get_repository_factory()
        region = factory.get_region_repository(user_id).update(region_id, data)
        if region:
            return jsonify(region)
        return jsonify({'error': 'Region not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/regions/<int:region_id>', methods=['DELETE'])
def delete_region(region_id):
    """Delete a region."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        if factory.get_region_repository(user_id).delete(region_id):
            return '', 204
        return jsonify({'error': 'Region not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/regions/<int:region_id>/usage', methods=['GET'])
def check_region_usage(region_id):
    """Check if region is in use by products."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        region = factory.get_region_repository(user_id).find_by_id(region_id)
        if not region:
            return jsonify({'error': 'Region not found'}), 404
        
        products = factory.get_product_repository(user_id).find_all()
        usage_count = 0
        
        for product in products:
            region_ids = product.get('region_id', [])
            # region_id is always an array after v1.3 standardization
            if region_id in region_ids:
                usage_count += 1
        
        return jsonify({
            'in_use': usage_count > 0,
            'usage_count': usage_count,
            'usage_type': 'products'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/regions/<int:region_id>/update_references', methods=['POST'])
def update_region_references(region_id):
    """Update or remove region references in products."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        action = data.get('action')
        replacement_id = data.get('replacement_id')
        
        factory = get_repository_factory()
        region = factory.get_region_repository(user_id).find_by_id(region_id)
        if not region:
            return jsonify({'error': 'Region not found'}), 404
        
        products = factory.get_product_repository(user_id).find_all()
        updated_count = 0
        
        for product in products:
            region_ids = product.get('region_id', [])
            updated = False
            
            # region_id is always an array after v1.3 standardization
            if region_id in region_ids:
                if action == 'remove':
                    product['region_id'] = [r for r in region_ids if r != region_id]
                    updated = True
                elif action == 'replace' and replacement_id:
                    product['region_id'] = [replacement_id if r == region_id else r for r in region_ids]
                    updated = True
            
            if updated:
                factory.get_product_repository(user_id).update(product['id'], product)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/countries/<int:country_id>/regions', methods=['GET', 'POST'])
def handle_country_regions(country_id):
    """Get all regions for a specific country or create a new region."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    
    if request.method == 'GET':
        try:
            regions = factory.get_region_repository(user_id).find_by_country(country_id)
            return jsonify(regions)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            # Verify country exists
            country = factory.get_country_repository(user_id).find_by_id(country_id)
            if not country:
                return jsonify({'error': 'Country not found'}), 404
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validate region name
            if not data.get('name') or not data['name'].strip():
                return jsonify({'error': 'Name is required'}), 400
            
            # Add country_id to region data
            region_data = data.copy()
            region_data['country_id'] = country_id
            
            region = factory.get_region_repository(user_id).create(region_data)
            return jsonify(region), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Brew Methods
@lookups.route('/brew_methods', methods=['GET'])
def get_brew_methods():
    """Get all brew methods."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    brew_methods = factory.get_brew_method_repository(user_id).find_all()
    return jsonify(brew_methods)

@lookups.route('/brew_methods/search', methods=['GET'])
def search_brew_methods():
    """Search brew methods by name or short_form."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    factory = get_repository_factory()
    results = factory.get_brew_method_repository(user_id).search(query)
    return jsonify(results)

@lookups.route('/brew_methods/<int:brew_method_id>', methods=['GET'])
def get_brew_method(brew_method_id):
    """Get a specific brew method."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        brew_method = factory.get_brew_method_repository(user_id).find_by_id(brew_method_id)
        if not brew_method:
            return jsonify({'error': 'Brew method not found'}), 404
        return jsonify(brew_method)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/brew_methods', methods=['POST'])
def create_brew_method():
    """Create a new brew method."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        factory = get_repository_factory()
        brew_method = factory.get_brew_method_repository(user_id).create(data)
        return jsonify(brew_method), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/brew_methods/<int:brew_method_id>', methods=['PUT'])
def update_brew_method(brew_method_id):
    """Update an existing brew method."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        factory = get_repository_factory()
        brew_method = factory.get_brew_method_repository(user_id).update(brew_method_id, data)
        if not brew_method:
            return jsonify({'error': 'Brew method not found'}), 404
        return jsonify(brew_method)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/brew_methods/<int:brew_method_id>', methods=['DELETE'])
def delete_brew_method(brew_method_id):
    """Delete a brew method."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        success = factory.get_brew_method_repository(user_id).delete(brew_method_id)
        if not success:
            return jsonify({'error': 'Brew method not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/brew_methods/<int:brew_method_id>/usage', methods=['GET'])
def check_brew_method_usage(brew_method_id):
    """Check if brew method is in use by brew sessions."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        brew_method = factory.get_brew_method_repository(user_id).find_by_id(brew_method_id)
        if not brew_method:
            return jsonify({'error': 'Brew method not found'}), 404
        
        sessions = factory.get_brew_session_repository(user_id).find_all()
        usage_count = sum(1 for s in sessions if s.get('brew_method_id') == brew_method_id)
        
        return jsonify({
            'in_use': usage_count > 0,
            'usage_count': usage_count,
            'usage_type': 'brew_sessions'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/brew_methods/<int:brew_method_id>/update_references', methods=['POST'])
def update_brew_method_references(brew_method_id):
    """Update or remove brew method references in brew sessions."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        action = data.get('action')  # 'remove' or 'replace'
        replacement_id = data.get('replacement_id')
        
        factory = get_repository_factory()
        brew_method = factory.get_brew_method_repository(user_id).find_by_id(brew_method_id)
        if not brew_method:
            return jsonify({'error': 'Brew method not found'}), 404
        
        sessions = factory.get_brew_session_repository(user_id).find_all()
        updated_count = 0
        
        for session in sessions:
            if session.get('brew_method_id') == brew_method_id:
                if action == 'remove':
                    session['brew_method_id'] = None
                elif action == 'replace' and replacement_id:
                    session['brew_method_id'] = replacement_id
                
                factory.get_brew_session_repository(user_id).update(session['id'], session)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Recipes
@lookups.route('/recipes', methods=['GET'])
def get_recipes():
    """Get all recipes."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    recipes = factory.get_recipe_repository(user_id).find_all()
    return jsonify(recipes)

@lookups.route('/recipes/search', methods=['GET'])
def search_recipes():
    """Search recipes by name."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    factory = get_repository_factory()
    results = factory.get_recipe_repository(user_id).search(query)
    return jsonify(results)

@lookups.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """Get a specific recipe."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        recipe = factory.get_recipe_repository(user_id).find_by_id(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404
        return jsonify(recipe)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/recipes', methods=['POST'])
def create_recipe():
    """Create a new recipe."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        factory = get_repository_factory()
        recipe = factory.get_recipe_repository(user_id).create(data)
        return jsonify(recipe), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    """Update an existing recipe."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        factory = get_repository_factory()
        recipe = factory.get_recipe_repository(user_id).update(recipe_id, data)
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404
        return jsonify(recipe)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    """Delete a recipe."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        success = factory.get_recipe_repository(user_id).delete(recipe_id)
        if not success:
            return jsonify({'error': 'Recipe not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/recipes/<int:recipe_id>/usage', methods=['GET'])
def check_recipe_usage(recipe_id):
    """Check if recipe is in use by brew sessions."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        recipe = factory.get_recipe_repository(user_id).find_by_id(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404
        
        sessions = factory.get_brew_session_repository(user_id).find_all()
        usage_count = sum(1 for s in sessions if s.get('recipe_id') == recipe_id)
        
        return jsonify({
            'in_use': usage_count > 0,
            'usage_count': usage_count,
            'usage_type': 'brew_sessions'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/recipes/<int:recipe_id>/update_references', methods=['POST'])
def update_recipe_references(recipe_id):
    """Update or remove recipe references in brew sessions."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        action = data.get('action')  # 'remove' or 'replace'
        replacement_id = data.get('replacement_id')
        
        factory = get_repository_factory()
        recipe = factory.get_recipe_repository(user_id).find_by_id(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404
        
        sessions = factory.get_brew_session_repository(user_id).find_all()
        updated_count = 0
        
        for session in sessions:
            if session.get('recipe_id') == recipe_id:
                if action == 'remove':
                    session['recipe_id'] = None
                elif action == 'replace' and replacement_id:
                    session['recipe_id'] = replacement_id
                
                factory.get_brew_session_repository(user_id).update(session['id'], session)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Decaf Methods
@lookups.route('/decaf_methods', methods=['GET'])
def get_decaf_methods():
    """Get all decaf methods."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    decaf_methods = factory.get_decaf_method_repository(user_id).find_all()
    return jsonify(decaf_methods)

@lookups.route('/decaf_methods/search', methods=['GET'])
def search_decaf_methods():
    """Search decaf methods by name."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    factory = get_repository_factory()
    results = factory.get_decaf_method_repository(user_id).search(query)
    return jsonify(results)

@lookups.route('/decaf_methods/<int:decaf_method_id>', methods=['GET'])
def get_decaf_method(decaf_method_id):
    """Get a specific decaf method."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        decaf_method = factory.get_decaf_method_repository(user_id).find_by_id(decaf_method_id)
        if not decaf_method:
            return jsonify({'error': 'Decaf method not found'}), 404
        return jsonify(decaf_method)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/decaf_methods', methods=['POST'])
def create_decaf_method():
    """Create a new decaf method."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        factory = get_repository_factory()
        decaf_method = factory.get_decaf_method_repository(user_id).create(data)
        return jsonify(decaf_method), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/decaf_methods/<int:decaf_method_id>', methods=['PUT'])
def update_decaf_method(decaf_method_id):
    """Update an existing decaf method."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        factory = get_repository_factory()
        decaf_method = factory.get_decaf_method_repository(user_id).update(decaf_method_id, data)
        if not decaf_method:
            return jsonify({'error': 'Decaf method not found'}), 404
        return jsonify(decaf_method)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/decaf_methods/<int:decaf_method_id>', methods=['DELETE'])
def delete_decaf_method(decaf_method_id):
    """Delete a decaf method."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        success = factory.get_decaf_method_repository(user_id).delete(decaf_method_id)
        if not success:
            return jsonify({'error': 'Decaf method not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/decaf_methods/<int:decaf_method_id>/usage', methods=['GET'])
def check_decaf_method_usage(decaf_method_id):
    """Check if decaf method is in use by products."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        decaf_method = factory.get_decaf_method_repository(user_id).find_by_id(decaf_method_id)
        if not decaf_method:
            return jsonify({'error': 'Decaf method not found'}), 404
        
        products = factory.get_product_repository(user_id).find_all()
        usage_count = sum(1 for p in products if p.get('decaf_method_id') == decaf_method_id)
        
        return jsonify({
            'in_use': usage_count > 0,
            'usage_count': usage_count,
            'usage_type': 'products'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/decaf_methods/<int:decaf_method_id>/update_references', methods=['POST'])
def update_decaf_method_references(decaf_method_id):
    """Update or remove decaf method references in products."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        action = data.get('action')
        replacement_id = data.get('replacement_id')
        
        factory = get_repository_factory()
        decaf_method = factory.get_decaf_method_repository(user_id).find_by_id(decaf_method_id)
        if not decaf_method:
            return jsonify({'error': 'Decaf method not found'}), 404
        
        products = factory.get_product_repository(user_id).find_all()
        updated_count = 0
        
        for product in products:
            if product.get('decaf_method_id') == decaf_method_id:
                if action == 'remove':
                    product['decaf_method_id'] = None
                    updated = True
                elif action == 'replace' and replacement_id:
                    product['decaf_method_id'] = replacement_id
                    updated = True
                else:
                    updated = False
                
                if updated:
                    factory.get_product_repository(user_id).update(product['id'], product)
                    updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Grinders
@lookups.route('/grinders', methods=['GET'])
def get_grinders():
    """Get all grinders."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    grinders = factory.get_grinder_repository(user_id).find_all()
    return jsonify(grinders)

@lookups.route('/grinders/search', methods=['GET'])
def search_grinders():
    """Search grinders by name or short_form."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    factory = get_repository_factory()
    results = factory.get_grinder_repository(user_id).search(query)
    return jsonify(results)

@lookups.route('/grinders/<int:grinder_id>', methods=['GET'])
def get_grinder(grinder_id):
    """Get a specific grinder."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        grinder = factory.get_grinder_repository(user_id).find_by_id(grinder_id)
        if not grinder:
            return jsonify({'error': 'Grinder not found'}), 404
        return jsonify(grinder)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/grinders', methods=['POST'])
def create_grinder():
    """Create a new grinder."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        
        # Validate and convert manually_ground_grams to float
        if 'manually_ground_grams' in data:
            try:
                if data['manually_ground_grams'] is not None:
                    data['manually_ground_grams'] = float(data['manually_ground_grams'])
                    if data['manually_ground_grams'] < 0:
                        return jsonify({'error': 'Manual ground amount cannot be negative'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Manual ground amount must be a valid number'}), 400
        
        factory = get_repository_factory()
        repo = factory.get_grinder_repository(user_id)
        
        # Handle is_default flag
        is_default = data.get('is_default', False)
        if is_default:
            # If setting as default, clear the flag from data before creating
            # We'll set it properly after creation
            data_copy = data.copy()
            data_copy.pop('is_default', None)
            grinder = repo.create(data_copy)
            # Now set as default (this will clear any existing default)
            grinder = repo.set_default(grinder['id'])
        else:
            # Ensure is_default field is present in data (defaults to False)
            if 'is_default' not in data:
                data['is_default'] = False
            # Ensure manually_ground_grams field is present (defaults to 0)
            if 'manually_ground_grams' not in data:
                data['manually_ground_grams'] = 0
            grinder = repo.create(data)
        
        return jsonify(grinder), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/grinders/<int:grinder_id>', methods=['PUT'])
def update_grinder(grinder_id):
    """Update an existing grinder."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate and convert manually_ground_grams to float
        if 'manually_ground_grams' in data:
            try:
                if data['manually_ground_grams'] is not None:
                    data['manually_ground_grams'] = float(data['manually_ground_grams'])
                    if data['manually_ground_grams'] < 0:
                        return jsonify({'error': 'Manual ground amount cannot be negative'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Manual ground amount must be a valid number'}), 400
        
        factory = get_repository_factory()
        repo = factory.get_grinder_repository(user_id)
        
        # Handle is_default flag
        is_default = data.get('is_default')
        if is_default is not None:
            # Remove is_default from data for normal update
            data_copy = data.copy()
            data_copy.pop('is_default', None)
            
            # Update other fields first
            grinder = repo.update(grinder_id, data_copy)
            if not grinder:
                return jsonify({'error': 'Grinder not found'}), 404
            
            # Handle default setting
            if is_default:
                grinder = repo.set_default(grinder_id)
            else:
                grinder = repo.clear_default(grinder_id)
        else:
            # Normal update without default handling
            grinder = repo.update(grinder_id, data)
            if not grinder:
                return jsonify({'error': 'Grinder not found'}), 404
        
        return jsonify(grinder)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/grinders/<int:grinder_id>', methods=['DELETE'])
def delete_grinder(grinder_id):
    """Delete a grinder."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        success = factory.get_grinder_repository(user_id).delete(grinder_id)
        if not success:
            return jsonify({'error': 'Grinder not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/grinders/default', methods=['GET'])
def get_default_grinder():
    """Get the default grinder."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        default_grinder = factory.get_grinder_repository(user_id).find_default()
        if not default_grinder:
            return jsonify({'error': 'No default grinder set'}), 404
        return jsonify(default_grinder)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/grinders/smart_default', methods=['GET'])
def get_smart_default_grinder():
    """Get the smart default grinder based on usage patterns."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        smart_default = factory.get_grinder_repository(user_id).get_smart_default()
        if not smart_default:
            return jsonify({'error': 'No grinders available'}), 404
        return jsonify(smart_default)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/grinders/<int:grinder_id>/set_default', methods=['POST'])
def set_default_grinder(grinder_id):
    """Set a grinder as the default."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        repo = factory.get_grinder_repository(user_id)
        grinder = repo.set_default(grinder_id)
        return jsonify(grinder)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/grinders/<int:grinder_id>/clear_default', methods=['POST'])
def clear_default_grinder(grinder_id):
    """Clear the default flag from a grinder."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        repo = factory.get_grinder_repository(user_id)
        grinder = repo.clear_default(grinder_id)
        return jsonify(grinder)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/grinders/<int:grinder_id>/stats', methods=['GET'])
def get_grinder_stats(grinder_id):
    """Get usage statistics for a grinder."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        repo = factory.get_grinder_repository(user_id)
        grinder = repo.find_by_id(grinder_id)
        if not grinder:
            return jsonify({'error': 'Grinder not found'}), 404
        
        stats = repo.get_usage_stats(grinder_id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@lookups.route('/grinders/<int:grinder_id>/usage', methods=['GET'])
def check_grinder_usage(grinder_id):
    """Check if grinder is in use by brew sessions."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        grinder = factory.get_grinder_repository(user_id).find_by_id(grinder_id)
        if not grinder:
            return jsonify({'error': 'Grinder not found'}), 404
        
        sessions = factory.get_brew_session_repository(user_id).find_all()
        usage_count = sum(1 for s in sessions if s.get('grinder_id') == grinder_id)
        
        return jsonify({
            'in_use': usage_count > 0,
            'usage_count': usage_count,
            'usage_type': 'brew_sessions'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/grinders/<int:grinder_id>/update_references', methods=['POST'])
def update_grinder_references(grinder_id):
    """Update or remove grinder references in brew sessions."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        action = data.get('action')
        replacement_id = data.get('replacement_id')
        
        factory = get_repository_factory()
        grinder = factory.get_grinder_repository(user_id).find_by_id(grinder_id)
        if not grinder:
            return jsonify({'error': 'Grinder not found'}), 404
        
        sessions = factory.get_brew_session_repository(user_id).find_all()
        updated_count = 0
        
        for session in sessions:
            if session.get('grinder_id') == grinder_id:
                if action == 'remove':
                    session['grinder_id'] = None
                elif action == 'replace' and replacement_id:
                    session['grinder_id'] = replacement_id
                
                factory.get_brew_session_repository(user_id).update(session['id'], session)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Filters
@lookups.route('/filters', methods=['GET'])
def get_filters():
    """Get all filters."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    filters = factory.get_filter_repository(user_id).find_all()
    return jsonify(filters)

@lookups.route('/filters/search', methods=['GET'])
def search_filters():
    """Search filters by name."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    factory = get_repository_factory()
    results = factory.get_filter_repository(user_id).search(query)
    return jsonify(results)

@lookups.route('/filters/<int:filter_id>', methods=['GET'])
def get_filter(filter_id):
    """Get a specific filter."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        filter_item = factory.get_filter_repository(user_id).find_by_id(filter_id)
        if not filter_item:
            return jsonify({'error': 'Filter not found'}), 404
        return jsonify(filter_item)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/filters', methods=['POST'])
def create_filter():
    """Create a new filter."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        factory = get_repository_factory()
        filter_item = factory.get_filter_repository(user_id).create(data)
        return jsonify(filter_item), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/filters/<int:filter_id>', methods=['PUT'])
def update_filter(filter_id):
    """Update an existing filter."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        factory = get_repository_factory()
        filter_item = factory.get_filter_repository(user_id).update(filter_id, data)
        if not filter_item:
            return jsonify({'error': 'Filter not found'}), 404
        return jsonify(filter_item)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/filters/<int:filter_id>', methods=['DELETE'])
def delete_filter(filter_id):
    """Delete a filter."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        success = factory.get_filter_repository(user_id).delete(filter_id)
        if not success:
            return jsonify({'error': 'Filter not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/filters/<int:filter_id>/usage', methods=['GET'])
def check_filter_usage(filter_id):
    """Check if filter is in use by brew sessions."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        filter_item = factory.get_filter_repository(user_id).find_by_id(filter_id)
        if not filter_item:
            return jsonify({'error': 'Filter not found'}), 404
        
        sessions = factory.get_brew_session_repository(user_id).find_all()
        usage_count = sum(1 for s in sessions if s.get('filter_id') == filter_id)
        
        return jsonify({
            'in_use': usage_count > 0,
            'usage_count': usage_count,
            'usage_type': 'brew_sessions'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/filters/<int:filter_id>/update_references', methods=['POST'])
def update_filter_references(filter_id):
    """Update or remove filter references in brew sessions."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        action = data.get('action')
        replacement_id = data.get('replacement_id')
        
        factory = get_repository_factory()
        filter_item = factory.get_filter_repository(user_id).find_by_id(filter_id)
        if not filter_item:
            return jsonify({'error': 'Filter not found'}), 404
        
        sessions = factory.get_brew_session_repository(user_id).find_all()
        updated_count = 0
        
        for session in sessions:
            if session.get('filter_id') == filter_id:
                if action == 'remove':
                    session['filter_id'] = None
                elif action == 'replace' and replacement_id:
                    session['filter_id'] = replacement_id
                
                factory.get_brew_session_repository(user_id).update(session['id'], session)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Kettles
@lookups.route('/kettles', methods=['GET'])
def get_kettles():
    """Get all kettles."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    kettles = factory.get_kettle_repository(user_id).find_all()
    return jsonify(kettles)

@lookups.route('/kettles/search', methods=['GET'])
def search_kettles():
    """Search kettles by name."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    factory = get_repository_factory()
    results = factory.get_kettle_repository(user_id).search(query)
    return jsonify(results)

@lookups.route('/kettles/<int:kettle_id>', methods=['GET'])
def get_kettle(kettle_id):
    """Get a specific kettle."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        kettle = factory.get_kettle_repository(user_id).find_by_id(kettle_id)
        if not kettle:
            return jsonify({'error': 'Kettle not found'}), 404
        return jsonify(kettle)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/kettles', methods=['POST'])
def create_kettle():
    """Create a new kettle."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        factory = get_repository_factory()
        kettle = factory.get_kettle_repository(user_id).create(data)
        return jsonify(kettle), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/kettles/<int:kettle_id>', methods=['PUT'])
def update_kettle(kettle_id):
    """Update an existing kettle."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        factory = get_repository_factory()
        kettle = factory.get_kettle_repository(user_id).update(kettle_id, data)
        if not kettle:
            return jsonify({'error': 'Kettle not found'}), 404
        return jsonify(kettle)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/kettles/<int:kettle_id>', methods=['DELETE'])
def delete_kettle(kettle_id):
    """Delete a kettle."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        success = factory.get_kettle_repository(user_id).delete(kettle_id)
        if not success:
            return jsonify({'error': 'Kettle not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/kettles/<int:kettle_id>/usage', methods=['GET'])
def check_kettle_usage(kettle_id):
    """Check if kettle is in use by brew sessions."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        kettle = factory.get_kettle_repository(user_id).find_by_id(kettle_id)
        if not kettle:
            return jsonify({'error': 'Kettle not found'}), 404
        
        sessions = factory.get_brew_session_repository(user_id).find_all()
        usage_count = sum(1 for s in sessions if s.get('kettle_id') == kettle_id)
        
        return jsonify({
            'in_use': usage_count > 0,
            'usage_count': usage_count,
            'usage_type': 'brew_sessions'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/kettles/<int:kettle_id>/update_references', methods=['POST'])
def update_kettle_references(kettle_id):
    """Update or remove kettle references in brew sessions."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        action = data.get('action')
        replacement_id = data.get('replacement_id')
        
        factory = get_repository_factory()
        kettle = factory.get_kettle_repository(user_id).find_by_id(kettle_id)
        if not kettle:
            return jsonify({'error': 'Kettle not found'}), 404
        
        sessions = factory.get_brew_session_repository(user_id).find_all()
        updated_count = 0
        
        for session in sessions:
            if session.get('kettle_id') == kettle_id:
                if action == 'remove':
                    session['kettle_id'] = None
                elif action == 'replace' and replacement_id:
                    session['kettle_id'] = replacement_id
                
                factory.get_brew_session_repository(user_id).update(session['id'], session)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Scales
@lookups.route('/scales', methods=['GET'])
def get_scales():
    """Get all scales."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    scales = factory.get_scale_repository(user_id).find_all()
    return jsonify(scales)

@lookups.route('/scales/search', methods=['GET'])
def search_scales():
    """Search scales by name."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    factory = get_repository_factory()
    results = factory.get_scale_repository(user_id).search(query)
    return jsonify(results)

@lookups.route('/scales/<int:scale_id>', methods=['GET'])
def get_scale(scale_id):
    """Get a specific scale."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        scale = factory.get_scale_repository(user_id).find_by_id(scale_id)
        if not scale:
            return jsonify({'error': 'Scale not found'}), 404
        return jsonify(scale)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/scales', methods=['POST'])
def create_scale():
    """Create a new scale."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        factory = get_repository_factory()
        scale = factory.get_scale_repository(user_id).create(data)
        return jsonify(scale), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/scales/<int:scale_id>', methods=['PUT'])
def update_scale(scale_id):
    """Update an existing scale."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        factory = get_repository_factory()
        scale = factory.get_scale_repository(user_id).update(scale_id, data)
        if not scale:
            return jsonify({'error': 'Scale not found'}), 404
        return jsonify(scale)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/scales/<int:scale_id>', methods=['DELETE'])
def delete_scale(scale_id):
    """Delete a scale."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        success = factory.get_scale_repository(user_id).delete(scale_id)
        if not success:
            return jsonify({'error': 'Scale not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/scales/<int:scale_id>/usage', methods=['GET'])
def check_scale_usage(scale_id):
    """Check if scale is in use by brew sessions."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        scale = factory.get_scale_repository(user_id).find_by_id(scale_id)
        if not scale:
            return jsonify({'error': 'Scale not found'}), 404
        
        sessions = factory.get_brew_session_repository(user_id).find_all()
        usage_count = sum(1 for s in sessions if s.get('scale_id') == scale_id)
        
        return jsonify({
            'in_use': usage_count > 0,
            'usage_count': usage_count,
            'usage_type': 'brew_sessions'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookups.route('/scales/<int:scale_id>/update_references', methods=['POST'])
def update_scale_references(scale_id):
    """Update or remove scale references in brew sessions."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        action = data.get('action')
        replacement_id = data.get('replacement_id')
        
        factory = get_repository_factory()
        scale = factory.get_scale_repository(user_id).find_by_id(scale_id)
        if not scale:
            return jsonify({'error': 'Scale not found'}), 404
        
        sessions = factory.get_brew_session_repository(user_id).find_all()
        updated_count = 0
        
        for session in sessions:
            if session.get('scale_id') == scale_id:
                if action == 'remove':
                    session['scale_id'] = None
                elif action == 'replace' and replacement_id:
                    session['scale_id'] = replacement_id
                
                factory.get_brew_session_repository(user_id).update(session['id'], session)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500