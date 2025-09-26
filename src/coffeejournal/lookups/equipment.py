"""
Equipment lookup endpoints (grinders, filters, kettles, scales).
Restored from original lookups.py to preserve all functionality.
"""

from flask import Blueprint, jsonify, request
from .common import validate_user_context, validate_lookup_data
from ..repositories.factory import get_repository_factory

equipment_bp = Blueprint('equipment', __name__)


# ==================== GRINDERS ====================

@equipment_bp.route('/grinders', methods=['GET'])
@validate_user_context
def get_grinders(user_id):
    """Get all grinders."""
    try:
        factory = get_repository_factory()
        grinders = factory.get_grinder_repository(user_id).find_all()
        return jsonify(grinders)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/grinders/search', methods=['GET'])
@validate_user_context
def search_grinders(user_id):
    """Search grinders by name or short_form."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    try:
        factory = get_repository_factory()
        results = factory.get_grinder_repository(user_id).search(query)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/grinders/<int:grinder_id>', methods=['GET'])
@validate_user_context
def get_grinder(user_id, grinder_id):
    """Get a specific grinder."""
    try:
        factory = get_repository_factory()
        grinder = factory.get_grinder_repository(user_id).find_by_id(grinder_id)
        if not grinder:
            return jsonify({'error': 'Grinder not found'}), 404
        return jsonify(grinder)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/grinders', methods=['POST'])
@validate_user_context
def create_grinder(user_id):
    """Create a new grinder."""
    try:
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


@equipment_bp.route('/grinders/<int:grinder_id>', methods=['PUT'])
@validate_user_context
def update_grinder(user_id, grinder_id):
    """Update an existing grinder."""
    try:
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


@equipment_bp.route('/grinders/<int:grinder_id>', methods=['DELETE'])
@validate_user_context
def delete_grinder(user_id, grinder_id):
    """Delete a grinder."""
    try:
        factory = get_repository_factory()
        success = factory.get_grinder_repository(user_id).delete(grinder_id)
        if not success:
            return jsonify({'error': 'Grinder not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/grinders/<int:grinder_id>/usage', methods=['GET'])
@validate_user_context
def check_grinder_usage(user_id, grinder_id):
    """Check if grinder is in use by brew sessions."""
    try:
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


@equipment_bp.route('/grinders/<int:grinder_id>/update_references', methods=['POST'])
@validate_user_context
def update_grinder_references(user_id, grinder_id):
    """Update or remove grinder references in brew sessions."""
    try:
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
                else:
                    continue
                
                factory.get_brew_session_repository(user_id).update(session['id'], session)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/grinders/default', methods=['GET'])
@validate_user_context
def get_default_grinder(user_id):
    """Get the default grinder."""
    try:
        factory = get_repository_factory()
        default_grinder = factory.get_grinder_repository(user_id).find_default()
        if not default_grinder:
            return jsonify({'error': 'No default grinder set'}), 404
        return jsonify(default_grinder)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/grinders/smart_default', methods=['GET'])
@validate_user_context
def get_smart_default_grinder(user_id):
    """Get the smart default grinder based on usage patterns."""
    try:
        factory = get_repository_factory()
        smart_default = factory.get_grinder_repository(user_id).get_smart_default()
        if not smart_default:
            return jsonify({'error': 'No grinders available'}), 404
        return jsonify(smart_default)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/grinders/<int:grinder_id>/set_default', methods=['POST'])
@validate_user_context
def set_default_grinder(user_id, grinder_id):
    """Set a grinder as the default."""
    try:
        factory = get_repository_factory()
        repo = factory.get_grinder_repository(user_id)
        grinder = repo.set_default(grinder_id)
        return jsonify(grinder)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/grinders/<int:grinder_id>/clear_default', methods=['POST'])
@validate_user_context
def clear_default_grinder(user_id, grinder_id):
    """Clear the default flag from a grinder."""
    try:
        factory = get_repository_factory()
        repo = factory.get_grinder_repository(user_id)
        grinder = repo.clear_default(grinder_id)
        return jsonify(grinder)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/grinders/<int:grinder_id>/stats', methods=['GET'])
@validate_user_context
def get_grinder_stats(user_id, grinder_id):
    """Get statistics for a specific grinder."""
    try:
        factory = get_repository_factory()
        grinder = factory.get_grinder_repository(user_id).find_by_id(grinder_id)
        if not grinder:
            return jsonify({'error': 'Grinder not found'}), 404

        repo = factory.get_grinder_repository(user_id)
        stats = repo.get_usage_stats(grinder_id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/grinders/<int:grinder_id>/scores-over-time', methods=['GET'])
@validate_user_context
def get_grinder_scores_over_time(user_id, grinder_id):
    """Get brew session scores over time for a specific grinder."""
    try:
        from ..api.utils import enrich_brew_session_with_lookups

        factory = get_repository_factory()
        grinder = factory.get_grinder_repository(user_id).find_by_id(grinder_id)
        if not grinder:
            return jsonify({'error': 'Grinder not found'}), 404

        # Get all brew sessions for this grinder sorted by timestamp
        brew_sessions_repo = factory.get_brew_session_repository(user_id)
        all_sessions = brew_sessions_repo.find_all()

        # Filter sessions for this grinder and sort by timestamp
        grinder_sessions = [s for s in all_sessions if s.get('grinder_id') == grinder_id]
        grinder_sessions.sort(key=lambda x: x.get('timestamp', ''))

        # Build scores over time data
        scores_data = []
        for session in grinder_sessions:
            # Enrich session with lookup data first to get calculated_score
            enriched_session = enrich_brew_session_with_lookups(session.copy(), factory, user_id)

            # Check if session has a calculated score
            calculated_score = enriched_session.get('calculated_score')
            if calculated_score is not None and calculated_score > 0:
                # Get product name - try multiple sources
                product_name = 'Unknown'

                # First try product_details if already enriched
                if enriched_session.get('product_details') and enriched_session['product_details'].get('product_name'):
                    product_name = enriched_session['product_details']['product_name']

                # Fallback to direct product lookup via batch
                elif enriched_session.get('product_batch_id'):
                    batch = factory.get_batch_repository(user_id).find_by_id(enriched_session['product_batch_id'])
                    if batch and batch.get('product_id'):
                        product = factory.get_product_repository(user_id).find_by_id(batch['product_id'])
                        if product:
                            product_name = product.get('name', 'Unknown')

                # Another fallback via direct product_id
                elif enriched_session.get('product_id'):
                    product = factory.get_product_repository(user_id).find_by_id(enriched_session['product_id'])
                    if product:
                        product_name = product.get('name', 'Unknown')

                # Get brew method name
                brew_method_name = 'Unknown'
                if enriched_session.get('brew_method') and enriched_session['brew_method']:
                    brew_method_name = enriched_session['brew_method'].get('name', 'Unknown')

                scores_data.append({
                    'date': enriched_session.get('timestamp', '')[:10],  # YYYY-MM-DD format
                    'timestamp': enriched_session.get('timestamp', ''),
                    'score': calculated_score,
                    'product_name': product_name,
                    'brew_method': brew_method_name
                })

        return jsonify({
            'grinder_name': grinder.get('name', 'Unknown'),
            'data': scores_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/grinders/<int:grinder_id>/usage-over-time', methods=['GET'])
@validate_user_context
def get_grinder_usage_over_time(user_id, grinder_id):
    """Get daily usage (grams ground) over time for a specific grinder."""
    try:
        from collections import defaultdict
        from datetime import datetime

        factory = get_repository_factory()
        grinder = factory.get_grinder_repository(user_id).find_by_id(grinder_id)
        if not grinder:
            return jsonify({'error': 'Grinder not found'}), 404

        # Get all brew sessions and shots for this grinder
        brew_sessions_repo = factory.get_brew_session_repository(user_id)
        shots_repo = factory.get_shot_repository(user_id)
        all_sessions = brew_sessions_repo.find_all()
        all_shots = shots_repo.find_all()

        # Filter sessions for this grinder and group by date
        daily_usage = defaultdict(float)

        # Process brew sessions
        for session in all_sessions:
            if session.get('grinder_id') == grinder_id:
                # Get the coffee amount (grams ground)
                coffee_grams = session.get('amount_coffee_grams', 0)
                if coffee_grams and coffee_grams > 0:
                    # Get date from timestamp
                    timestamp = session.get('timestamp', '')
                    if timestamp:
                        date = timestamp[:10]  # YYYY-MM-DD format
                        daily_usage[date] += coffee_grams

        # Process shots (espresso) - shots have grinder_id directly
        for shot in all_shots:
            if shot.get('grinder_id') == grinder_id:
                # Get the dose amount (grams ground)
                dose_grams = shot.get('dose_grams', 0)
                if dose_grams and dose_grams > 0:
                    # Get date from timestamp
                    timestamp = shot.get('timestamp', '')
                    if timestamp:
                        date = timestamp[:10]  # YYYY-MM-DD format
                        daily_usage[date] += dose_grams

        # Convert to sorted list of daily usage
        usage_data = []
        for date, grams in sorted(daily_usage.items()):
            usage_data.append({
                'date': date,
                'grams_ground': round(grams, 1)
            })

        return jsonify({
            'grinder_name': grinder.get('name', 'Unknown'),
            'data': usage_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== FILTERS ====================

@equipment_bp.route('/filters', methods=['GET'])
@validate_user_context
def get_filters(user_id):
    """Get all filters."""
    try:
        factory = get_repository_factory()
        filters = factory.get_filter_repository(user_id).find_all()
        return jsonify(filters)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/filters/<int:filter_id>', methods=['GET'])
@validate_user_context
def get_filter(user_id, filter_id):
    """Get a specific filter."""
    try:
        factory = get_repository_factory()
        filter_item = factory.get_filter_repository(user_id).find_by_id(filter_id)
        if not filter_item:
            return jsonify({'error': 'Filter not found'}), 404
        return jsonify(filter_item)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/filters', methods=['POST'])
@validate_user_context
def create_filter(user_id):
    """Create a new filter."""
    try:
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        
        factory = get_repository_factory()
        filter_item = factory.get_filter_repository(user_id).create(data)
        return jsonify(filter_item), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/filters/<int:filter_id>', methods=['PUT'])
@validate_user_context
def update_filter(user_id, filter_id):
    """Update an existing filter."""
    try:
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


@equipment_bp.route('/filters/<int:filter_id>', methods=['DELETE'])
@validate_user_context
def delete_filter(user_id, filter_id):
    """Delete a filter."""
    try:
        factory = get_repository_factory()
        success = factory.get_filter_repository(user_id).delete(filter_id)
        if not success:
            return jsonify({'error': 'Filter not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/filters/<int:filter_id>/usage', methods=['GET'])
@validate_user_context
def check_filter_usage(user_id, filter_id):
    """Check if filter is in use by brew sessions."""
    try:
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


@equipment_bp.route('/filters/<int:filter_id>/update_references', methods=['POST'])
@validate_user_context
def update_filter_references(user_id, filter_id):
    """Update or remove filter references in brew sessions."""
    try:
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
                else:
                    continue
                
                factory.get_brew_session_repository(user_id).update(session['id'], session)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== KETTLES ====================

@equipment_bp.route('/kettles', methods=['GET'])
@validate_user_context
def get_kettles(user_id):
    """Get all kettles."""
    try:
        factory = get_repository_factory()
        kettles = factory.get_kettle_repository(user_id).find_all()
        return jsonify(kettles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/kettles/<int:kettle_id>', methods=['GET'])
@validate_user_context
def get_kettle(user_id, kettle_id):
    """Get a specific kettle."""
    try:
        factory = get_repository_factory()
        kettle = factory.get_kettle_repository(user_id).find_by_id(kettle_id)
        if not kettle:
            return jsonify({'error': 'Kettle not found'}), 404
        return jsonify(kettle)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/kettles', methods=['POST'])
@validate_user_context
def create_kettle(user_id):
    """Create a new kettle."""
    try:
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        
        factory = get_repository_factory()
        kettle = factory.get_kettle_repository(user_id).create(data)
        return jsonify(kettle), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/kettles/<int:kettle_id>', methods=['PUT'])
@validate_user_context
def update_kettle(user_id, kettle_id):
    """Update an existing kettle."""
    try:
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


@equipment_bp.route('/kettles/<int:kettle_id>', methods=['DELETE'])
@validate_user_context
def delete_kettle(user_id, kettle_id):
    """Delete a kettle."""
    try:
        factory = get_repository_factory()
        success = factory.get_kettle_repository(user_id).delete(kettle_id)
        if not success:
            return jsonify({'error': 'Kettle not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/kettles/<int:kettle_id>/usage', methods=['GET'])
@validate_user_context
def check_kettle_usage(user_id, kettle_id):
    """Check if kettle is in use by brew sessions."""
    try:
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


@equipment_bp.route('/kettles/<int:kettle_id>/update_references', methods=['POST'])
@validate_user_context
def update_kettle_references(user_id, kettle_id):
    """Update or remove kettle references in brew sessions."""
    try:
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
                else:
                    continue
                
                factory.get_brew_session_repository(user_id).update(session['id'], session)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== SCALES ====================

@equipment_bp.route('/scales', methods=['GET'])
@validate_user_context
def get_scales(user_id):
    """Get all scales."""
    try:
        factory = get_repository_factory()
        scales = factory.get_scale_repository(user_id).find_all()
        return jsonify(scales)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/scales/search', methods=['GET'])
@validate_user_context
def search_scales(user_id):
    """Search scales by name."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    try:
        factory = get_repository_factory()
        results = factory.get_scale_repository(user_id).search(query)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/scales/<int:scale_id>', methods=['GET'])
