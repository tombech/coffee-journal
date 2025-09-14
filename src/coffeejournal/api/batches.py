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
    calculate_total_score,
    calculate_coffee_age,
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
    
    # Update batch - only include fields that are provided in the request
    batch_data = {}
    
    # Always include product_id for updates
    batch_data['product_id'] = product_id
    
    # Only include fields that are explicitly provided in the request
    if 'roast_date' in data:
        roast_date = data['roast_date']
        if roast_date == '':  # Handle empty string
            roast_date = datetime.now().strftime('%Y-%m-%d')  # Default to today
        batch_data['roast_date'] = roast_date
    if 'purchase_date' in data:
        purchase_date = data['purchase_date']
        if purchase_date == '':  # Handle empty string
            purchase_date = None
        batch_data['purchase_date'] = purchase_date
    if 'amount_grams' in data:
        batch_data['amount_grams'] = safe_float(data['amount_grams'])
    if 'price' in data:
        batch_data['price'] = safe_float(data['price'])
    if 'seller' in data:
        batch_data['seller'] = data['seller']
    if 'notes' in data:
        batch_data['notes'] = data['notes']
    if 'rating' in data:
        batch_data['rating'] = safe_int(data['rating'])
    if 'is_active' in data:
        batch_data['is_active'] = data['is_active']
    
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
        brewer_repo = factory.get_brewer_repository(user_id)
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
            
            # Add brew method, recipe, brewer, grinder, filter, kettle, and scale objects
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
            
            if session.get('brewer_id'):
                brewer = brewer_repo.find_by_id(session['brewer_id'])
                session['brewer'] = brewer if brewer else None
            else:
                session['brewer'] = None
            
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
        
        # Get or create brew method, recipe, brewer, grinder, filter, kettle, and scale
        brew_method_repo = factory.get_brew_method_repository(user_id)
        recipe_repo = factory.get_recipe_repository(user_id)
        brewer_repo = factory.get_brewer_repository(user_id)
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
        
        brewer = None
        if data.get('brewer'):
            brewer = brewer_repo.get_or_create_by_identifier(data['brewer'])
        
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
        
        # Use safe conversion for tasting scores and overall score
        sweetness = safe_float(data.get('sweetness'))
        acidity = safe_float(data.get('acidity'))
        bitterness = safe_float(data.get('bitterness'))
        body = safe_float(data.get('body'))
        aroma = safe_float(data.get('aroma'))
        flavor_profile_match = safe_float(data.get('flavor_profile_match'))
        
        session_data = {
            'timestamp': data.get('timestamp', datetime.utcnow().isoformat()),
            'product_batch_id': batch_id,  # Use batch_id from URL
            'product_id': batch.get('product_id'),  # Get product_id from batch
            'recipe_id': recipe['id'] if recipe else data.get('recipe_id'),
            'brew_method_id': brew_method['id'] if brew_method else data.get('brew_method_id'),
            'brewer_id': brewer['id'] if brewer else data.get('brewer_id'),
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
        
        # Add brew method, recipe, brewer, grinder, filter, kettle, and scale objects
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
        
        if brewer:
            session['brewer'] = brewer
        elif session.get('brewer_id'):
            brew = brewer_repo.find_by_id(session['brewer_id'])
            session['brewer'] = brew if brew else None
        else:
            session['brewer'] = None
        
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
    """Get all brew sessions from all batches with pagination support."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 30, type=int)
    
    # Get sorting parameters
    sort = request.args.get('sort', 'timestamp')  # Default: newest first
    sort_direction = request.args.get('sort_direction', 'desc')
    
    # Get filtering parameters (now using IDs instead of names)
    product_id = request.args.get('product_id', type=int)
    batch_id = request.args.get('batch_id', type=int)
    brew_method_id = request.args.get('brew_method', type=int)
    recipe_id = request.args.get('recipe', type=int)
    roaster_id = request.args.get('roaster', type=int)
    bean_type_id = request.args.get('bean_type', type=int)
    country_id = request.args.get('country', type=int)
    region_id = request.args.get('region', type=int)
    decaf_method_id = request.args.get('decaf_method', type=int)
    grinder_id = request.args.get('grinder', type=int)
    filter_id = request.args.get('filter', type=int)
    kettle_id = request.args.get('kettle', type=int)
    scale_id = request.args.get('scale', type=int)
    min_score = request.args.get('min_score', type=float)
    max_score = request.args.get('max_score', type=float)
    
    # Validate pagination parameters
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:  # Limit max page size to prevent performance issues
        page_size = 30
    
    # Validate sorting parameters
    valid_sort_fields = [
        'timestamp', 'amount_coffee_grams', 'amount_water_grams', 'brew_temperature_c',
        'bloom_time_seconds', 'brew_time_seconds', 'score', 'sweetness', 'acidity', 
        'bitterness', 'body', 'aroma', 'flavor_profile_match', 'product_name', 
        'brew_method', 'recipe', 'grinder', 'filter', 'brew_ratio'
    ]
    if sort not in valid_sort_fields:
        sort = 'timestamp'
    
    if sort_direction not in ['asc', 'desc']:
        sort_direction = 'desc'
    
    factory = get_repository_factory()
    all_sessions = factory.get_brew_session_repository(user_id).find_all()
    
    # Pre-load all lookup data into dictionaries for O(1) lookups
    product_repo = factory.get_product_repository(user_id)
    batch_repo = factory.get_batch_repository(user_id)
    brew_method_repo = factory.get_brew_method_repository(user_id)
    recipe_repo = factory.get_recipe_repository(user_id)
    brewer_repo = factory.get_brewer_repository(user_id)
    grinder_repo = factory.get_grinder_repository(user_id)
    filter_repo = factory.get_filter_repository(user_id)
    kettle_repo = factory.get_kettle_repository(user_id)
    scale_repo = factory.get_scale_repository(user_id)
    
    # Load all data once and create lookup dictionaries
    all_products = {p['id']: p for p in product_repo.find_all()}
    all_batches = {b['id']: b for b in batch_repo.find_all()}
    all_brew_methods = {m['id']: m for m in brew_method_repo.find_all()}
    all_recipes = {r['id']: r for r in recipe_repo.find_all()}
    all_brewers = {b['id']: b for b in brewer_repo.find_all()}
    all_grinders = {g['id']: g for g in grinder_repo.find_all()}
    all_filters = {f['id']: f for f in filter_repo.find_all()}
    all_kettles = {k['id']: k for k in kettle_repo.find_all()}
    all_scales = {s['id']: s for s in scale_repo.find_all()}
    
    # Also pre-load product lookups for enrichment
    roaster_repo = factory.get_roaster_repository(user_id)
    bean_type_repo = factory.get_bean_type_repository(user_id)
    country_repo = factory.get_country_repository(user_id)
    region_repo = factory.get_region_repository(user_id)
    decaf_method_repo = factory.get_decaf_method_repository(user_id)
    
    all_roasters = {r['id']: r for r in roaster_repo.find_all()}
    all_bean_types = {bt['id']: bt for bt in bean_type_repo.find_all()}
    all_countries = {c['id']: c for c in country_repo.find_all()}
    all_regions = {r['id']: r for r in region_repo.find_all()}
    all_decaf_methods = {dm['id']: dm for dm in decaf_method_repo.find_all()}
    
    for session in all_sessions:
        # Get product and batch info for enrichment using pre-loaded dictionaries
        product = all_products.get(session.get('product_id'))
        batch = all_batches.get(session.get('product_batch_id'))
        
        if product:
            # Inline optimized product enrichment using pre-loaded lookups
            enriched_product = product.copy()
            
            # Enrich roaster
            enriched_product['roaster'] = all_roasters.get(product.get('roaster_id'))
            
            # Enrich bean types
            bean_type_ids = product.get('bean_type_id', [])
            if isinstance(bean_type_ids, int):
                bean_type_ids = [bean_type_ids]
            enriched_product['bean_type'] = [all_bean_types.get(bt_id) for bt_id in bean_type_ids if bt_id in all_bean_types]
            
            # Enrich country
            enriched_product['country'] = all_countries.get(product.get('country_id'))
            
            # Enrich regions
            region_ids = product.get('region_id', [])
            if isinstance(region_ids, int):
                region_ids = [region_ids]
            enriched_product['region'] = [all_regions.get(r_id) for r_id in region_ids if r_id in all_regions]
            
            # Enrich decaf method
            enriched_product['decaf_method'] = all_decaf_methods.get(product.get('decaf_method_id'))
            
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
                'decaf': enriched_product.get('decaf', False),
                'decaf_method': enriched_product.get('decaf_method'),
                'country': enriched_product.get('country'),
                'region': enriched_product.get('region')
            }
        else:
            session['product_name'] = 'N/A'
            session['product_details'] = {}
        
        # Enrich equipment lookups using pre-loaded dictionaries
        session['brew_method'] = all_brew_methods.get(session.get('brew_method_id'))
        session['recipe'] = all_recipes.get(session.get('recipe_id'))
        session['brewer'] = all_brewers.get(session.get('brewer_id'))
        session['grinder'] = all_grinders.get(session.get('grinder_id'))
        session['filter'] = all_filters.get(session.get('filter_id'))
        session['kettle'] = all_kettles.get(session.get('kettle_id'))
        session['scale'] = all_scales.get(session.get('scale_id'))
        
        # Add calculated score
        session['calculated_score'] = calculate_total_score(session)
        
        # Calculate brew ratio using consistent field names
        session['brew_ratio'] = calculate_brew_ratio(session.get('amount_coffee_grams'), session.get('amount_water_grams'))
        
        # Calculate coffee age from roast date to brew date
        if batch and batch.get('roast_date') and session.get('timestamp'):
            session['coffee_age'] = calculate_coffee_age(batch['roast_date'], session['timestamp'])
        else:
            session['coffee_age'] = None
    
    # Apply filters to enriched sessions
    filtered_sessions = []
    for session in all_sessions:
        # Direct field filters
        if product_id and session.get('product_id') != product_id:
            continue
        if batch_id and session.get('product_batch_id') != batch_id:
            continue
        
        # Score range filters (use calculated score from enrichment)
        if min_score is not None:
            score = session.get('calculated_score') or 0
            if score < min_score:
                continue
        if max_score is not None:
            score = session.get('calculated_score') or 0
            if score > max_score:
                continue
        
        # Brew method filter (by ID)
        if brew_method_id:
            if session.get('brew_method_id') != brew_method_id:
                continue
        
        # Recipe filter (by ID)
        if recipe_id:
            if session.get('recipe_id') != recipe_id:
                continue
        
        # Equipment filters (by ID)
        if grinder_id and session.get('grinder_id') != grinder_id:
            continue
        if filter_id and session.get('filter_id') != filter_id:
            continue
        if kettle_id and session.get('kettle_id') != kettle_id:
            continue
        if scale_id and session.get('scale_id') != scale_id:
            continue
        
        # Product detail filters (by ID)
        if roaster_id or bean_type_id or country_id or region_id or decaf_method_id:
            product_details = session.get('product_details', {})
            
            # Roaster filter (by ID)
            if roaster_id:
                roaster = product_details.get('roaster')
                if not roaster or roaster.get('id') != roaster_id:
                    continue
            
            # Bean type filter (by ID) - check if any bean type matches
            if bean_type_id:
                bean_types = product_details.get('bean_type', [])
                found = False
                for bt in bean_types:
                    if bt.get('id') == bean_type_id:
                        found = True
                        break
                if not found:
                    continue
            
            # Country filter (by ID)
            if country_id:
                country = product_details.get('country')
                if not country or country.get('id') != country_id:
                    continue
            
            # Region filter (by ID) - check if any region matches
            if region_id:
                regions = product_details.get('region', [])
                found = False
                for region in regions:
                    if region.get('id') == region_id:
                        found = True
                        break
                if not found:
                    continue
            
            # Decaf method filter (by ID)
            if decaf_method_id:
                decaf_method = product_details.get('decaf_method')
                if not decaf_method or decaf_method.get('id') != decaf_method_id:
                    continue
        
        # Decaf filter (still using request parameter directly)
        decaf_filter = request.args.get('decaf')
        if decaf_filter is not None:
            is_decaf = session.get('product_details', {}).get('decaf', False)
            filter_decaf = decaf_filter.lower() in ['true', '1', 'yes']
            if is_decaf != filter_decaf:
                continue
        
        # Date range filters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        if date_from or date_to:
            session_date = session.get('timestamp', '')[:10]  # Get date part only
            if date_from and session_date < date_from:
                continue
            if date_to and session_date > date_to:
                continue
        
        # If we got here, the session passes all filters
        filtered_sessions.append(session)
    
    # Use filtered sessions for sorting and pagination
    all_sessions = filtered_sessions
    
    # Server-side sorting on enriched data
    def get_sort_value(session, sort_field):
        """Get the value to sort by from enriched session data."""
        if sort_field == 'timestamp':
            return session.get('timestamp', '')
        elif sort_field == 'product_name':
            return session.get('product_name', '').lower()
        elif sort_field == 'brew_method':
            method = session.get('brew_method')
            return method.get('name', '').lower() if method else ''
        elif sort_field == 'recipe':
            recipe = session.get('recipe')
            return recipe.get('name', '').lower() if recipe else ''
        elif sort_field == 'grinder':
            grinder = session.get('grinder')
            return grinder.get('name', '').lower() if grinder else ''
        elif sort_field == 'filter':
            filter_obj = session.get('filter')
            return filter_obj.get('name', '').lower() if filter_obj else ''
        elif sort_field == 'brew_ratio':
            return session.get('brew_ratio', 0)
        elif sort_field == 'score':
            # Use the calculated score from centralized enrichment
            return session.get('calculated_score') or 0
        else:
            # For all other numeric fields
            value = session.get(sort_field)
            return value if value is not None else 0
    
    # Sort enriched sessions
    reverse_sort = sort_direction == 'desc'
    sorted_sessions = sorted(all_sessions, key=lambda x: get_sort_value(x, sort), reverse=reverse_sort)
    
    # Calculate pagination
    total_count = len(sorted_sessions)
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    sessions = sorted_sessions[start_index:end_index]
    
    # Build pagination metadata
    pagination = {
        'page': page,
        'page_size': page_size,
        'total_count': total_count,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_previous': page > 1,
        'next_page': page + 1 if page < total_pages else None,
        'previous_page': page - 1 if page > 1 else None
    }
    
    # Sessions are already enriched and sorted, just return the paginated results
    
    return jsonify({
        'data': sessions,
        'pagination': pagination
    })


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
    
    # Calculate coffee age from roast date to brew date
    if batch and batch.get('roast_date') and session.get('timestamp'):
        session['coffee_age'] = calculate_coffee_age(batch['roast_date'], session['timestamp'])
    else:
        session['coffee_age'] = None
    
    if product:
        # Use consistent product enrichment
        enriched_product = enrich_product_with_lookups(product.copy(), factory, user_id)
        session['product_details'] = {
            'roaster': enriched_product.get('roaster'),
            'bean_type': enriched_product.get('bean_type'),
            'product_name': enriched_product.get('product_name'),
            'roast_date': batch.get('roast_date') if batch else None,
            'roast_type': enriched_product.get('roast_type'),
            'decaf': enriched_product.get('decaf', False),
            'country': enriched_product.get('country'),
            'region': enriched_product.get('region')
        }
    else:
        session['product_details'] = {}
    
    # Add brew method, recipe, brewer, grinder, filter, kettle, and scale objects
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
    
    if session.get('brewer_id'):
        brewer_repo = factory.get_brewer_repository(user_id)
        brewer = brewer_repo.find_by_id(session['brewer_id'])
        session['brewer'] = brewer if brewer else None
    else:
        session['brewer'] = None
    
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
    
    # Get or create brew method, recipe, brewer, grinder, filter, kettle, and scale
    brew_method_repo = factory.get_brew_method_repository(user_id)
    recipe_repo = factory.get_recipe_repository(user_id)
    brewer_repo = factory.get_brewer_repository(user_id)
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
    
    brewer = None
    if data.get('brewer'):
        brewer = brewer_repo.get_or_create_by_identifier(data['brewer'])
    
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
        'brewer_id': brewer['id'] if brewer else existing_session.get('brewer_id'),
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
    
    # Get smart defaults for each equipment type and products
    defaults = {
        'brew_method': None,
        'recipe': None,
        'grinder': None,
        'filter': None,
        'kettle': None,
        'scale': None,
        'product': None
    }
    
    # Get smart default for each lookup type
    brew_method_repo = factory.get_brew_method_repository(user_id)
    recipe_repo = factory.get_recipe_repository(user_id)
    grinder_repo = factory.get_grinder_repository(user_id)
    filter_repo = factory.get_filter_repository(user_id)
    kettle_repo = factory.get_kettle_repository(user_id)
    scale_repo = factory.get_scale_repository(user_id)
    product_repo = factory.get_product_repository(user_id)
    
    # Fetch smart defaults
    brew_method_default = brew_method_repo.get_smart_default(factory, user_id)
    if brew_method_default:
        defaults['brew_method'] = brew_method_default
    
    recipe_default = recipe_repo.get_smart_default(factory, user_id)
    if recipe_default:
        defaults['recipe'] = recipe_default
    
    grinder_default = grinder_repo.get_smart_default(factory, user_id)
    if grinder_default:
        defaults['grinder'] = grinder_default
    
    filter_default = filter_repo.get_smart_default(factory, user_id)
    if filter_default:
        defaults['filter'] = filter_default
    
    kettle_default = kettle_repo.get_smart_default(factory, user_id)
    if kettle_default:
        defaults['kettle'] = kettle_default
    
    scale_default = scale_repo.get_smart_default(factory, user_id)
    if scale_default:
        defaults['scale'] = scale_default
    
    product_default = product_repo.get_smart_default(factory, user_id)
    if product_default:
        defaults['product'] = product_default
    
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


@batches_bp.route('/brew_sessions/filter_options', methods=['GET'])
def get_brew_session_filter_options():
    """
    Get all available filter options for brew sessions based on the complete dataset.
    
    This endpoint returns all possible values for filter dropdowns, not limited by current
    pagination or filtering, to prevent the feedback loop where filtering reduces available options.
    """
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    
    # Get ALL brew sessions (no filtering, pagination, or limits)
    all_sessions = factory.get_brew_session_repository(user_id).find_all()
    
    # Initialize sets to collect unique values (store objects with id and name)
    roasters = set()
    bean_types = set()
    countries = set()
    brew_methods = set()
    recipes = set()
    grinders = set()
    filters_equipment = set()
    kettles = set()
    scales = set()
    
    # Get repository instances for enrichment
    product_repo = factory.get_product_repository(user_id)
    brew_method_repo = factory.get_brew_method_repository(user_id)
    recipe_repo = factory.get_recipe_repository(user_id)
    grinder_repo = factory.get_grinder_repository(user_id)
    filter_repo = factory.get_filter_repository(user_id)
    kettle_repo = factory.get_kettle_repository(user_id)
    scale_repo = factory.get_scale_repository(user_id)
    
    # Process each session to extract filter options
    for session in all_sessions:
        # Get product for roaster, bean type, country, region info
        product = product_repo.find_by_id(session.get('product_id'))
        if product:
            # Enrich product with lookup data
            enriched_product = enrich_product_with_lookups(product.copy(), factory, user_id)
            
            # Extract roaster (store as JSON string for set uniqueness)
            roaster = enriched_product.get('roaster')
            if roaster and roaster.get('id') and roaster.get('name'):
                roasters.add(f"{roaster['id']}|{roaster['name']}")
            
            # Extract bean types (store as JSON string for set uniqueness)
            bean_type_list = enriched_product.get('bean_type', [])
            if isinstance(bean_type_list, list):
                for bt in bean_type_list:
                    if bt and bt.get('id') and bt.get('name'):
                        bean_types.add(f"{bt['id']}|{bt['name']}")
            
            # Extract country (store as JSON string for set uniqueness)
            country = enriched_product.get('country')
            if country and country.get('id') and country.get('name'):
                countries.add(f"{country['id']}|{country['name']}")
        
        # Extract brew method (store as JSON string for set uniqueness)
        if session.get('brew_method_id'):
            method = brew_method_repo.find_by_id(session['brew_method_id'])
            if method and method.get('id') and method.get('name'):
                brew_methods.add(f"{method['id']}|{method['name']}")
        
        # Extract recipe (store as JSON string for set uniqueness)
        if session.get('recipe_id'):
            recipe = recipe_repo.find_by_id(session['recipe_id'])
            if recipe and recipe.get('id') and recipe.get('name'):
                recipes.add(f"{recipe['id']}|{recipe['name']}")
        
        # Extract grinder (store as JSON string for set uniqueness)
        if session.get('grinder_id'):
            grinder = grinder_repo.find_by_id(session['grinder_id'])
            if grinder and grinder.get('id') and grinder.get('name'):
                grinders.add(f"{grinder['id']}|{grinder['name']}")
        
        # Extract filter (store as JSON string for set uniqueness)
        if session.get('filter_id'):
            filter_item = filter_repo.find_by_id(session['filter_id'])
            if filter_item and filter_item.get('id') and filter_item.get('name'):
                filters_equipment.add(f"{filter_item['id']}|{filter_item['name']}")
        
        # Extract kettle (store as JSON string for set uniqueness)
        if session.get('kettle_id'):
            kettle = kettle_repo.find_by_id(session['kettle_id'])
            if kettle and kettle.get('id') and kettle.get('name'):
                kettles.add(f"{kettle['id']}|{kettle['name']}")
        
        # Extract scale (store as JSON string for set uniqueness)
        if session.get('scale_id'):
            scale = scale_repo.find_by_id(session['scale_id'])
            if scale and scale.get('id') and scale.get('name'):
                scales.add(f"{scale['id']}|{scale['name']}")
    
    # Helper function to convert "id|name" strings to objects
    def parse_id_name_pairs(pairs_set):
        result = []
        for pair in sorted(pairs_set):
            if '|' in pair:
                id_str, name = pair.split('|', 1)
                try:
                    result.append({'id': int(id_str), 'name': name})
                except ValueError:
                    # Skip invalid entries
                    continue
        return result
    
    # Convert sets to sorted lists of objects with id and name
    return jsonify({
        'roasters': parse_id_name_pairs(roasters),
        'bean_types': parse_id_name_pairs(bean_types),
        'countries': parse_id_name_pairs(countries),
        'brew_methods': parse_id_name_pairs(brew_methods),
        'recipes': parse_id_name_pairs(recipes),
        'grinders': parse_id_name_pairs(grinders),
        'filters': parse_id_name_pairs(filters_equipment),
        'kettles': parse_id_name_pairs(kettles),
        'scales': parse_id_name_pairs(scales),
        'decaf_options': [
            {'id': 'true', 'name': 'Yes'}, 
            {'id': 'false', 'name': 'No'}
        ]  # Static options with consistent format
    })