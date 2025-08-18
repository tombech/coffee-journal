"""
API endpoints for shot session management (grouping shots for dialing-in workflows).
"""

from flask import Blueprint, request, jsonify
from ..repositories.factory import get_repository_factory
from ..api.utils import get_user_id_from_request, validate_user_id, check_required_fields, calculate_coffee_age
from datetime import datetime, timezone

shot_sessions_bp = Blueprint('shot_sessions', __name__, url_prefix='/shot_sessions')


def enrich_shot_session_with_shots(session, factory, user_id):
    """Enrich a shot session with its associated shots."""
    if not session:
        return session
    
    # Get all shots for this session
    shots = factory.get_shot_repository(user_id).find_by_session(session['id'])
    
    # Sort shots by timestamp for consistent ordering
    shots.sort(key=lambda x: x.get('timestamp', ''))
    
    # Basic enrichment for shots (simplified to avoid circular dependencies)
    for i, shot in enumerate(shots):
        # Add session-relative shot number (1-based)
        shot['session_shot_number'] = i + 1
        
        # Calculate time since previous shot
        if i > 0:
            previous_shot = shots[i-1]
            if shot.get('timestamp') and previous_shot.get('timestamp'):
                try:
                    from dateutil.parser import parse as parse_datetime
                    current_time = parse_datetime(shot['timestamp'])
                    previous_time = parse_datetime(previous_shot['timestamp'])
                    time_diff = current_time - previous_time
                    
                    # Format time difference
                    total_seconds = int(time_diff.total_seconds())
                    if total_seconds < 60:
                        shot['time_since_previous'] = f'{total_seconds}s'
                    elif total_seconds < 3600:
                        minutes = total_seconds // 60
                        seconds = total_seconds % 60
                        if seconds > 0:
                            shot['time_since_previous'] = f'{minutes}m {seconds}s'
                        else:
                            shot['time_since_previous'] = f'{minutes}m'
                    elif total_seconds < 86400:
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        if minutes > 0:
                            shot['time_since_previous'] = f'{hours}h {minutes}m'
                        else:
                            shot['time_since_previous'] = f'{hours}h'
                    else:
                        days = total_seconds // 86400
                        hours = (total_seconds % 86400) // 3600
                        if hours > 0:
                            shot['time_since_previous'] = f'{days}d {hours}h'
                        else:
                            shot['time_since_previous'] = f'{days}d'
                except:
                    shot['time_since_previous'] = None
            else:
                shot['time_since_previous'] = None
        else:
            shot['time_since_previous'] = 'first'
        
        # Add product name
        if shot.get('product_id'):
            product = factory.get_product_repository(user_id).find_by_id(shot['product_id'])
            if product:
                shot['product_name'] = product.get('product_name', 'Unknown')
        
        # Add brewer name
        if shot.get('brewer_id'):
            brewer = factory.get_brewer_repository(user_id).find_by_id(shot['brewer_id'])
            if brewer:
                shot['brewer_name'] = brewer.get('name', 'Unknown')
    
    session['shots'] = shots
    session['shot_count'] = len(shots)
    
    # Add session-level product and brewer information
    if session.get('product_id'):
        product = factory.get_product_repository(user_id).find_by_id(session['product_id'])
        if product:
            session['product'] = {
                'id': product['id'],
                'product_name': product.get('product_name', 'Unknown')
            }
    
    if session.get('product_batch_id'):
        batch = factory.get_batch_repository(user_id).find_by_id(session['product_batch_id'])
        if batch:
            session['product_batch'] = {
                'id': batch['id'],
                'roast_date': batch.get('roast_date', 'Unknown')
            }
            
            # Calculate coffee age from roast date to session creation date
            if batch.get('roast_date') and session.get('created_at'):
                session['coffee_age'] = calculate_coffee_age(batch['roast_date'], session['created_at'])
            else:
                session['coffee_age'] = None
    else:
        session['coffee_age'] = None
    
    if session.get('brewer_id'):
        brewer = factory.get_brewer_repository(user_id).find_by_id(session['brewer_id'])
        if brewer:
            session['brewer'] = {
                'id': brewer['id'],
                'name': brewer.get('name', 'Unknown')
            }
    
    # Calculate aggregate statistics
    if shots:
        scores = [s.get('score', 0) for s in shots if s.get('score')]
        if scores:
            session['avg_score'] = round(sum(scores) / len(scores), 2)
            session['min_score'] = min(scores)
            session['max_score'] = max(scores)
        
        doses = [s.get('dose_grams', 0) for s in shots if s.get('dose_grams')]
        if doses:
            session['avg_dose'] = round(sum(doses) / len(doses), 1)
        
        yields = [s.get('yield_grams', 0) for s in shots if s.get('yield_grams')]
        if yields:
            session['avg_yield'] = round(sum(yields) / len(yields), 1)
        
        # Count extraction statuses
        status_counts = {}
        for shot in shots:
            status = shot.get('extraction_status')
            if status:
                status_counts[status] = status_counts.get(status, 0) + 1
        session['extraction_status_counts'] = status_counts
    
    return session


