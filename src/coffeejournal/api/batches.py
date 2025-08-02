"""
Batch and Brew Session API endpoints for the Coffee Journal application.

This module contains all endpoints related to coffee batches and brew sessions:
- GET /batches/{id} - Get a specific batch
- PUT /batches/{id} - Update a batch
- DELETE /batches/{id} - Delete a batch and related brew sessions
- GET /batches/{id}/brew_sessions - Get all brew sessions for a batch
- POST /batches/{id}/brew_sessions - Create a new brew session for a batch
- GET /brew_sessions - Get all brew sessions
- GET /brew_sessions/{id} - Get a specific brew session
- PUT /brew_sessions/{id} - Update a brew session
- DELETE /brew_sessions/{id} - Delete a brew session
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
from ..repositories.factory import get_repository_factory
from .utils import (
    calculate_brew_ratio,
    enrich_product_with_lookups,
    safe_float,
    safe_int,
    calculate_price_per_cup,
    enrich_brew_session_with_lookups,
    validate_tasting_score,
    get_user_id_from_request,
    validate_user_id
)

batches_bp = Blueprint('batches', __name__)


# --- Individual Batch Endpoints ---

@batches_bp.route('/batches/<int:batch_id>', methods=['GET'])
def get_batch(batch_id):
    """Get a specific batch."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    batch = factory.get_batch_repository(user_id).find_by_id(batch_id)
    
    if not batch:
        return jsonify({'error': 'Batch not found'}), 404
    
    # Enrich with product information
    product = factory.get_product_repository(user_id).find_by_id(batch['product_id'])
    if product:
        enriched_product = enrich_product_with_lookups(product, factory, user_id)
        roaster_name = enriched_product.get('roaster', {}).get('name', 'N/A') if enriched_product.get('roaster') else 'N/A'
        bean_type_names = ', '.join([bt.get('name', 'N/A') for bt in enriched_product.get('bean_type', [])]) if enriched_product.get('bean_type') else 'N/A'
        batch['product_name'] = f"{roaster_name} - {bean_type_names}"
    else:
        batch['product_name'] = "N/A Product"
    
    batch['price_per_cup'] = calculate_price_per_cup(batch.get('price'), batch.get('amount_grams'))
    
    return jsonify(batch)


