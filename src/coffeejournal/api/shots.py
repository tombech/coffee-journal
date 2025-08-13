"""
API endpoints for espresso shot tracking.
"""

from flask import Blueprint, request, jsonify
from ..repositories.factory import get_repository_factory
from ..api.utils import (
    get_user_id_from_request, validate_user_id,
    check_required_fields, validate_score_fields,
    enrich_product_with_lookups, calculate_coffee_age,
    calculate_total_score
)
from datetime import datetime, timezone

shots_bp = Blueprint('shots', __name__, url_prefix='/shots')


def calculate_dose_yield_ratio(dose_grams, yield_grams):
    """Calculate dose to yield ratio for espresso shots."""
    if dose_grams and yield_grams:
        try:
            dose_float = float(dose_grams)
            yield_float = float(yield_grams)
            if dose_float > 0:
                ratio = yield_float / dose_float
                return round(ratio, 1)
        except (ValueError, TypeError, ZeroDivisionError):
            return None
    return None


def enrich_shot(shot, factory, user_id):
    """Enrich a shot with lookup data."""
    if not shot:
        return shot
    
    # Enrich product
    if shot.get('product_id'):
        product = factory.get_product_repository(user_id).find_by_id(shot['product_id'])
        if product:
            # Enrich product with its lookups
            product = enrich_product_with_lookups(product, factory, user_id)
            shot['product'] = product
            shot['product_name'] = product.get('product_name', 'Unknown')
    
    # Enrich batch
    if shot.get('product_batch_id'):
        batch = factory.get_batch_repository(user_id).find_by_id(shot['product_batch_id'])
        if batch:
            shot['batch'] = batch
            
            # Calculate coffee age from roast date to shot timestamp
            if batch.get('roast_date') and shot.get('timestamp'):
                shot['coffee_age'] = calculate_coffee_age(batch['roast_date'], shot['timestamp'])
            else:
                shot['coffee_age'] = None
    else:
        shot['coffee_age'] = None
    
    # Enrich brewer
    if shot.get('brewer_id'):
        brewer = factory.get_brewer_repository(user_id).find_by_id(shot['brewer_id'])
        if brewer:
            shot['brewer'] = brewer
            shot['brewer_name'] = brewer.get('name', 'Unknown')
    
    # Enrich grinder
    if shot.get('grinder_id'):
        grinder = factory.get_grinder_repository(user_id).find_by_id(shot['grinder_id'])
        if grinder:
            shot['grinder'] = grinder
            shot['grinder_name'] = grinder.get('name', 'Unknown')
    
    # Enrich portafilter
    if shot.get('portafilter_id'):
        portafilter = factory.get_portafilter_repository(user_id).find_by_id(shot['portafilter_id'])
        if portafilter:
            shot['portafilter'] = portafilter
            shot['portafilter_name'] = portafilter.get('name', 'Unknown')
    
    # Enrich basket
    if shot.get('basket_id'):
        basket = factory.get_basket_repository(user_id).find_by_id(shot['basket_id'])
        if basket:
            shot['basket'] = basket
            shot['basket_name'] = basket.get('name', 'Unknown')
    
    # Enrich tamper
    if shot.get('tamper_id'):
        tamper = factory.get_tamper_repository(user_id).find_by_id(shot['tamper_id'])
        if tamper:
            shot['tamper'] = tamper
            shot['tamper_name'] = tamper.get('name', 'Unknown')
    
    # Enrich scale
    if shot.get('scale_id'):
        scale = factory.get_scale_repository(user_id).find_by_id(shot['scale_id'])
        if scale:
            shot['scale'] = scale
            shot['scale_name'] = scale.get('name', 'Unknown')
    
    # Enrich recipe
    if shot.get('recipe_id'):
        recipe = factory.get_recipe_repository(user_id).find_by_id(shot['recipe_id'])
        if recipe:
            shot['recipe'] = recipe
            shot['recipe_name'] = recipe.get('name', 'Unknown')
    
    # Enrich shot session
    if shot.get('shot_session_id'):
        session = factory.get_shot_session_repository(user_id).find_by_id(shot['shot_session_id'])
        if session:
            shot['shot_session'] = session
            shot['shot_session_title'] = session.get('title', 'Unknown')
    
    # Calculate dose-yield ratio
    shot['dose_yield_ratio'] = calculate_dose_yield_ratio(shot.get('dose_grams'), shot.get('yield_grams'))
    
    # Calculate overall score
    shot['calculated_score'] = calculate_total_score(shot)
    
    return shot


