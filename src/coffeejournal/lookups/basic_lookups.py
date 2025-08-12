"""
Basic lookup endpoints (roasters, bean_types, countries, regions, brew_methods, recipes, decaf_methods).
Restored from original lookups.py to preserve all functionality.
"""

from flask import Blueprint, jsonify, request
from .common import validate_user_context, validate_lookup_data
from ..repositories.factory import get_repository_factory

basic_lookups_bp = Blueprint('basic_lookups', __name__)


# ==================== ROASTERS ====================

@basic_lookups_bp.route('/roasters', methods=['GET'])
@validate_user_context
def get_roasters(user_id):
    """Get all roasters."""
    try:
        factory = get_repository_factory()
        roasters = factory.get_roaster_repository(user_id).find_all()
        return jsonify(roasters)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/roasters/search', methods=['GET'])
@validate_user_context
def search_roasters(user_id):
    """Search roasters by name."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    try:
        factory = get_repository_factory()
        results = factory.get_roaster_repository(user_id).search(query)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/roasters/<int:roaster_id>', methods=['GET'])
@validate_user_context
def get_roaster(user_id, roaster_id):
    """Get a specific roaster."""
    try:
        factory = get_repository_factory()
        roaster = factory.get_roaster_repository(user_id).find_by_id(roaster_id)
        if not roaster:
            return jsonify({'error': 'Roaster not found'}), 404
        return jsonify(roaster)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/roasters/<int:roaster_id>/detail', methods=['GET'])
@validate_user_context
def get_roaster_detail(user_id, roaster_id):
    """Get detailed information about a roaster including usage statistics."""
    try:
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
            'active_batches': len([b for b in batches if b.get('amount_grams', 0) > 0]),
            'total_spent': sum(b.get('price', 0) for b in batches if b.get('price')),
            'avg_rating': sum(s.get('score', 0) for s in sessions if s.get('score')) / len(sessions) if sessions and any(s.get('score') for s in sessions) else None
        }
        
        # Get recent products (sorted by creation date)
        recent_products = sorted(products, key=lambda x: x.get('id', 0), reverse=True)[:5]
        
        # Get recent sessions (sorted by timestamp)
        recent_sessions = sorted(sessions, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
        
        return jsonify({
            'roaster': roaster,
            'statistics': stats,
            'recent_products': recent_products,
            'recent_sessions': recent_sessions
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/roasters', methods=['POST'])
@validate_user_context
def create_roaster(user_id):
    """Create a new roaster."""
    try:
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
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


@basic_lookups_bp.route('/roasters/<int:roaster_id>', methods=['PUT'])
@validate_user_context
def update_roaster(user_id, roaster_id):
    """Update an existing roaster."""
    try:
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


@basic_lookups_bp.route('/roasters/<int:roaster_id>', methods=['DELETE'])
@validate_user_context
def delete_roaster(user_id, roaster_id):
    """Delete a roaster."""
    try:
        factory = get_repository_factory()
        success = factory.get_roaster_repository(user_id).delete(roaster_id)
        if not success:
            return jsonify({'error': 'Roaster not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/roasters/<int:roaster_id>/usage', methods=['GET'])
@validate_user_context
def check_roaster_usage(user_id, roaster_id):
    """Check if roaster is in use by products."""
    try:
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


@basic_lookups_bp.route('/roasters/<int:roaster_id>/update_references', methods=['POST'])
@validate_user_context
def update_roaster_references(user_id, roaster_id):
    """Update or remove roaster references in products."""
    try:
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
                else:
                    continue
                
                factory.get_product_repository(user_id).update(product['id'], product)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/roasters/default', methods=['GET'])
@validate_user_context
def get_default_roaster(user_id):
    """Get the default roaster."""
    try:
        factory = get_repository_factory()
        default_roaster = factory.get_roaster_repository(user_id).find_default()
        if not default_roaster:
            return jsonify({'error': 'No default roaster set'}), 404
        return jsonify(default_roaster)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/roasters/smart_default', methods=['GET'])
@validate_user_context
def get_smart_default_roaster(user_id):
    """Get the smart default roaster based on usage patterns."""
    try:
        factory = get_repository_factory()
        smart_default = factory.get_roaster_repository(user_id).get_smart_default()
        if not smart_default:
            return jsonify({'error': 'No roasters available'}), 404
        return jsonify(smart_default)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/roasters/<int:roaster_id>/set_default', methods=['POST'])
@validate_user_context
def set_default_roaster(user_id, roaster_id):
    """Set a roaster as the default."""
    try:
        factory = get_repository_factory()
        repo = factory.get_roaster_repository(user_id)
        roaster = repo.set_default(roaster_id)
        return jsonify(roaster)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/roasters/<int:roaster_id>/clear_default', methods=['POST'])
@validate_user_context
def clear_default_roaster(user_id, roaster_id):
    """Clear the default flag from a roaster."""
    try:
        factory = get_repository_factory()
        repo = factory.get_roaster_repository(user_id)
        roaster = repo.clear_default(roaster_id)
        return jsonify(roaster)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== BEAN TYPES ====================

@basic_lookups_bp.route('/bean_types', methods=['GET'])
@validate_user_context
def get_bean_types(user_id):
    """Get all bean types."""
    try:
        factory = get_repository_factory()
        bean_types = factory.get_bean_type_repository(user_id).find_all()
        return jsonify(bean_types)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/bean_types/<int:bean_type_id>', methods=['GET'])
@validate_user_context
def get_bean_type(user_id, bean_type_id):
    """Get a specific bean type."""
    try:
        factory = get_repository_factory()
        bean_type = factory.get_bean_type_repository(user_id).find_by_id(bean_type_id)
        if not bean_type:
            return jsonify({'error': 'Bean type not found'}), 404
        return jsonify(bean_type)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/bean_types', methods=['POST'])
@validate_user_context
def create_bean_type(user_id):
    """Create a new bean type."""
    try:
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        
        factory = get_repository_factory()
        bean_type = factory.get_bean_type_repository(user_id).create(data)
        return jsonify(bean_type), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/bean_types/<int:bean_type_id>', methods=['PUT'])
@validate_user_context
def update_bean_type(user_id, bean_type_id):
    """Update an existing bean type."""
    try:
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


@basic_lookups_bp.route('/bean_types/<int:bean_type_id>', methods=['DELETE'])
@validate_user_context
def delete_bean_type(user_id, bean_type_id):
    """Delete a bean type."""
    try:
        factory = get_repository_factory()
        success = factory.get_bean_type_repository(user_id).delete(bean_type_id)
        if not success:
            return jsonify({'error': 'Bean type not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/bean_types/<int:bean_type_id>/usage', methods=['GET'])
@validate_user_context
def check_bean_type_usage(user_id, bean_type_id):
    """Check if bean type is in use by products."""
    try:
        factory = get_repository_factory()
        bean_type = factory.get_bean_type_repository(user_id).find_by_id(bean_type_id)
        if not bean_type:
            return jsonify({'error': 'Bean type not found'}), 404
        
        products = factory.get_product_repository(user_id).find_all()
        usage_count = sum(1 for p in products if bean_type_id in (p.get('bean_type_id') or []))
        
        return jsonify({
            'in_use': usage_count > 0,
            'usage_count': usage_count,
            'usage_type': 'products'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/bean_types/<int:bean_type_id>/update_references', methods=['POST'])
@validate_user_context
def update_bean_type_references(user_id, bean_type_id):
    """Update or remove bean type references in products."""
    try:
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
            if not isinstance(bean_type_ids, list):
                bean_type_ids = [bean_type_ids] if bean_type_ids else []
            
            if bean_type_id in bean_type_ids:
                if action == 'remove':
                    bean_type_ids = [bt_id for bt_id in bean_type_ids if bt_id != bean_type_id]
                elif action == 'replace' and replacement_id:
                    bean_type_ids = [replacement_id if bt_id == bean_type_id else bt_id for bt_id in bean_type_ids]
                else:
                    continue
                
                product['bean_type_id'] = bean_type_ids
                factory.get_product_repository(user_id).update(product['id'], product)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== COUNTRIES ====================

@basic_lookups_bp.route('/countries', methods=['GET'])
@validate_user_context
def get_countries(user_id):
    """Get all countries."""
    try:
        factory = get_repository_factory()
        countries = factory.get_country_repository(user_id).find_all()
        return jsonify(countries)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/countries/<int:country_id>', methods=['GET'])
@validate_user_context
def get_country(user_id, country_id):
    """Get a specific country."""
    try:
        factory = get_repository_factory()
        country = factory.get_country_repository(user_id).find_by_id(country_id)
        if not country:
            return jsonify({'error': 'Country not found'}), 404
        return jsonify(country)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/countries', methods=['POST'])
@validate_user_context
def create_country(user_id):
    """Create a new country."""
    try:
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        
        factory = get_repository_factory()
        country = factory.get_country_repository(user_id).create(data)
        return jsonify(country), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/countries/<int:country_id>', methods=['PUT'])
@validate_user_context
def update_country(user_id, country_id):
    """Update an existing country."""
    try:
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


@basic_lookups_bp.route('/countries/<int:country_id>', methods=['DELETE'])
@validate_user_context
def delete_country(user_id, country_id):
    """Delete a country."""
    try:
        factory = get_repository_factory()
        success = factory.get_country_repository(user_id).delete(country_id)
        if not success:
            return jsonify({'error': 'Country not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/countries/<int:country_id>/usage', methods=['GET'])
@validate_user_context
def check_country_usage(user_id, country_id):
    """Check if country is in use by products."""
    try:
        factory = get_repository_factory()
        country = factory.get_country_repository(user_id).find_by_id(country_id)
        if not country:
            return jsonify({'error': 'Country not found'}), 404
        
        products = factory.get_product_repository(user_id).find_all()
        usage_count = sum(1 for p in products if p.get('country_id') == country_id)
        
        return jsonify({
            'in_use': usage_count > 0,
            'usage_count': usage_count,
            'usage_type': 'products'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/countries/<int:country_id>/update_references', methods=['POST'])
@validate_user_context
def update_country_references(user_id, country_id):
    """Update or remove country references in products."""
    try:
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
            if product.get('country_id') == country_id:
                if action == 'remove':
                    product['country_id'] = None
                elif action == 'replace' and replacement_id:
                    product['country_id'] = replacement_id
                else:
                    continue
                
                factory.get_product_repository(user_id).update(product['id'], product)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/countries/<int:country_id>/regions', methods=['GET', 'POST'])
@validate_user_context
def country_regions(user_id, country_id):
    """Get regions for a country or create a new region."""
    try:
        factory = get_repository_factory()
        
        # Verify country exists
        country = factory.get_country_repository(user_id).find_by_id(country_id)
        if not country:
            return jsonify({'error': 'Country not found'}), 404
        
        if request.method == 'GET':
            regions = factory.get_region_repository(user_id).find_by_country(country_id)
            return jsonify(regions)
        
        else:  # POST
            data = request.get_json()
            error_msg, status_code = validate_lookup_data(data)
            if error_msg:
                return jsonify({'error': error_msg}), status_code
            
            # Add country_id to the data
            data['country_id'] = country_id
            
            region = factory.get_region_repository(user_id).create(data)
            return jsonify(region), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== REGIONS ====================

@basic_lookups_bp.route('/regions', methods=['GET'])
@validate_user_context
def get_regions(user_id):
    """Get all regions."""
    try:
        factory = get_repository_factory()
        regions = factory.get_region_repository(user_id).find_all()
        return jsonify(regions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/regions/<int:region_id>', methods=['GET'])
@validate_user_context
def get_region(user_id, region_id):
    """Get a specific region."""
    try:
        factory = get_repository_factory()
        region = factory.get_region_repository(user_id).find_by_id(region_id)
        if not region:
            return jsonify({'error': 'Region not found'}), 404
        return jsonify(region)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/regions', methods=['POST'])
@validate_user_context
def create_region(user_id):
    """Create a new region."""
    try:
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        
        # Ensure country_id is provided
        if not data.get('country_id'):
            return jsonify({'error': 'country_id is required'}), 400
        
        factory = get_repository_factory()
        region = factory.get_region_repository(user_id).create(data)
        return jsonify(region), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/regions/<int:region_id>', methods=['PUT'])
@validate_user_context
def update_region(user_id, region_id):
    """Update an existing region."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        factory = get_repository_factory()
        region = factory.get_region_repository(user_id).update(region_id, data)
        if not region:
            return jsonify({'error': 'Region not found'}), 404
        return jsonify(region)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/regions/<int:region_id>', methods=['DELETE'])