@shot_sessions_bp.route('', methods=['GET'])
def get_all_shot_sessions():
    """Get all shot sessions with optional pagination."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        sessions = factory.get_shot_session_repository(user_id).find_all()
        
        # Apply filters
        if request.args.get('title'):
            title_filter = request.args.get('title').lower()
            sessions = [s for s in sessions if title_filter in s.get('title', '').lower()]
        
        if request.args.get('product_id'):
            product_id = int(request.args.get('product_id'))
            sessions = [s for s in sessions if s.get('product_id') == product_id]
        
        if request.args.get('product_batch_id'):
            batch_id = int(request.args.get('product_batch_id'))
            sessions = [s for s in sessions if s.get('product_batch_id') == batch_id]
        
        if request.args.get('brewer_id'):
            brewer_id = int(request.args.get('brewer_id'))
            sessions = [s for s in sessions if s.get('brewer_id') == brewer_id]
        
        if request.args.get('min_shots'):
            min_shots = int(request.args.get('min_shots'))
            # We need to check shot count, so let's filter after we get shot count
            temp_sessions = []
            for session in sessions:
                shots = factory.get_shot_repository(user_id).find_by_session(session['id'])
                if len(shots) >= min_shots:
                    temp_sessions.append(session)
            sessions = temp_sessions
        
        if request.args.get('max_shots'):
            max_shots = int(request.args.get('max_shots'))
            # We need to check shot count, so let's filter after we get shot count
            temp_sessions = []
            for session in sessions:
                shots = factory.get_shot_repository(user_id).find_by_session(session['id'])
                if len(shots) <= max_shots:
                    temp_sessions.append(session)
            sessions = temp_sessions
        
        # Sort by created_at (newest first by default)
        sort = request.args.get('sort', 'created_at')
        sort_direction = request.args.get('sort_direction', 'desc')
        reverse = sort_direction == 'desc'
        
        sessions.sort(key=lambda x: x.get(sort, ''), reverse=reverse)
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        include_shots = request.args.get('include_shots', 'true').lower() == 'true'
        
        total_count = len(sessions)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_sessions = sessions[start_idx:end_idx]
        
        # Optionally enrich with shots
        if include_shots:
            enriched_sessions = [enrich_shot_session_with_shots(session, factory, user_id) 
                               for session in paginated_sessions]
        else:
            # Just add shot count and basic enrichment without fetching all shots
            enriched_sessions = []
            for session in paginated_sessions:
                # Count shots
                shots = factory.get_shot_repository(user_id).find_by_session(session['id'])
                session['shot_count'] = len(shots)
                
                # Add product information
                if session.get('product_id'):
                    product = factory.get_product_repository(user_id).find_by_id(session['product_id'])
                    if product:
                        session['product'] = {
                            'id': product['id'],
                            'product_name': product.get('product_name', 'Unknown')
                        }
                
                # Add batch information
                if session.get('product_batch_id'):
                    batch = factory.get_batch_repository(user_id).find_by_id(session['product_batch_id'])
                    if batch:
                        session['product_batch'] = {
                            'id': batch['id'],
                            'roast_date': batch.get('roast_date', 'Unknown')
                        }
                        
                        # Calculate coffee age from roast date to session creation date
                        if batch.get('roast_date') and session.get('created_at'):
                            session['coffee_age'] = calculate_coffee_age(batch['roast_date'], session['created_at'])
                        else:
                            session['coffee_age'] = None
                    else:
                        session['coffee_age'] = None
                else:
                    session['coffee_age'] = None
                
                # Add brewer information  
                if session.get('brewer_id'):
                    brewer = factory.get_brewer_repository(user_id).find_by_id(session['brewer_id'])
                    if brewer:
                        session['brewer'] = {
                            'id': brewer['id'],
                            'name': brewer.get('name', 'Unknown')
                        }
                
                enriched_sessions.append(session)
        
        return jsonify({
            'data': enriched_sessions,
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


@shot_sessions_bp.route('/<int:session_id>', methods=['GET'])
def get_shot_session(session_id):
    """Get a specific shot session by ID."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        session = factory.get_shot_session_repository(user_id).find_by_id(session_id)
        
        if not session:
            return jsonify({'error': 'Shot session not found'}), 404
        
        # Enrich with shots
        session = enrich_shot_session_with_shots(session, factory, user_id)
        
        return jsonify(session)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@shot_sessions_bp.route('', methods=['POST'])