@shots_bp.route('', methods=['GET'])
def get_all_shots():
    """Get all shots with optional filtering and pagination."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        shots = factory.get_shot_repository(user_id).find_all()
        
        # Apply filters
        product_id = request.args.get('product_id', type=int)
        batch_id = request.args.get('batch_id', type=int)
        session_id = request.args.get('shot_session_id', type=int)
        brewer_id = request.args.get('brewer_id', type=int)
        extraction_status = request.args.get('extraction_status')
        min_score = request.args.get('min_score', type=float)
        max_score = request.args.get('max_score', type=float)
        
        if product_id:
            shots = [s for s in shots if s.get('product_id') == product_id]
        if batch_id:
            shots = [s for s in shots if s.get('product_batch_id') == batch_id]
        if session_id:
            shots = [s for s in shots if s.get('shot_session_id') == session_id]
        if brewer_id:
            shots = [s for s in shots if s.get('brewer_id') == brewer_id]
        if extraction_status:
            shots = [s for s in shots if s.get('extraction_status') == extraction_status]
        if min_score is not None:
            shots = [s for s in shots if s.get('score', 0) >= min_score]
        if max_score is not None:
            shots = [s for s in shots if s.get('score', 0) <= max_score]
        
        # Sort by timestamp (newest first by default)
        sort = request.args.get('sort', 'timestamp')
        sort_direction = request.args.get('sort_direction', 'desc')
        reverse = sort_direction == 'desc'
        
        if sort == 'score':
            shots.sort(key=lambda x: x.get('score', 0), reverse=reverse)
        elif sort == 'dose_grams':
            shots.sort(key=lambda x: x.get('dose_grams', 0), reverse=reverse)
        elif sort == 'yield_grams':
            shots.sort(key=lambda x: x.get('yield_grams', 0), reverse=reverse)
        elif sort == 'brew_time_seconds':
            shots.sort(key=lambda x: x.get('brew_time_seconds', 0), reverse=reverse)
        else:  # timestamp
            shots.sort(key=lambda x: x.get('timestamp', ''), reverse=reverse)
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        total_count = len(shots)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_shots = shots[start_idx:end_idx]
        
        # Enrich with lookup data
        enriched_shots = [enrich_shot(shot, factory, user_id) for shot in paginated_shots]
        
        return jsonify({
            'data': enriched_shots,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size,
                'has_next': end_idx < total_count,
                'has_previous': page > 1
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@shots_bp.route('/<int:shot_id>', methods=['GET'])
def get_shot(shot_id):
    """Get a specific shot by ID."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        shot = factory.get_shot_repository(user_id).find_by_id(shot_id)
        
        if not shot:
            return jsonify({'error': 'Shot not found'}), 404
        
        # Enrich with lookup data
        shot = enrich_shot(shot, factory, user_id)
        
        return jsonify(shot)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@shots_bp.route('', methods=['POST'])
def create_shot():
    """Create a new shot."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['dose_grams', 'yield_grams']
        missing_fields = check_required_fields(data, required_fields)
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Validate score fields
        score_fields = ['sweetness', 'acidity', 'bitterness', 'body', 'aroma', 'crema', 'flavor_profile_match']
        for field in score_fields:
            if field in data and data[field] is not None:
                try:
                    score = int(data[field])
                    if score < 1 or score > 10:
                        return jsonify({'error': f'{field} must be between 1 and 10'}), 400
                    data[field] = score
                except (ValueError, TypeError):
                    return jsonify({'error': f'{field} must be an integer'}), 400
        
        # Validate extraction status if provided
        if 'extraction_status' in data and data['extraction_status']:
            valid_statuses = ['channeling', 'over-extracted', 'under-extracted', 'perfect']
            if data['extraction_status'] not in valid_statuses:
                return jsonify({'error': f'extraction_status must be one of: {", ".join(valid_statuses)}'}), 400
        
        # Convert ID fields to integers to ensure consistent data types
        id_fields = ['product_id', 'product_batch_id', 'brewer_id', 'shot_session_id', 
                     'grinder_id', 'portafilter_id', 'basket_id', 'tamper_id', 
                     'scale_id', 'recipe_id']
        for field in id_fields:
            if field in data and data[field] is not None:
                data[field] = int(data[field])
        
        # Create the shot
        factory = get_repository_factory()
        shot = factory.get_shot_repository(user_id).create(data)
        
        # Enrich with lookup data
        shot = enrich_shot(shot, factory, user_id)
        
        return jsonify(shot), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@shots_bp.route('/<int:shot_id>', methods=['PUT'])
def update_shot(shot_id):
    """Update an existing shot."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        
        # Validate score fields if present
        score_fields = ['sweetness', 'acidity', 'bitterness', 'body', 'aroma', 'crema', 'flavor_profile_match']
        for field in score_fields:
            if field in data and data[field] is not None:
                try:
                    score = int(data[field])
                    if score < 1 or score > 10:
                        return jsonify({'error': f'{field} must be between 1 and 10'}), 400
                    data[field] = score
                except (ValueError, TypeError):
                    return jsonify({'error': f'{field} must be an integer'}), 400
        
        # Validate extraction status if provided
        if 'extraction_status' in data and data['extraction_status']:
            valid_statuses = ['channeling', 'over-extracted', 'under-extracted', 'perfect']
            if data['extraction_status'] not in valid_statuses:
                return jsonify({'error': f'extraction_status must be one of: {", ".join(valid_statuses)}'}), 400
        
        # Convert ID fields to integers to ensure consistent data types
        id_fields = ['product_id', 'product_batch_id', 'brewer_id', 'shot_session_id', 
                     'grinder_id', 'portafilter_id', 'basket_id', 'tamper_id', 
                     'scale_id', 'recipe_id']
        for field in id_fields:
            if field in data and data[field] is not None:
                data[field] = int(data[field])
        
        # Update the shot
        factory = get_repository_factory()
        shot = factory.get_shot_repository(user_id).update(shot_id, data)
        
        if not shot:
            return jsonify({'error': 'Shot not found'}), 404
        
        # Enrich with lookup data
        shot = enrich_shot(shot, factory, user_id)
        
        return jsonify(shot)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@shots_bp.route('/<int:shot_id>', methods=['DELETE'])