@validate_user_context
def delete_region(user_id, region_id):
    """Delete a region."""
    try:
        factory = get_repository_factory()
        success = factory.get_region_repository(user_id).delete(region_id)
        if not success:
            return jsonify({'error': 'Region not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/regions/<int:region_id>/usage', methods=['GET'])
@validate_user_context
def check_region_usage(user_id, region_id):
    """Check if region is in use by products."""
    try:
        factory = get_repository_factory()
        region = factory.get_region_repository(user_id).find_by_id(region_id)
        if not region:
            return jsonify({'error': 'Region not found'}), 404
        
        products = factory.get_product_repository(user_id).find_all()
        usage_count = sum(1 for p in products if region_id in (p.get('region_id') or []))
        
        return jsonify({
            'in_use': usage_count > 0,
            'usage_count': usage_count,
            'usage_type': 'products'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/regions/<int:region_id>/update_references', methods=['POST'])
@validate_user_context
def update_region_references(user_id, region_id):
    """Update or remove region references in products."""
    try:
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
            if not isinstance(region_ids, list):
                region_ids = [region_ids] if region_ids else []
            
            if region_id in region_ids:
                if action == 'remove':
                    region_ids = [r_id for r_id in region_ids if r_id != region_id]
                elif action == 'replace' and replacement_id:
                    region_ids = [replacement_id if r_id == region_id else r_id for r_id in region_ids]
                else:
                    continue
                
                product['region_id'] = region_ids
                factory.get_product_repository(user_id).update(product['id'], product)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== BREW METHODS ====================

@basic_lookups_bp.route('/brew_methods', methods=['GET'])
@validate_user_context
def get_brew_methods(user_id):
    """Get all brew methods."""
    try:
        factory = get_repository_factory()
        brew_methods = factory.get_brew_method_repository(user_id).find_all()
        return jsonify(brew_methods)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/brew_methods/<int:brew_method_id>', methods=['GET'])
@validate_user_context
def get_brew_method(user_id, brew_method_id):
    """Get a specific brew method."""
    try:
        factory = get_repository_factory()
        brew_method = factory.get_brew_method_repository(user_id).find_by_id(brew_method_id)
        if not brew_method:
            return jsonify({'error': 'Brew method not found'}), 404
        return jsonify(brew_method)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/brew_methods', methods=['POST'])
@validate_user_context
def create_brew_method(user_id):
    """Create a new brew method."""
    try:
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        
        factory = get_repository_factory()
        brew_method = factory.get_brew_method_repository(user_id).create(data)
        return jsonify(brew_method), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/brew_methods/<int:brew_method_id>', methods=['PUT'])
@validate_user_context
def update_brew_method(user_id, brew_method_id):
    """Update an existing brew method."""
    try:
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


@basic_lookups_bp.route('/brew_methods/<int:brew_method_id>', methods=['DELETE'])
@validate_user_context
def delete_brew_method(user_id, brew_method_id):
    """Delete a brew method."""
    try:
        factory = get_repository_factory()
        success = factory.get_brew_method_repository(user_id).delete(brew_method_id)
        if not success:
            return jsonify({'error': 'Brew method not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/brew_methods/<int:brew_method_id>/usage', methods=['GET'])
@validate_user_context
def check_brew_method_usage(user_id, brew_method_id):
    """Check if brew method is in use by brew sessions."""
    try:
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


@basic_lookups_bp.route('/brew_methods/<int:brew_method_id>/update_references', methods=['POST'])
@validate_user_context
def update_brew_method_references(user_id, brew_method_id):
    """Update or remove brew method references in brew sessions."""
    try:
        data = request.get_json()
        action = data.get('action')
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
                else:
                    continue
                
                factory.get_brew_session_repository(user_id).update(session['id'], session)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== RECIPES ====================

@basic_lookups_bp.route('/recipes', methods=['GET'])
@validate_user_context
def get_recipes(user_id):
    """Get all recipes."""
    try:
        factory = get_repository_factory()
        recipes = factory.get_recipe_repository(user_id).find_all()
        return jsonify(recipes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/recipes/<int:recipe_id>', methods=['GET'])
@validate_user_context
def get_recipe(user_id, recipe_id):
    """Get a specific recipe."""
    try:
        factory = get_repository_factory()
        recipe = factory.get_recipe_repository(user_id).find_by_id(recipe_id)
        if not recipe:
            return jsonify({'error': 'Recipe not found'}), 404
        return jsonify(recipe)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/recipes', methods=['POST'])
@validate_user_context
def create_recipe(user_id):
    """Create a new recipe."""
    try:
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        
        factory = get_repository_factory()
        recipe = factory.get_recipe_repository(user_id).create(data)
        return jsonify(recipe), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/recipes/<int:recipe_id>', methods=['PUT'])
@validate_user_context
def update_recipe(user_id, recipe_id):
    """Update an existing recipe."""
    try:
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


@basic_lookups_bp.route('/recipes/<int:recipe_id>', methods=['DELETE'])
@validate_user_context
def delete_recipe(user_id, recipe_id):
    """Delete a recipe."""
    try:
        factory = get_repository_factory()
        success = factory.get_recipe_repository(user_id).delete(recipe_id)
        if not success:
            return jsonify({'error': 'Recipe not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/recipes/<int:recipe_id>/usage', methods=['GET'])
@validate_user_context
def check_recipe_usage(user_id, recipe_id):
    """Check if recipe is in use by brew sessions."""
    try:
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


@basic_lookups_bp.route('/recipes/<int:recipe_id>/update_references', methods=['POST'])
@validate_user_context
def update_recipe_references(user_id, recipe_id):
    """Update or remove recipe references in brew sessions."""
    try:
        data = request.get_json()
        action = data.get('action')
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
                else:
                    continue
                
                factory.get_brew_session_repository(user_id).update(session['id'], session)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== DECAF METHODS ====================

@basic_lookups_bp.route('/decaf_methods', methods=['GET'])
@validate_user_context
def get_decaf_methods(user_id):
    """Get all decaffeination methods."""
    try:
        factory = get_repository_factory()
        decaf_methods = factory.get_decaf_method_repository(user_id).find_all()
        return jsonify(decaf_methods)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/decaf_methods/<int:decaf_method_id>', methods=['GET'])
@validate_user_context
def get_decaf_method(user_id, decaf_method_id):
    """Get a specific decaffeination method."""
    try:
        factory = get_repository_factory()
        decaf_method = factory.get_decaf_method_repository(user_id).find_by_id(decaf_method_id)
        if not decaf_method:
            return jsonify({'error': 'Decaf method not found'}), 404
        return jsonify(decaf_method)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/decaf_methods', methods=['POST'])
@validate_user_context
def create_decaf_method(user_id):
    """Create a new decaffeination method."""
    try:
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        
        factory = get_repository_factory()
        decaf_method = factory.get_decaf_method_repository(user_id).create(data)
        return jsonify(decaf_method), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/decaf_methods/<int:decaf_method_id>', methods=['PUT'])
@validate_user_context
def update_decaf_method(user_id, decaf_method_id):
    """Update an existing decaffeination method."""
    try:
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


@basic_lookups_bp.route('/decaf_methods/<int:decaf_method_id>', methods=['DELETE'])
@validate_user_context
def delete_decaf_method(user_id, decaf_method_id):
    """Delete a decaffeination method."""
    try:
        factory = get_repository_factory()
        success = factory.get_decaf_method_repository(user_id).delete(decaf_method_id)
        if not success:
            return jsonify({'error': 'Decaf method not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@basic_lookups_bp.route('/decaf_methods/<int:decaf_method_id>/usage', methods=['GET'])
@validate_user_context
def check_decaf_method_usage(user_id, decaf_method_id):
    """Check if decaffeination method is in use by products."""
    try:
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


@basic_lookups_bp.route('/decaf_methods/<int:decaf_method_id>/update_references', methods=['POST'])
@validate_user_context
def update_decaf_method_references(user_id, decaf_method_id):
    """Update or remove decaffeination method references in products."""
    try:
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
                elif action == 'replace' and replacement_id:
                    product['decaf_method_id'] = replacement_id
                else:
                    continue
                
                factory.get_product_repository(user_id).update(product['id'], product)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500