def create_shot_session():
    """Create a new shot session."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'product_id', 'product_batch_id', 'brewer_id']
        missing_fields = check_required_fields(data, required_fields)
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Convert ID fields to integers to ensure consistent data types
        if 'product_id' in data and data['product_id'] is not None:
            data['product_id'] = int(data['product_id'])
        if 'product_batch_id' in data and data['product_batch_id'] is not None:
            data['product_batch_id'] = int(data['product_batch_id'])
        if 'brewer_id' in data and data['brewer_id'] is not None:
            data['brewer_id'] = int(data['brewer_id'])
        
        # Create the session
        factory = get_repository_factory()
        session = factory.get_shot_session_repository(user_id).create(data)
        
        # Initialize with empty shots list
        session['shots'] = []
        session['shot_count'] = 0
        
        return jsonify(session), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@shot_sessions_bp.route('/<int:session_id>', methods=['PUT'])
def update_shot_session(session_id):
    """Update an existing shot session."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        
        # Convert ID fields to integers to ensure consistent data types
        if 'product_id' in data and data['product_id'] is not None:
            data['product_id'] = int(data['product_id'])
        if 'product_batch_id' in data and data['product_batch_id'] is not None:
            data['product_batch_id'] = int(data['product_batch_id'])
        if 'brewer_id' in data and data['brewer_id'] is not None:
            data['brewer_id'] = int(data['brewer_id'])
        
        # Update the session
        factory = get_repository_factory()
        session = factory.get_shot_session_repository(user_id).update(session_id, data)
        
        if not session:
            return jsonify({'error': 'Shot session not found'}), 404
        
        # Enrich with shots
        session = enrich_shot_session_with_shots(session, factory, user_id)
        
        return jsonify(session)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@shot_sessions_bp.route('/<int:session_id>', methods=['DELETE'])
def delete_shot_session(session_id):
    """Delete a shot session (removes references from shots but doesn't delete them)."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        
        # The delete method in the repository handles removing references from shots
        if factory.get_shot_session_repository(user_id).delete(session_id, factory):
            return '', 204
        
        return jsonify({'error': 'Shot session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@shot_sessions_bp.route('/<int:session_id>/shots', methods=['GET'])
def get_session_shots(session_id):
    """Get all shots in a specific session."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        
        # Check if session exists
        session = factory.get_shot_session_repository(user_id).find_by_id(session_id)
        if not session:
            return jsonify({'error': 'Shot session not found'}), 404
        
        # Get all shots for this session
        shots = factory.get_shot_repository(user_id).find_by_session(session_id)
        
        # Sort by timestamp (oldest first for dialing-in progression)
        shots.sort(key=lambda x: x.get('timestamp', ''))
        
        # Basic enrichment
        for shot in shots:
            if shot.get('product_id'):
                product = factory.get_product_repository(user_id).find_by_id(shot['product_id'])
                if product:
                    shot['product_name'] = product.get('product_name', 'Unknown')
            
            if shot.get('brewer_id'):
                brewer = factory.get_brewer_repository(user_id).find_by_id(shot['brewer_id'])
                if brewer:
                    shot['brewer_name'] = brewer.get('name', 'Unknown')
        
        return jsonify(shots)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@shot_sessions_bp.route('/<int:session_id>/add_shot', methods=['POST'])