@validate_user_context
def get_scale(user_id, scale_id):
    """Get a specific scale."""
    try:
        factory = get_repository_factory()
        scale = factory.get_scale_repository(user_id).find_by_id(scale_id)
        if not scale:
            return jsonify({'error': 'Scale not found'}), 404
        return jsonify(scale)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/scales', methods=['POST'])
@validate_user_context
def create_scale(user_id):
    """Create a new scale."""
    try:
        data = request.get_json()
        error_msg, status_code = validate_lookup_data(data)
        if error_msg:
            return jsonify({'error': error_msg}), status_code
        
        factory = get_repository_factory()
        scale = factory.get_scale_repository(user_id).create(data)
        return jsonify(scale), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/scales/<int:scale_id>', methods=['PUT'])
@validate_user_context
def update_scale(user_id, scale_id):
    """Update an existing scale."""
    try:
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


@equipment_bp.route('/scales/<int:scale_id>', methods=['DELETE'])
@validate_user_context
def delete_scale(user_id, scale_id):
    """Delete a scale."""
    try:
        factory = get_repository_factory()
        success = factory.get_scale_repository(user_id).delete(scale_id)
        if not success:
            return jsonify({'error': 'Scale not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@equipment_bp.route('/scales/<int:scale_id>/usage', methods=['GET'])
@validate_user_context
def check_scale_usage(user_id, scale_id):
    """Check if scale is in use by brew sessions."""
    try:
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


@equipment_bp.route('/scales/<int:scale_id>/update_references', methods=['POST'])
@validate_user_context
def update_scale_references(user_id, scale_id):
    """Update or remove scale references in brew sessions."""
    try:
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
                else:
                    continue
                
                factory.get_brew_session_repository(user_id).update(session['id'], session)
                updated_count += 1
        
        return jsonify({'updated_count': updated_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500