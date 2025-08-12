"""
Common utilities for lookup endpoints.
"""

from flask import jsonify
from functools import wraps
from ..api.utils import get_user_id_from_request, validate_user_id


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


def create_standard_endpoints(blueprint, repo_name, item_name, plural_name=None):
    """
    Create standard CRUD endpoints for a lookup type.
    
    Args:
        blueprint: Flask blueprint to add routes to
        repo_name: Repository method name (e.g., 'get_roaster_repository')
        item_name: Singular item name (e.g., 'roaster')
        plural_name: Plural name (defaults to item_name + 's')
    """
    if plural_name is None:
        plural_name = item_name + 's'
    
    from ..repositories.factory import get_repository_factory
    from flask import request
    
    @blueprint.route(f'/{plural_name}', methods=['GET'])
    @validate_user_context
    def get_items(user_id):
        f"""Get all {plural_name}."""
        try:
            factory = get_repository_factory()
            repo = getattr(factory, repo_name)(user_id)
            items = repo.find_all()
            
            # Optional search filter
            search = request.args.get('search')
            if search:
                search_lower = search.lower()
                items = [item for item in items 
                        if search_lower in item.get('name', '').lower() or 
                           search_lower in item.get('description', '').lower()]
            
            return jsonify(items)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route(f'/{plural_name}', methods=['POST'])
    @validate_user_context
    def create_item(user_id):
        f"""Create a new {item_name}."""
        try:
            data = request.get_json()
            error, status_code = validate_lookup_data(data, item_name)
            if error:
                return jsonify({'error': error}), status_code
            
            factory = get_repository_factory()
            repo = getattr(factory, repo_name)(user_id)
            item = repo.create(data)
            return jsonify(item), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route(f'/{plural_name}/<int:item_id>', methods=['PUT'])
    @validate_user_context
    def update_item(user_id, item_id):
        f"""Update an existing {item_name}."""
        try:
            data = request.get_json()
            error, status_code = validate_lookup_data(data, item_name)
            if error:
                return jsonify({'error': error}), status_code
            
            factory = get_repository_factory()
            repo = getattr(factory, repo_name)(user_id)
            item = repo.update(item_id, data)
            if not item:
                return jsonify({'error': f'{item_name.capitalize()} not found'}), 404
            return jsonify(item)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route(f'/{plural_name}/<int:item_id>', methods=['DELETE'])
    @validate_user_context
    def delete_item(user_id, item_id):
        f"""Delete a {item_name}."""
        try:
            factory = get_repository_factory()
            repo = getattr(factory, repo_name)(user_id)
            if repo.delete(item_id):
                return '', 204
            return jsonify({'error': f'{item_name.capitalize()} not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500