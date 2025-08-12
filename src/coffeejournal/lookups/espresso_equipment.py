"""
Espresso equipment lookup endpoints (brewers, portafilters, baskets, tampers, WDT tools, leveling tools).
"""

from flask import Blueprint, jsonify, request
from .common import validate_user_context, validate_lookup_data
from ..repositories.factory import get_repository_factory

espresso_equipment_bp = Blueprint('espresso_equipment', __name__)


# ==================== BREWERS ====================

@espresso_equipment_bp.route('/brewers', methods=['GET'])
@validate_user_context
def get_brewers(user_id):
    """Get all brewers with optional search."""
    try:
        factory = get_repository_factory()
        brewers = factory.get_brewer_repository(user_id).find_all()
        
        # Optional search filter
        search = request.args.get('search')
        if search:
            search_lower = search.lower()
            brewers = [b for b in brewers if search_lower in b.get('name', '').lower() or 
                      search_lower in b.get('type', '').lower() or
                      search_lower in b.get('description', '').lower()]
        
        return jsonify(brewers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/brewers/<int:brewer_id>', methods=['GET'])
@validate_user_context
def get_brewer(user_id, brewer_id):
    """Get a specific brewer by ID."""
    try:
        factory = get_repository_factory()
        brewer = factory.get_brewer_repository(user_id).find_by_id(brewer_id)
        if not brewer:
            return jsonify({'error': 'Brewer not found'}), 404
        return jsonify(brewer)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/brewers', methods=['POST'])
@validate_user_context
def create_brewer(user_id):
    """Create a new brewer."""
    try:
        data = request.get_json()
        error, status_code = validate_lookup_data(data, "brewer")
        if error:
            return jsonify({'error': error}), status_code
        
        factory = get_repository_factory()
        brewer = factory.get_brewer_repository(user_id).create(data)
        return jsonify(brewer), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/brewers/<int:brewer_id>', methods=['PUT'])
@validate_user_context
def update_brewer(user_id, brewer_id):
    """Update an existing brewer."""
    try:
        data = request.get_json()
        error, status_code = validate_lookup_data(data, "brewer")
        if error:
            return jsonify({'error': error}), status_code
        
        factory = get_repository_factory()
        brewer = factory.get_brewer_repository(user_id).update(brewer_id, data)
        if not brewer:
            return jsonify({'error': 'Brewer not found'}), 404
        return jsonify(brewer)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/brewers/<int:brewer_id>', methods=['DELETE'])
@validate_user_context
def delete_brewer(user_id, brewer_id):
    """Delete a brewer."""
    try:
        factory = get_repository_factory()
        if factory.get_brewer_repository(user_id).delete(brewer_id):
            return '', 204
        return jsonify({'error': 'Brewer not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/brewers/<int:brewer_id>/usage', methods=['GET'])
@validate_user_context
def check_brewer_usage(user_id, brewer_id):
    """Check if brewer is used in brew sessions or shots."""
    try:
        factory = get_repository_factory()
        brewer = factory.get_brewer_repository(user_id).find_by_id(brewer_id)
        if not brewer:
            return jsonify({'error': 'Brewer not found'}), 404
        
        # Check brew sessions
        brew_sessions = factory.get_brew_session_repository(user_id).find_all()
        brew_usage_count = sum(1 for s in brew_sessions if s.get('brewer_id') == brewer_id)
        
        # Check shots
        shots = factory.get_shot_repository(user_id).find_all()
        shot_usage_count = sum(1 for s in shots if s.get('brewer_id') == brewer_id)
        
        total_usage = brew_usage_count + shot_usage_count
        
        # Determine usage type based on actual usage
        if brew_usage_count > 0 and shot_usage_count > 0:
            usage_type = 'brew_sessions_and_shots'
        elif brew_usage_count > 0:
            usage_type = 'brew_sessions'
        elif shot_usage_count > 0:
            usage_type = 'shots'
        else:
            usage_type = 'none'
        
        return jsonify({
            'in_use': total_usage > 0,
            'usage_count': total_usage,
            'brew_session_count': brew_usage_count,
            'shot_count': shot_usage_count,
            'usage_type': usage_type
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== PORTAFILTERS ====================

@espresso_equipment_bp.route('/portafilters', methods=['GET'])
@validate_user_context
def get_portafilters(user_id):
    """Get all portafilters."""
    try:
        factory = get_repository_factory()
        portafilters = factory.get_portafilter_repository(user_id).find_all()
        
        search = request.args.get('search')
        if search:
            search_lower = search.lower()
            portafilters = [p for p in portafilters if search_lower in p.get('name', '').lower() or 
                          search_lower in p.get('size', '').lower()]
        
        return jsonify(portafilters)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/portafilters/<int:portafilter_id>', methods=['GET'])
@validate_user_context
def get_portafilter(user_id, portafilter_id):
    """Get a specific portafilter by ID."""
    try:
        factory = get_repository_factory()
        portafilter = factory.get_portafilter_repository(user_id).find_by_id(portafilter_id)
        if not portafilter:
            return jsonify({'error': 'Portafilter not found'}), 404
        return jsonify(portafilter)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/portafilters', methods=['POST'])
@validate_user_context
def create_portafilter(user_id):
    """Create a new portafilter."""
    try:
        data = request.get_json()
        error, status_code = validate_lookup_data(data, "portafilter")
        if error:
            return jsonify({'error': error}), status_code
        
        factory = get_repository_factory()
        portafilter = factory.get_portafilter_repository(user_id).create(data)
        return jsonify(portafilter), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/portafilters/<int:portafilter_id>', methods=['PUT'])
@validate_user_context
def update_portafilter(user_id, portafilter_id):
    """Update an existing portafilter."""
    try:
        data = request.get_json()
        error, status_code = validate_lookup_data(data, "portafilter")
        if error:
            return jsonify({'error': error}), status_code
        
        factory = get_repository_factory()
        portafilter = factory.get_portafilter_repository(user_id).update(portafilter_id, data)
        if not portafilter:
            return jsonify({'error': 'Portafilter not found'}), 404
        return jsonify(portafilter)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/portafilters/<int:portafilter_id>', methods=['DELETE'])
@validate_user_context
def delete_portafilter(user_id, portafilter_id):
    """Delete a portafilter."""
    try:
        factory = get_repository_factory()
        if factory.get_portafilter_repository(user_id).delete(portafilter_id):
            return '', 204
        return jsonify({'error': 'Portafilter not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/portafilters/<int:portafilter_id>/usage', methods=['GET'])
@validate_user_context
def check_portafilter_usage(user_id, portafilter_id):
    """Check if portafilter is used in shots."""
    try:
        factory = get_repository_factory()
        portafilter = factory.get_portafilter_repository(user_id).find_by_id(portafilter_id)
        if not portafilter:
            return jsonify({'error': 'Portafilter not found'}), 404
        
        shots = factory.get_shot_repository(user_id).find_all()
        usage_count = sum(1 for s in shots if s.get('portafilter_id') == portafilter_id)
        
        return jsonify({
            'in_use': usage_count > 0,
            'usage_count': usage_count,
            'usage_type': 'shots'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== BASKETS ====================

@espresso_equipment_bp.route('/baskets', methods=['GET'])  
@validate_user_context
def get_baskets(user_id):
    """Get all baskets."""
    try:
        factory = get_repository_factory()
        baskets = factory.get_basket_repository(user_id).find_all()
        return jsonify(baskets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/baskets/<int:basket_id>', methods=['GET'])
@validate_user_context
def get_basket(user_id, basket_id):
    """Get a specific basket by ID."""
    try:
        factory = get_repository_factory()
        basket = factory.get_basket_repository(user_id).find_by_id(basket_id)
        if not basket:
            return jsonify({'error': 'Basket not found'}), 404
        return jsonify(basket)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/baskets', methods=['POST'])
@validate_user_context
def create_basket(user_id):
    """Create a new basket."""
    try:
        data = request.get_json()
        error, status_code = validate_lookup_data(data, "basket")
        if error:
            return jsonify({'error': error}), status_code
        
        factory = get_repository_factory()
        basket = factory.get_basket_repository(user_id).create(data)
        return jsonify(basket), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/baskets/<int:basket_id>', methods=['PUT'])
@validate_user_context
def update_basket(user_id, basket_id):
    """Update an existing basket."""
    try:
        data = request.get_json()
        error, status_code = validate_lookup_data(data, "basket")
        if error:
            return jsonify({'error': error}), status_code
        
        factory = get_repository_factory()
        basket = factory.get_basket_repository(user_id).update(basket_id, data)
        if not basket:
            return jsonify({'error': 'Basket not found'}), 404
        return jsonify(basket)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/baskets/<int:basket_id>', methods=['DELETE'])
@validate_user_context
def delete_basket(user_id, basket_id):
    """Delete a basket."""
    try:
        factory = get_repository_factory()
        if factory.get_basket_repository(user_id).delete(basket_id):
            return '', 204
        return jsonify({'error': 'Basket not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== TAMPERS ====================

@espresso_equipment_bp.route('/tampers', methods=['GET'])
@validate_user_context  
def get_tampers(user_id):
    """Get all tampers."""
    try:
        factory = get_repository_factory()
        tampers = factory.get_tamper_repository(user_id).find_all()
        return jsonify(tampers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/tampers', methods=['POST'])
@validate_user_context
def create_tamper(user_id):
    """Create a new tamper."""
    try:
        data = request.get_json()
        error, status_code = validate_lookup_data(data, "tamper")
        if error:
            return jsonify({'error': error}), status_code
        
        factory = get_repository_factory()
        tamper = factory.get_tamper_repository(user_id).create(data)
        return jsonify(tamper), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/tampers/<int:tamper_id>', methods=['GET'])
@validate_user_context
def get_tamper(user_id, tamper_id):
    """Get a specific tamper by ID."""
    try:
        factory = get_repository_factory()
        tamper = factory.get_tamper_repository(user_id).find_by_id(tamper_id)
        if not tamper:
            return jsonify({'error': 'Tamper not found'}), 404
        return jsonify(tamper)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/tampers/<int:tamper_id>', methods=['PUT'])
@validate_user_context
def update_tamper(user_id, tamper_id):
    """Update an existing tamper."""
    try:
        data = request.get_json()
        error, status_code = validate_lookup_data(data, "tamper")
        if error:
            return jsonify({'error': error}), status_code
        
        factory = get_repository_factory()
        tamper = factory.get_tamper_repository(user_id).update(tamper_id, data)
        if not tamper:
            return jsonify({'error': 'Tamper not found'}), 404
        return jsonify(tamper)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/tampers/<int:tamper_id>', methods=['DELETE'])
@validate_user_context
def delete_tamper(user_id, tamper_id):
    """Delete a tamper."""
    try:
        factory = get_repository_factory()
        if factory.get_tamper_repository(user_id).delete(tamper_id):
            return '', 204
        return jsonify({'error': 'Tamper not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== WDT TOOLS ====================

@espresso_equipment_bp.route('/wdt_tools', methods=['GET'])
@validate_user_context
def get_wdt_tools(user_id):
    """Get all WDT tools."""
    try:
        factory = get_repository_factory()
        wdt_tools = factory.get_wdt_tool_repository(user_id).find_all()
        return jsonify(wdt_tools)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/wdt_tools', methods=['POST'])
@validate_user_context
def create_wdt_tool(user_id):
    """Create a new WDT tool."""
    try:
        data = request.get_json()
        error, status_code = validate_lookup_data(data, "WDT tool")
        if error:
            return jsonify({'error': error}), status_code
        
        factory = get_repository_factory()
        wdt_tool = factory.get_wdt_tool_repository(user_id).create(data)
        return jsonify(wdt_tool), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/wdt_tools/<int:wdt_tool_id>', methods=['GET'])
@validate_user_context
def get_wdt_tool(user_id, wdt_tool_id):
    """Get a specific WDT tool by ID."""
    try:
        factory = get_repository_factory()
        wdt_tool = factory.get_wdt_tool_repository(user_id).find_by_id(wdt_tool_id)
        if not wdt_tool:
            return jsonify({'error': 'WDT tool not found'}), 404
        return jsonify(wdt_tool)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/wdt_tools/<int:wdt_tool_id>', methods=['PUT'])
@validate_user_context
def update_wdt_tool(user_id, wdt_tool_id):
    """Update an existing WDT tool."""
    try:
        data = request.get_json()
        error, status_code = validate_lookup_data(data, "WDT tool")
        if error:
            return jsonify({'error': error}), status_code
        
        factory = get_repository_factory()
        wdt_tool = factory.get_wdt_tool_repository(user_id).update(wdt_tool_id, data)
        if not wdt_tool:
            return jsonify({'error': 'WDT tool not found'}), 404
        return jsonify(wdt_tool)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/wdt_tools/<int:wdt_tool_id>', methods=['DELETE'])
@validate_user_context
def delete_wdt_tool(user_id, wdt_tool_id):
    """Delete a WDT tool."""
    try:
        factory = get_repository_factory()
        if factory.get_wdt_tool_repository(user_id).delete(wdt_tool_id):
            return '', 204
        return jsonify({'error': 'WDT tool not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== LEVELING TOOLS ====================

@espresso_equipment_bp.route('/leveling_tools', methods=['GET'])
@validate_user_context
def get_leveling_tools(user_id):
    """Get all leveling tools."""
    try:
        factory = get_repository_factory()
        leveling_tools = factory.get_leveling_tool_repository(user_id).find_all()
        return jsonify(leveling_tools)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/leveling_tools', methods=['POST'])
@validate_user_context
def create_leveling_tool(user_id):
    """Create a new leveling tool."""
    try:
        data = request.get_json()
        error, status_code = validate_lookup_data(data, "leveling tool")
        if error:
            return jsonify({'error': error}), status_code
        
        factory = get_repository_factory()
        leveling_tool = factory.get_leveling_tool_repository(user_id).create(data)
        return jsonify(leveling_tool), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/leveling_tools/<int:leveling_tool_id>', methods=['GET'])
@validate_user_context
def get_leveling_tool(user_id, leveling_tool_id):
    """Get a specific leveling tool by ID."""
    try:
        factory = get_repository_factory()
        leveling_tool = factory.get_leveling_tool_repository(user_id).find_by_id(leveling_tool_id)
        if not leveling_tool:
            return jsonify({'error': 'Leveling tool not found'}), 404
        return jsonify(leveling_tool)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/leveling_tools/<int:leveling_tool_id>', methods=['PUT'])
@validate_user_context
def update_leveling_tool(user_id, leveling_tool_id):
    """Update an existing leveling tool."""
    try:
        data = request.get_json()
        error, status_code = validate_lookup_data(data, "leveling tool")
        if error:
            return jsonify({'error': error}), status_code
        
        factory = get_repository_factory()
        leveling_tool = factory.get_leveling_tool_repository(user_id).update(leveling_tool_id, data)
        if not leveling_tool:
            return jsonify({'error': 'Leveling tool not found'}), 404
        return jsonify(leveling_tool)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@espresso_equipment_bp.route('/leveling_tools/<int:leveling_tool_id>', methods=['DELETE'])
@validate_user_context
def delete_leveling_tool(user_id, leveling_tool_id):
    """Delete a leveling tool."""
    try:
        factory = get_repository_factory()
        if factory.get_leveling_tool_repository(user_id).delete(leveling_tool_id):
            return '', 204
        return jsonify({'error': 'Leveling tool not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500