@batches_bp.route('/batches/<int:batch_id>/detail', methods=['GET'])
def get_batch_detail(batch_id):
    """Get detailed information about a batch including statistics."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    batch_repo = factory.get_batch_repository(user_id)
    product_repo = factory.get_product_repository(user_id)
    session_repo = factory.get_brew_session_repository(user_id)
    
    batch = batch_repo.find_by_id(batch_id)
    if not batch:
        return jsonify({'error': 'Batch not found'}), 404
    
    # Get product information
    product = product_repo.find_by_id(batch['product_id'])
    enriched_product = enrich_product_with_lookups(product, factory, user_id) if product else None
    
    # Get all brew sessions for this batch
    sessions = session_repo.find_by_batch(batch_id)
    
    # Calculate statistics
    stats = {
        'total_brew_sessions': len(sessions),
        'total_coffee_used': sum(s.get('amount_coffee_grams', 0) for s in sessions),
        'total_water_used': sum(s.get('amount_water_grams', 0) for s in sessions),
        'coffee_remaining': max(0, batch.get('amount_grams', 0) - sum(s.get('amount_coffee_grams', 0) for s in sessions)),
        'sessions_remaining_estimate': 0,
        'avg_rating': None,
        'rating_breakdown': {
            'overall': [],
            'aroma': [],
            'acidity': [],
            'body': [],
            'flavor': [],
            'aftertaste': []
        }
    }
    
    # Calculate sessions remaining estimate
    if sessions and stats['coffee_remaining'] > 0:
        avg_coffee_per_session = stats['total_coffee_used'] / len(sessions)
        if avg_coffee_per_session > 0:
            stats['sessions_remaining_estimate'] = int(stats['coffee_remaining'] / avg_coffee_per_session)
    
    # Calculate rating statistics
    for session in sessions:
        for rating_type in stats['rating_breakdown'].keys():
            value = session.get(f'rating_{rating_type}')
            if value and isinstance(value, (int, float)):
                stats['rating_breakdown'][rating_type].append(value)
    
    # Calculate averages
    for rating_type, values in stats['rating_breakdown'].items():
        if values:
            stats['rating_breakdown'][rating_type] = {
                'avg': round(sum(values) / len(values), 1),
                'count': len(values),
                'min': min(values),
                'max': max(values)
            }
        else:
            stats['rating_breakdown'][rating_type] = None
    
    # Overall average
    overall_ratings = [s.get('rating_overall') for s in sessions if s.get('rating_overall')]
    if overall_ratings:
        stats['avg_rating'] = round(sum(overall_ratings) / len(overall_ratings), 1)
    
    # Calculate price per cup
    price_per_cup = calculate_price_per_cup(batch, stats['total_brew_sessions'])
    
    return jsonify({
        'batch': batch,
        'product': enriched_product,
        'statistics': stats,
        'price_per_cup': price_per_cup,
        'recent_sessions': sessions[-10:] if sessions else [],  # Last 10 sessions
        'all_sessions': len(sessions)  # Count of all sessions
    })


@batches_bp.route('/batches/<int:batch_id>', methods=['PUT'])
def update_batch(batch_id):
    """Update a batch."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    data = request.json
    
    # Check if batch exists
    batch_repo = factory.get_batch_repository(user_id)
    existing_batch = batch_repo.find_by_id(batch_id)
    if not existing_batch:
        return jsonify({'error': 'Batch not found'}), 404
    
    # Validate product exists if changing it
    product_id = data.get('product_id', existing_batch['product_id'])
    product = factory.get_product_repository(user_id).find_by_id(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Update batch
    batch_data = {
        'product_id': product_id,
        'roast_date': data.get('roast_date'),
        'purchase_date': data.get('purchase_date'),
        'amount_grams': safe_float(data.get('amount_grams')),
        'price': safe_float(data.get('price')),
        'seller': data.get('seller'),
        'notes': data.get('notes'),
        'rating': safe_int(data.get('rating')),
        'is_active': data.get('is_active', existing_batch.get('is_active', True))  # Preserve existing or default to True
    }
    
    batch = batch_repo.update(batch_id, batch_data)
    
    # Add enriched data
    enriched_product = enrich_product_with_lookups(product, factory, user_id)
    roaster_name = enriched_product.get('roaster', {}).get('name', 'N/A') if enriched_product.get('roaster') else 'N/A'
    bean_type_names = ', '.join([bt.get('name', 'N/A') for bt in enriched_product.get('bean_type', [])]) if enriched_product.get('bean_type') else 'N/A'
    batch['product_name'] = f"{roaster_name} - {bean_type_names}"
    batch['price_per_cup'] = calculate_price_per_cup(batch.get('price'), batch.get('amount_grams'))
    
    return jsonify(batch)


@batches_bp.route('/batches/<int:batch_id>', methods=['DELETE'])
def delete_batch(batch_id):
    """Delete a batch and all related brew sessions."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    
    # Check if batch exists
    batch_repo = factory.get_batch_repository(user_id)
    batch = batch_repo.find_by_id(batch_id)
    if not batch:
        return jsonify({'error': 'Batch not found'}), 404
    
    # Delete related brew sessions
    factory.get_brew_session_repository(user_id).delete_by_batch(batch_id)
    
    # Delete batch
    batch_repo.delete(batch_id)
    
    return '', 204


# --- Nested Brew Session Endpoints ---

@batches_bp.route('/batches/<int:batch_id>/brew_sessions', methods=['GET', 'POST'])
def handle_batch_brew_sessions(batch_id):
    """Get all brew sessions for a batch or create a new brew session."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    
    # Check if batch exists
    batch_repo = factory.get_batch_repository(user_id)
    batch = batch_repo.find_by_id(batch_id)
    if not batch:
        return jsonify({'error': 'Batch not found'}), 404
    
    if request.method == 'GET':
        sessions = factory.get_brew_session_repository(user_id).find_by_batch(batch_id)
        
        # Get repositories for enrichment
        product_repo = factory.get_product_repository(user_id)
        brew_method_repo = factory.get_brew_method_repository(user_id)
        recipe_repo = factory.get_recipe_repository(user_id)
        grinder_repo = factory.get_grinder_repository(user_id)
        filter_repo = factory.get_filter_repository(user_id)
        kettle_repo = factory.get_kettle_repository(user_id)
        scale_repo = factory.get_scale_repository(user_id)
        
        # Enrich with product and batch information
        for session in sessions:
            # Get product info for enrichment
            product = product_repo.find_by_id(batch.get('product_id'))
            if product:
                # Use consistent product enrichment
                enriched_product = enrich_product_with_lookups(product.copy(), factory, user_id)
                
                # Create display name from enriched data
                roaster_name = enriched_product.get('roaster', {}).get('name', 'N/A') if enriched_product.get('roaster') else 'N/A'
                bean_type_display = enriched_product.get('bean_type', [])
                if isinstance(bean_type_display, list) and bean_type_display:
                    bean_type_names = [bt.get('name', 'N/A') for bt in bean_type_display]
                    bean_type_str = ', '.join(bean_type_names)
                else:
                    bean_type_str = 'N/A'
                
                session['product_name'] = f"{roaster_name} - {bean_type_str}"
            
            # Add brew method, recipe, grinder, filter, kettle, and scale objects
            if session.get('brew_method_id'):
                method = brew_method_repo.find_by_id(session['brew_method_id'])
                session['brew_method'] = method if method else None
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
                filter_lookup = filter_repo.find_by_id(session['filter_id'])
                session['filter'] = filter_lookup if filter_lookup else None
            else:
                session['filter'] = None
            
            if session.get('kettle_id'):
                kettle_lookup = kettle_repo.find_by_id(session['kettle_id'])
                session['kettle'] = kettle_lookup if kettle_lookup else None
            else:
                session['kettle'] = None
            
            if session.get('scale_id'):
                scale_lookup = scale_repo.find_by_id(session['scale_id'])
                session['scale'] = scale_lookup if scale_lookup else None
            else:
                session['scale'] = None
            
            # Calculate brew ratio
            session['brew_ratio'] = calculate_brew_ratio(session.get('amount_coffee_grams'), session.get('amount_water_grams'))
        
        return jsonify(sessions)
    
    elif request.method == 'POST':
        """Create a new brew session for the specified batch."""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get or create brew method, recipe, grinder, filter, kettle, and scale
        brew_method_repo = factory.get_brew_method_repository(user_id)
        recipe_repo = factory.get_recipe_repository(user_id)
        grinder_repo = factory.get_grinder_repository(user_id)
        filter_repo = factory.get_filter_repository(user_id)
        kettle_repo = factory.get_kettle_repository(user_id)
        scale_repo = factory.get_scale_repository(user_id)
        
        brew_method = None
        if data.get('brew_method'):
            brew_method = brew_method_repo.get_or_create_by_identifier(data['brew_method'])
        
        recipe = None
        if data.get('recipe'):
            recipe = recipe_repo.get_or_create_by_identifier(data['recipe'])
        
        grinder = None
        if data.get('grinder'):
            grinder = grinder_repo.get_or_create_by_identifier(data['grinder'])
        
        filter_type = None
        if data.get('filter'):
            filter_type = filter_repo.get_or_create_by_identifier(data['filter'])
        
        kettle = None
        if data.get('kettle'):
            kettle = kettle_repo.get_or_create_by_identifier(data['kettle'])
        
        scale = None
        if data.get('scale'):
            scale = scale_repo.get_or_create_by_identifier(data['scale'])
        
        # Extract and validate fields from request
        # Convert numeric fields with type safety
        amount_coffee_grams = safe_float(data.get('amount_coffee_grams'))
        amount_water_grams = safe_float(data.get('amount_water_grams'))
        brew_temperature_c = safe_float(data.get('brew_temperature_c'))
        bloom_time_seconds = safe_int(data.get('bloom_time_seconds'))
        brew_time_seconds = safe_int(data.get('brew_time_seconds'))
        score = safe_float(data.get('score'))
        
        # Validate tasting scores (1-10 range)
        sweetness = safe_float(data.get('sweetness'))
        acidity = safe_float(data.get('acidity'))
        bitterness = safe_float(data.get('bitterness'))
        body = safe_float(data.get('body'))
        aroma = safe_float(data.get('aroma'))
        flavor_profile_match = safe_float(data.get('flavor_profile_match'))
        
        # Validate tasting scores are in range
        validation_errors = []
        for field_name, field_value in [
            ('sweetness', sweetness),
            ('acidity', acidity),
            ('bitterness', bitterness),
            ('body', body),
            ('aroma', aroma),
            ('flavor_profile_match', flavor_profile_match)
        ]:
            if field_value is not None and (field_value < 1 or field_value > 10):
                validation_errors.append(f"{field_name} must be between 1 and 10")
        
        # Validate overall score is in range (can be float)
        if score is not None and (score < 1.0 or score > 10.0):
            validation_errors.append("score must be between 1.0 and 10.0")
        
        if validation_errors:
            return jsonify({'error': '; '.join(validation_errors)}), 400
        
        session_data = {
            'timestamp': data.get('timestamp', datetime.utcnow().isoformat()),
            'product_batch_id': batch_id,  # Use batch_id from URL
            'product_id': batch.get('product_id'),  # Get product_id from batch
            'recipe_id': recipe['id'] if recipe else data.get('recipe_id'),
            'brew_method_id': brew_method['id'] if brew_method else data.get('brew_method_id'),
            'grinder_id': grinder['id'] if grinder else data.get('grinder_id'),
            'grinder_setting': data.get('grinder_setting'),
            'filter_id': filter_type['id'] if filter_type else data.get('filter_id'),
            'kettle_id': kettle['id'] if kettle else data.get('kettle_id'),
            'scale_id': scale['id'] if scale else data.get('scale_id'),
            'amount_coffee_grams': amount_coffee_grams,
            'amount_water_grams': amount_water_grams,
            'brew_temperature_c': brew_temperature_c,
            'bloom_time_seconds': bloom_time_seconds,
            'brew_time_seconds': brew_time_seconds,
            'sweetness': sweetness,
            'acidity': acidity,
            'bitterness': bitterness,
            'body': body,
            'aroma': aroma,
            'flavor_profile_match': flavor_profile_match,
            'score': score,
            'notes': data.get('notes')
        }
        
        session_repo = factory.get_brew_session_repository(user_id)
        session = session_repo.create(session_data)
        
        # Enrich with product information
        product_repo = factory.get_product_repository(user_id)
        product = product_repo.find_by_id(batch.get('product_id'))
        if product:
            # Use consistent product enrichment
            enriched_product = enrich_product_with_lookups(product.copy(), factory, user_id)
            
            # Create display name from enriched data
            roaster_name = enriched_product.get('roaster', {}).get('name', 'N/A') if enriched_product.get('roaster') else 'N/A'
            bean_type_display = enriched_product.get('bean_type', [])
            if isinstance(bean_type_display, list) and bean_type_display:
                bean_type_names = [bt.get('name', 'N/A') for bt in bean_type_display]
                bean_type_str = ', '.join(bean_type_names)
            else:
                bean_type_str = 'N/A'
            
            session['product_name'] = f"{roaster_name} - {bean_type_str}"
        
        # Add brew method, recipe, grinder, filter, kettle, and scale objects
        if brew_method:
            session['brew_method'] = brew_method
        elif session.get('brew_method_id'):
            method = brew_method_repo.find_by_id(session['brew_method_id'])
            session['brew_method'] = method if method else None
        else:
            session['brew_method'] = None
        
        if recipe:
            session['recipe'] = recipe
        elif session.get('recipe_id'):
            rec = recipe_repo.find_by_id(session['recipe_id'])
            session['recipe'] = rec if rec else None
        else:
            session['recipe'] = None
        
        if grinder:
            session['grinder'] = grinder
        elif session.get('grinder_id'):
            grind = grinder_repo.find_by_id(session['grinder_id'])
            session['grinder'] = grind if grind else None
        else:
            session['grinder'] = None
        
        if filter_type:
            session['filter'] = filter_type
        elif session.get('filter_id'):
            filt = filter_repo.find_by_id(session['filter_id'])
            session['filter'] = filt if filt else None
        else:
            session['filter'] = None
        
        if kettle:
            session['kettle'] = kettle
        elif session.get('kettle_id'):
            kett = kettle_repo.find_by_id(session['kettle_id'])
            session['kettle'] = kett if kett else None
        else:
            session['kettle'] = None
        
        if scale:
            session['scale'] = scale
        elif session.get('scale_id'):
            sc = scale_repo.find_by_id(session['scale_id'])
            session['scale'] = sc if sc else None
        else:
            session['scale'] = None
        
        # Calculate brew ratio
        session['brew_ratio'] = calculate_brew_ratio(session.get('amount_coffee_grams'), session.get('amount_water_grams'))
        
        return jsonify(session), 201


# --- Global Brew Session Endpoints ---

@batches_bp.route('/brew_sessions', methods=['GET'])
def get_all_brew_sessions():
    """Get all brew sessions from all batches."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    sessions = factory.get_brew_session_repository(user_id).find_all()
    
    # Enrich with product information and calculate brew ratio
    product_repo = factory.get_product_repository(user_id)
    batch_repo = factory.get_batch_repository(user_id)
    brew_method_repo = factory.get_brew_method_repository(user_id)
    recipe_repo = factory.get_recipe_repository(user_id)
    grinder_repo = factory.get_grinder_repository(user_id)
    filter_repo = factory.get_filter_repository(user_id)
    kettle_repo = factory.get_kettle_repository(user_id)
    scale_repo = factory.get_scale_repository(user_id)
    
    for session in sessions:
        # Get product and batch info for enrichment
        product = product_repo.find_by_id(session.get('product_id'))
        batch = batch_repo.find_by_id(session.get('product_batch_id'))
        
        if product:
            # Use consistent product enrichment
            enriched_product = enrich_product_with_lookups(product.copy(), factory, user_id)
            
            # Create display name from enriched data
            roaster_name = enriched_product.get('roaster', {}).get('name', 'N/A') if enriched_product.get('roaster') else 'N/A'
            bean_type_display = enriched_product.get('bean_type', [])
            if isinstance(bean_type_display, list) and bean_type_display:
                bean_type_names = [bt.get('name', 'N/A') for bt in bean_type_display]
                bean_type_str = ', '.join(bean_type_names)
            else:
                bean_type_str = 'N/A'
            
            session['product_name'] = f"{roaster_name} - {bean_type_str}"
            session['product_details'] = {
                'roaster': enriched_product.get('roaster'),
                'bean_type': enriched_product.get('bean_type'),
                'product_name': enriched_product.get('product_name'),
                'roast_date': batch.get('roast_date') if batch else None,
                'roast_type': enriched_product.get('roast_type'),
                'decaf': enriched_product.get('decaf', False)
            }
        else:
            session['product_details'] = {}
        
        # Add brew method, recipe, grinder, filter, kettle, and scale objects
        if session.get('brew_method_id'):
            method = brew_method_repo.find_by_id(session['brew_method_id'])
            session['brew_method'] = method if method else None
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
            filter_lookup = filter_repo.find_by_id(session['filter_id'])
            session['filter'] = filter_lookup if filter_lookup else None
        else:
            session['filter'] = None
        
        if session.get('kettle_id'):
            kettle_lookup = kettle_repo.find_by_id(session['kettle_id'])
            session['kettle'] = kettle_lookup if kettle_lookup else None
        else:
            session['kettle'] = None
        
        if session.get('scale_id'):
            scale_lookup = scale_repo.find_by_id(session['scale_id'])
            session['scale'] = scale_lookup if scale_lookup else None
        else:
            session['scale'] = None
        
        # Calculate brew ratio using consistent field names
        session['brew_ratio'] = calculate_brew_ratio(session.get('amount_coffee_grams'), session.get('amount_water_grams'))
    
    return jsonify(sessions)


@batches_bp.route('/brew_sessions/<int:session_id>', methods=['GET'])
def get_brew_session(session_id):
    """Get a specific brew session."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    session = factory.get_brew_session_repository(user_id).find_by_id(session_id)
    
    if not session:
        return jsonify({'error': 'Brew session not found'}), 404
    
    # Enrich with product and batch information
    product_repo = factory.get_product_repository(user_id)
    batch_repo = factory.get_batch_repository(user_id)
    brew_method_repo = factory.get_brew_method_repository(user_id)
    recipe_repo = factory.get_recipe_repository(user_id)
    
    # Calculate brew ratio
    session['brew_ratio'] = calculate_brew_ratio(
        session.get('amount_coffee_grams'),
        session.get('amount_water_grams')
    )
    
    # Get product details
    product = product_repo.find_by_id(session['product_id'])
    batch = batch_repo.find_by_id(session['product_batch_id'])
    
    if product:
        # Use consistent product enrichment
        enriched_product = enrich_product_with_lookups(product.copy(), factory, user_id)
        session['product_details'] = {
            'roaster': enriched_product.get('roaster'),
            'bean_type': enriched_product.get('bean_type'),
            'roast_date': batch.get('roast_date') if batch else None,
            'roast_type': enriched_product.get('roast_type'),
            'decaf': enriched_product.get('decaf', False)
        }
    else:
        session['product_details'] = {}
    
    # Add brew method, recipe, grinder, filter, kettle, and scale objects
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
        grinder_repo = factory.get_grinder_repository(user_id)
        grinder = grinder_repo.find_by_id(session['grinder_id'])
        session['grinder'] = grinder if grinder else None
    else:
        session['grinder'] = None
    
    if session.get('filter_id'):
        filter_repo = factory.get_filter_repository(user_id)
        filter_lookup = filter_repo.find_by_id(session['filter_id'])
        session['filter'] = filter_lookup if filter_lookup else None
    else:
        session['filter'] = None
    
    if session.get('kettle_id'):
        kettle_repo = factory.get_kettle_repository(user_id)
        kettle_lookup = kettle_repo.find_by_id(session['kettle_id'])
        session['kettle'] = kettle_lookup if kettle_lookup else None
    else:
        session['kettle'] = None
    
    if session.get('scale_id'):
        scale_repo = factory.get_scale_repository(user_id)
        scale_lookup = scale_repo.find_by_id(session['scale_id'])
        session['scale'] = scale_lookup if scale_lookup else None
    else:
        session['scale'] = None
    
    return jsonify(session)


@batches_bp.route('/brew_sessions/<int:session_id>/detail', methods=['GET'])
def get_brew_session_detail(session_id):
    """Get detailed information about a brew session including related data."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    session_repo = factory.get_brew_session_repository(user_id)
    batch_repo = factory.get_batch_repository(user_id)
    product_repo = factory.get_product_repository(user_id)
    
    session = session_repo.find_by_id(session_id)
    if not session:
        return jsonify({'error': 'Brew session not found'}), 404
    
    # Enrich session with lookup data
    enriched_session = enrich_brew_session_with_lookups(session, factory, user_id)
    
    # Get related batch and product info
    batch = batch_repo.find_by_id(session['product_batch_id']) if session.get('product_batch_id') else None
    product = product_repo.find_by_id(session['product_id']) if session.get('product_id') else None
    enriched_product = enrich_product_with_lookups(product, factory, user_id) if product else None
    
    # Calculate brew ratio if possible
    brew_ratio = None
    if session.get('amount_coffee_grams') and session.get('amount_water_grams'):
        brew_ratio = calculate_brew_ratio(session['amount_coffee_grams'], session['amount_water_grams'])
    
    # Calculate extraction details
    extraction_details = {
        'brew_ratio': brew_ratio,
        'coffee_to_water_ratio': f"1:{round(session.get('amount_water_grams', 0) / session.get('amount_coffee_grams', 1), 1)}" if session.get('amount_coffee_grams') else None,
        'extraction_time_formatted': None,
        'water_temp_celsius': session.get('water_temperature'),
        'water_temp_fahrenheit': round((session.get('water_temperature', 0) * 9/5) + 32, 1) if session.get('water_temperature') else None
    }
    
    # Format extraction time
    if session.get('extraction_time_minutes'):
        total_seconds = int(session['extraction_time_minutes'] * 60)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        extraction_details['extraction_time_formatted'] = f"{minutes}:{seconds:02d}"
    
    # Compile all rating information
    ratings = {
        'overall': session.get('rating_overall'),
        'aroma': session.get('rating_aroma'),
        'acidity': session.get('rating_acidity'),
        'body': session.get('rating_body'),
        'flavor': session.get('rating_flavor'),
        'aftertaste': session.get('rating_aftertaste'),
        'has_ratings': any(session.get(f'rating_{r}') for r in ['overall', 'aroma', 'acidity', 'body', 'flavor', 'aftertaste'])
    }
    
    # Get other sessions from same batch for comparison
    other_sessions = []
    if batch:
        all_batch_sessions = session_repo.find_by_batch(batch['id'])
        other_sessions = [s for s in all_batch_sessions if s['id'] != session_id][-5:]  # Last 5 other sessions
    
    return jsonify({
        'session': enriched_session,
        'batch': batch,
        'product': enriched_product,
        'extraction_details': extraction_details,
        'ratings': ratings,
        'related_sessions': other_sessions,
        'batch_session_count': len(other_sessions) + 1  # Including current session
    })


@batches_bp.route('/brew_sessions/<int:session_id>', methods=['PUT'])
def update_brew_session(session_id):
    """Update a brew session."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    data = request.json
    
    # Check if session exists
    session_repo = factory.get_brew_session_repository(user_id)
    existing_session = session_repo.find_by_id(session_id)
    if not existing_session:
        return jsonify({'error': 'Brew session not found'}), 404
    
    # Validate product and batch if changing them
    # Convert string IDs to integers (frontend sends strings from form inputs)
    # For valid strings (like "123"), convert to int. For invalid values (empty string, None), 
    # let the subsequent lookup fail with 404 as expected by tests
    raw_batch_id = data.get('product_batch_id', existing_session['product_batch_id'])
    raw_product_id = data.get('product_id', existing_session['product_id'])
    
    # Only convert valid string representations to integers
    # Invalid values (None, empty string) will be passed through and cause 404 in lookup
    if isinstance(raw_batch_id, str) and raw_batch_id.strip() and raw_batch_id.isdigit():
        product_batch_id = int(raw_batch_id)
    else:
        product_batch_id = raw_batch_id
        
    if isinstance(raw_product_id, str) and raw_product_id.strip() and raw_product_id.isdigit():
        product_id = int(raw_product_id)
    else:
        product_id = raw_product_id
    
    product = factory.get_product_repository(user_id).find_by_id(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    batch = factory.get_batch_repository(user_id).find_by_id(product_batch_id)
    if not batch:
        return jsonify({'error': 'Batch not found'}), 404
    
    # Validate that the batch belongs to the specified product
    if batch['product_id'] != product_id:
        return jsonify({'error': 'Batch does not belong to the specified product'}), 400
    
    # Get or create brew method, recipe, grinder, filter, kettle, and scale
    brew_method_repo = factory.get_brew_method_repository(user_id)
    recipe_repo = factory.get_recipe_repository(user_id)
    grinder_repo = factory.get_grinder_repository(user_id)
    filter_repo = factory.get_filter_repository(user_id)
    kettle_repo = factory.get_kettle_repository(user_id)
    scale_repo = factory.get_scale_repository(user_id)
    
    brew_method = None
    if data.get('brew_method'):
        brew_method = brew_method_repo.get_or_create_by_identifier(data['brew_method'])
    
    recipe = None
    if data.get('recipe'):
        recipe = recipe_repo.get_or_create_by_identifier(data['recipe'])
    
    grinder = None
    if data.get('grinder'):
        grinder = grinder_repo.get_or_create_by_identifier(data['grinder'])
    
    filter_type = None
    if data.get('filter'):
        filter_type = filter_repo.get_or_create_by_identifier(data['filter'])
    
    kettle = None
    if data.get('kettle'):
        kettle = kettle_repo.get_or_create_by_identifier(data['kettle'])
    
    scale = None
    if data.get('scale'):
        scale = scale_repo.get_or_create_by_identifier(data['scale'])
    
    # Extract and validate fields from request
    # Convert numeric fields with type safety
    amount_coffee_grams = safe_float(data.get('amount_coffee_grams'))
    amount_water_grams = safe_float(data.get('amount_water_grams'))
    brew_temperature_c = safe_float(data.get('brew_temperature_c'))
    bloom_time_seconds = safe_int(data.get('bloom_time_seconds'))
    brew_time_seconds = safe_int(data.get('brew_time_seconds'))
    score = safe_float(data.get('score'))
    
    # Validate tasting scores (1-10 range)
    sweetness = safe_float(data.get('sweetness'))
    acidity = safe_float(data.get('acidity'))
    bitterness = safe_float(data.get('bitterness'))
    body = safe_float(data.get('body'))
    aroma = safe_float(data.get('aroma'))
    flavor_profile_match = safe_float(data.get('flavor_profile_match'))
    
    # Validate tasting scores are in range
    validation_errors = []
    for field_name, field_value in [
        ('sweetness', sweetness),
        ('acidity', acidity),
        ('bitterness', bitterness),
        ('body', body),
        ('aroma', aroma),
        ('flavor_profile_match', flavor_profile_match)
    ]:
        if field_value is not None and (field_value < 1 or field_value > 10):
            validation_errors.append(f"{field_name} must be between 1 and 10")
    
    # Validate overall score is in range (can be float)
    if score is not None and (score < 1.0 or score > 10.0):
        validation_errors.append("score must be between 1.0 and 10.0")
    
    if validation_errors:
        return jsonify({'error': '; '.join(validation_errors)}), 400
    
    # Update brew session (only update fields that are provided)
    session_data = existing_session.copy()
    session_data.update({
        'timestamp': data.get('timestamp', existing_session['timestamp']),
        'product_batch_id': product_batch_id,
        'product_id': product_id,
        'brew_method_id': brew_method['id'] if brew_method else existing_session.get('brew_method_id'),
        'recipe_id': recipe['id'] if recipe else existing_session.get('recipe_id'),
        'grinder_id': grinder['id'] if grinder else existing_session.get('grinder_id'),
        'grinder_setting': data.get('grinder_setting', existing_session.get('grinder_setting')),
        'filter_id': filter_type['id'] if filter_type else existing_session.get('filter_id'),
        'kettle_id': kettle['id'] if kettle else existing_session.get('kettle_id'),
        'scale_id': scale['id'] if scale else existing_session.get('scale_id'),
        'amount_coffee_grams': amount_coffee_grams if amount_coffee_grams is not None else existing_session.get('amount_coffee_grams'),
        'amount_water_grams': amount_water_grams if amount_water_grams is not None else existing_session.get('amount_water_grams'),
        'brew_temperature_c': brew_temperature_c if brew_temperature_c is not None else existing_session.get('brew_temperature_c'),
        'bloom_time_seconds': bloom_time_seconds if bloom_time_seconds is not None else existing_session.get('bloom_time_seconds'),
        'brew_time_seconds': brew_time_seconds if brew_time_seconds is not None else existing_session.get('brew_time_seconds'),
        'sweetness': sweetness if sweetness is not None else existing_session.get('sweetness'),
        'acidity': acidity if acidity is not None else existing_session.get('acidity'),
        'bitterness': bitterness if bitterness is not None else existing_session.get('bitterness'),
        'body': body if body is not None else existing_session.get('body'),
        'aroma': aroma if aroma is not None else existing_session.get('aroma'),
        'flavor_profile_match': flavor_profile_match if flavor_profile_match is not None else existing_session.get('flavor_profile_match'),
        'score': score if score is not None else existing_session.get('score'),
        'notes': data.get('notes', existing_session.get('notes'))
    })
    
    session = session_repo.update(session_id, session_data)
    
    # Add enriched data
    session['brew_ratio'] = calculate_brew_ratio(
        session.get('amount_coffee_grams'),
        session.get('amount_water_grams')
    )
    session['brew_method'] = brew_method if brew_method else None
    session['recipe'] = recipe if recipe else None
    
    if grinder:
        session['grinder'] = grinder
    elif session.get('grinder_id'):
        grinder_lookup = grinder_repo.find_by_id(session['grinder_id'])
        session['grinder'] = grinder_lookup if grinder_lookup else None
    else:
        session['grinder'] = None
    
    if filter_type:
        session['filter'] = filter_type
    elif session.get('filter_id'):
        filter_lookup = filter_repo.find_by_id(session['filter_id'])
        session['filter'] = filter_lookup if filter_lookup else None
    else:
        session['filter'] = None
    
    if kettle:
        session['kettle'] = kettle
    elif session.get('kettle_id'):
        kettle_lookup = kettle_repo.find_by_id(session['kettle_id'])
        session['kettle'] = kettle_lookup if kettle_lookup else None
    else:
        session['kettle'] = None
    
    if scale:
        session['scale'] = scale
    elif session.get('scale_id'):
        scale_lookup = scale_repo.find_by_id(session['scale_id'])
        session['scale'] = scale_lookup if scale_lookup else None
    else:
        session['scale'] = None
    
    # Use consistent product enrichment for product details
    enriched_product = enrich_product_with_lookups(product, factory, user_id)
    session['product_details'] = {
        'roaster': enriched_product.get('roaster'),
        'bean_type': enriched_product.get('bean_type'),
        'product_name': enriched_product.get('product_name'),
        'roast_date': batch.get('roast_date'),
        'roast_type': enriched_product.get('roast_type'),
        'decaf': enriched_product.get('decaf', False)
    }
    
    return jsonify(session)


@batches_bp.route('/brew_sessions/<int:session_id>', methods=['DELETE'])
def delete_brew_session(session_id):
    """Delete a brew session."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    
    # Check if session exists
    session_repo = factory.get_brew_session_repository(user_id)
    session = session_repo.find_by_id(session_id)
    if not session:
        return jsonify({'error': 'Brew session not found'}), 404
    
    # Delete session
    session_repo.delete(session_id)
    
    return '', 204


@batches_bp.route('/brew_sessions/defaults', methods=['GET'])
def get_brew_session_defaults():
    """Get smart defaults for creating a new brew session."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    
    # Get smart defaults for each equipment type
    defaults = {
        'brew_method': None,
        'recipe': None,
        'grinder': None,
        'filter': None,
        'kettle': None,
        'scale': None
    }
    
    # Get smart default for each lookup type
    brew_method_repo = factory.get_brew_method_repository(user_id)
    recipe_repo = factory.get_recipe_repository(user_id)
    grinder_repo = factory.get_grinder_repository(user_id)
    filter_repo = factory.get_filter_repository(user_id)
    kettle_repo = factory.get_kettle_repository(user_id)
    scale_repo = factory.get_scale_repository(user_id)
    
    # Fetch smart defaults
    brew_method_default = brew_method_repo.get_smart_default(factory)
    if brew_method_default:
        defaults['brew_method'] = brew_method_default
    
    recipe_default = recipe_repo.get_smart_default(factory)
    if recipe_default:
        defaults['recipe'] = recipe_default
    
    grinder_default = grinder_repo.get_smart_default(factory)
    if grinder_default:
        defaults['grinder'] = grinder_default
    
    filter_default = filter_repo.get_smart_default(factory)
    if filter_default:
        defaults['filter'] = filter_default
    
    kettle_default = kettle_repo.get_smart_default(factory)
    if kettle_default:
        defaults['kettle'] = kettle_default
    
    scale_default = scale_repo.get_smart_default(factory)
    if scale_default:
        defaults['scale'] = scale_default
    
    return jsonify(defaults)


@batches_bp.route('/batches/<int:batch_id>/brew_sessions/<int:session_id>/duplicate', methods=['POST'])
def duplicate_brew_session(batch_id, session_id):
    """Duplicate a brew session."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    
    # Check if batch exists
    batch_repo = factory.get_batch_repository(user_id)
    batch = batch_repo.find_by_id(batch_id)
    if not batch:
        return jsonify({'message': 'Batch not found'}), 404
    
    # Check if session exists
    session_repo = factory.get_brew_session_repository(user_id)
    original_session = session_repo.find_by_id(session_id)
    if not original_session:
        return jsonify({'message': 'Brew session not found'}), 404
    
    # Verify session belongs to the specified batch
    if original_session.get('product_batch_id') != batch_id:
        return jsonify({'message': 'Brew session does not belong to batch'}), 400
    
    # Create copy of session data with new timestamp
    duplicate_data = original_session.copy()
    
    # Remove ID and timestamps so new ones are generated
    duplicate_data.pop('id', None)
    duplicate_data.pop('created_at', None)
    duplicate_data.pop('updated_at', None)
    
    # Set new timestamp to current time
    from datetime import timezone
    duplicate_data['timestamp'] = datetime.now(timezone.utc).isoformat()
    
    # Create the duplicate session
    duplicated_session = session_repo.create(duplicate_data)
    
    return jsonify(duplicated_session), 201


@batches_bp.route('/test/cleanup/<user_id>', methods=['DELETE'])
def cleanup_test_user(user_id):
    """
    Delete test user data - for E2E test cleanup.
    
    Security: Only allows deletion of users starting with 'test_'
    """
    # Security check - only allow test users to be deleted
    if not user_id.startswith('test_'):
        return jsonify({'error': 'Can only delete test users (starting with test_)'}), 403
    
    try:
        factory = get_repository_factory()
        factory.delete_user(user_id)
        return jsonify({'message': f'Test user {user_id} cleaned up successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to cleanup test user: {str(e)}'}), 500


@batches_bp.route('/test/cleanup-all', methods=['DELETE'])
def cleanup_all_test_users():
    """
    Delete ALL test user data - for global E2E test cleanup.
    
    Useful for cleaning up after test suite interruptions or crashes.
    """
    try:
        factory = get_repository_factory()
        count = factory.cleanup_test_users()
        return jsonify({
            'message': f'Cleaned up {count} test users',
            'count': count
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to cleanup test users: {str(e)}'}), 500