def delete_shot(shot_id):
    """Delete a shot."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        
        if factory.get_shot_repository(user_id).delete(shot_id):
            return '', 204
        
        return jsonify({'error': 'Shot not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@shots_bp.route('/<int:shot_id>/remove_from_session', methods=['POST'])
def remove_shot_from_session(shot_id):
    """Remove a shot from its session."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        shot = factory.get_shot_repository(user_id).remove_from_session(shot_id)
        
        if not shot:
            return jsonify({'error': 'Shot not found'}), 404
        
        # Enrich with lookup data
        shot = enrich_shot(shot, factory, user_id)
        
        return jsonify(shot)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@shots_bp.route('/filter_options', methods=['GET'])
def get_shot_filter_options():
    """Get all unique values for shot filters."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        shots = factory.get_shot_repository(user_id).find_all()
        
        # Collect unique values for each filterable field
        products = set()
        batches = set()
        brewers = set()
        grinders = set()
        portafilters = set()
        baskets = set()
        tampers = set()
        extraction_statuses = set()
        
        for shot in shots:
            if shot.get('product_id'):
                product = factory.get_product_repository(user_id).find_by_id(shot['product_id'])
                if product:
                    products.add((product['id'], product.get('product_name', 'Unknown')))
            
            if shot.get('product_batch_id'):
                batch = factory.get_batch_repository(user_id).find_by_id(shot['product_batch_id'])
                if batch:
                    batches.add((batch['id'], f"Batch {batch['id']} - {batch.get('roast_date', 'Unknown')}"))
            
            if shot.get('brewer_id'):
                brewer = factory.get_brewer_repository(user_id).find_by_id(shot['brewer_id'])
                if brewer:
                    brewers.add((brewer['id'], brewer.get('name', 'Unknown')))
            
            if shot.get('grinder_id'):
                grinder = factory.get_grinder_repository(user_id).find_by_id(shot['grinder_id'])
                if grinder:
                    grinders.add((grinder['id'], grinder.get('name', 'Unknown')))
            
            if shot.get('portafilter_id'):
                portafilter = factory.get_portafilter_repository(user_id).find_by_id(shot['portafilter_id'])
                if portafilter:
                    portafilters.add((portafilter['id'], portafilter.get('name', 'Unknown')))
            
            if shot.get('basket_id'):
                basket = factory.get_basket_repository(user_id).find_by_id(shot['basket_id'])
                if basket:
                    baskets.add((basket['id'], basket.get('name', 'Unknown')))
            
            if shot.get('tamper_id'):
                tamper = factory.get_tamper_repository(user_id).find_by_id(shot['tamper_id'])
                if tamper:
                    tampers.add((tamper['id'], tamper.get('name', 'Unknown')))
            
            if shot.get('extraction_status'):
                extraction_statuses.add(shot['extraction_status'])
        
        # Format for response
        filter_options = {
            'products': [{'id': id, 'name': name} for id, name in sorted(products, key=lambda x: x[1])],
            'batches': [{'id': id, 'name': name} for id, name in sorted(batches, key=lambda x: x[0])],
            'brewers': [{'id': id, 'name': name} for id, name in sorted(brewers, key=lambda x: x[1])],
            'grinders': [{'id': id, 'name': name} for id, name in sorted(grinders, key=lambda x: x[1])],
            'portafilters': [{'id': id, 'name': name} for id, name in sorted(portafilters, key=lambda x: x[1])],
            'baskets': [{'id': id, 'name': name} for id, name in sorted(baskets, key=lambda x: x[1])],
            'tampers': [{'id': id, 'name': name} for id, name in sorted(tampers, key=lambda x: x[1])],
            'extraction_statuses': sorted(list(extraction_statuses))
        }
        
        return jsonify(filter_options)
    except Exception as e:
        return jsonify({'error': str(e)}), 500