def add_shot_to_session(session_id):
    """Add an existing shot to a session."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        data = request.get_json()
        shot_id = data.get('shot_id')
        
        if not shot_id:
            return jsonify({'error': 'shot_id is required'}), 400
        
        # Convert shot_id to integer to ensure consistent data types
        shot_id = int(shot_id)
        
        factory = get_repository_factory()
        
        # Check if session exists
        session = factory.get_shot_session_repository(user_id).find_by_id(session_id)
        if not session:
            return jsonify({'error': 'Shot session not found'}), 404
        
        # Check if shot exists
        shot = factory.get_shot_repository(user_id).find_by_id(shot_id)
        if not shot:
            return jsonify({'error': 'Shot not found'}), 404
        
        # Update shot to reference this session
        shot['shot_session_id'] = session_id
        updated_shot = factory.get_shot_repository(user_id).update(shot_id, shot)
        
        return jsonify(updated_shot)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@shot_sessions_bp.route('/<int:session_id>/duplicate', methods=['POST'])
def duplicate_shot_session(session_id):
    """Duplicate a shot session."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        session_repo = factory.get_shot_session_repository(user_id)
        
        # Get the original session
        original_session = session_repo.find_by_id(session_id)
        if not original_session:
            return jsonify({'error': 'Shot session not found'}), 404
        
        # Create duplicate with modified title
        duplicate_data = original_session.copy()
        duplicate_data.pop('id', None)  # Remove ID so a new one is generated
        duplicate_data.pop('created_at', None)  # Remove timestamp so a new one is generated
        duplicate_data.pop('updated_at', None)
        
        # Modify the title to indicate it's a duplicate
        original_title = duplicate_data.get('title', 'Session')
        if '(Copy' in original_title:
            # If already a copy, increment the number
            import re
            match = re.search(r'\(Copy( \d+)?\)$', original_title)
            if match:
                number_part = match.group(1)
                if number_part:
                    current_num = int(number_part.strip())
                    new_title = original_title.replace(f'(Copy {current_num})', f'(Copy {current_num + 1})')
                else:
                    new_title = original_title.replace('(Copy)', '(Copy 2)')
            else:
                new_title = f"{original_title} (Copy)"
        else:
            new_title = f"{original_title} (Copy)"
        
        duplicate_data['title'] = new_title
        
        # Create the duplicate
        new_session = session_repo.create(duplicate_data)
        
        return jsonify({
            'message': 'Shot session duplicated successfully',
            'original_shot_session': original_session,
            'new_shot_session': new_session
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@shot_sessions_bp.route('/<int:session_id>/duplicate_newest_shot', methods=['POST'])
def duplicate_newest_shot_in_session(session_id):
    """Duplicate the newest shot in a session for iterative dialing-in."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        
        # Check if session exists
        session = factory.get_shot_session_repository(user_id).find_by_id(session_id)
        if not session:
            return jsonify({'error': 'Shot session not found'}), 404
        
        # Get all shots for this session
        shots = factory.get_shot_repository(user_id).find_by_session(session_id)
        
        if not shots:
            return jsonify({'error': 'No shots found in this session to duplicate'}), 404
        
        # Find the newest shot (sort by timestamp, then by ID)
        shots.sort(key=lambda x: (x.get('timestamp', ''), x.get('id', 0)), reverse=True)
        newest_shot = shots[0]
        
        # Create duplicate shot data
        duplicate_data = newest_shot.copy()
        duplicate_data.pop('id', None)  # Remove ID so a new one is generated
        duplicate_data.pop('timestamp', None)  # Remove timestamp so a new one is generated
        duplicate_data.pop('created_at', None)
        duplicate_data.pop('updated_at', None)
        
        # Clear fields that typically change between shots
        duplicate_data.pop('overall_score', None)
        duplicate_data.pop('notes', None)
        duplicate_data.pop('extraction_status', None)
        
        # Keep the session reference
        duplicate_data['shot_session_id'] = session_id
        
        # Create the duplicate shot
        new_shot = factory.get_shot_repository(user_id).create(duplicate_data)
        
        return jsonify({
            'message': 'Newest shot duplicated successfully',
            'original_shot': newest_shot,
            'new_shot': new_shot,
            'session_id': session_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@shot_sessions_bp.route('/filter_options', methods=['GET'])
def get_shot_session_filter_options():
    """Get all unique values for shot session filters."""
    try:
        # Get and validate user_id
        user_id = get_user_id_from_request()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        factory = get_repository_factory()
        shot_sessions = factory.get_shot_session_repository(user_id).find_all()
        
        # Collect unique values for each filterable field
        products = set()
        batches = set()
        brewers = set()
        
        for session in shot_sessions:
            if session.get('product_id'):
                product = factory.get_product_repository(user_id).find_by_id(session['product_id'])
                if product:
                    products.add((product['id'], product.get('product_name', 'Unknown')))
            
            if session.get('product_batch_id'):
                batch = factory.get_batch_repository(user_id).find_by_id(session['product_batch_id'])
                if batch:
                    batches.add((batch['id'], f"Batch {batch['id']} - {batch.get('roast_date', 'Unknown')}"))
            
            if session.get('brewer_id'):
                brewer = factory.get_brewer_repository(user_id).find_by_id(session['brewer_id'])
                if brewer:
                    brewers.add((brewer['id'], brewer.get('name', 'Unknown')))
        
        # Format for response
        filter_options = {
            'products': [{'id': id, 'product_name': name} for id, name in sorted(products, key=lambda x: x[1])],
            'batches': [{'id': id, 'name': name} for id, name in sorted(batches, key=lambda x: x[0])],
            'brewers': [{'id': id, 'name': name} for id, name in sorted(brewers, key=lambda x: x[1])],
        }
        
        return jsonify(filter_options)
    except Exception as e:
        return jsonify({'error': str(e)}), 500