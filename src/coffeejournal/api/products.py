"""
Product API endpoints for the Coffee Journal application.

This module contains all endpoints related to coffee products:
- GET /products - List all products with optional filtering
- POST /products - Create a new product
- GET /products/{id} - Get a specific product
- PUT /products/{id} - Update a product
- DELETE /products/{id} - Delete a product
- GET /products/{id}/batches - Get batches for a product
- POST /products/{id}/batches - Create a new batch for a product
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
from ..repositories.factory import get_repository_factory
from ..services.brew_recommendations import BrewRecommendationService
from .utils import (
    enrich_product_with_lookups, 
    resolve_lookup_field, 
    safe_int, 
    safe_float,
    calculate_price_per_cup,
    get_user_id_from_request,
    validate_user_id
)

products_bp = Blueprint('products', __name__)


@products_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products with optional filtering and smart ordering."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    product_repo = factory.get_product_repository(user_id)
    
    # Check if smart ordering with batch status is requested
    smart_order = request.args.get('smart_order', 'false').lower() == 'true'
    
    if smart_order:
        # Get products with smart ordering and batch status
        products = product_repo.get_products_with_batch_status(factory, user_id)
    else:
        # Get all products in default order
        products = product_repo.find_all()
    
    # Enrich all products with lookup objects
    enriched_products = []
    for product in products:
        enriched_product = enrich_product_with_lookups(product.copy(), factory, user_id)
        
        # Preserve batch status info if it exists (from smart ordering)
        if 'has_active_batches' in product:
            enriched_product['has_active_batches'] = product['has_active_batches']
            enriched_product['active_batch_count'] = product['active_batch_count']
            enriched_product['total_batches'] = product['total_batches']
            enriched_product['usage_score'] = product['usage_score']
        
        enriched_products.append(enriched_product)
    
    # Apply filters to enriched products
    filters = {}
    if request.args.get('roaster'):
        filters['roaster'] = request.args.get('roaster')
    if request.args.get('bean_type'):
        filters['bean_type'] = request.args.get('bean_type')
    if request.args.get('country'):
        filters['country'] = request.args.get('country')
    
    if filters:
        filtered_products = enriched_products
        
        if 'roaster' in filters:
            filtered_products = [p for p in filtered_products 
                               if p.get('roaster') and p['roaster'].get('name') == filters['roaster']]
        
        if 'bean_type' in filters:
            filtered_products = [p for p in filtered_products 
                               if p.get('bean_type') and 
                               any(bt.get('name') == filters['bean_type'] for bt in p['bean_type'])]
        
        if 'country' in filters:
            filtered_products = [p for p in filtered_products 
                               if p.get('country') and p['country'].get('name') == filters['country']]
        
        return jsonify(filtered_products)
    
    return jsonify(enriched_products)


@products_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    product = factory.get_product_repository(user_id).find_by_id(product_id)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Enrich product with lookup objects
    enriched_product = enrich_product_with_lookups(product.copy(), factory, user_id)
    
    return jsonify(enriched_product)


@products_bp.route('/products', methods=['POST'])
def create_product():
    """Create a new product."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    data = request.json
    
    # Validate required fields
    if not data.get('roaster') and not data.get('roaster_id') and not data.get('roaster_name'):
        return jsonify({'error': 'Roaster is required'}), 400
    
    # Resolve lookup fields using new helper
    roaster_result = resolve_lookup_field(data, 'roaster', factory.get_roaster_repository(user_id))
    if not roaster_result['item']:
        return jsonify({'error': 'Invalid roaster'}), 400
    
    bean_type_result = resolve_lookup_field(data, 'bean_type', factory.get_bean_type_repository(user_id), allow_multiple=True)
    country_result = resolve_lookup_field(data, 'country', factory.get_country_repository(user_id))
    region_result = resolve_lookup_field(data, 'region', factory.get_region_repository(user_id), allow_multiple=True, country_id=country_result['id'])
    
    # Handle decaf method
    decaf_method_result = {'item': None, 'id': None, 'name': None}
    if data.get('decaf') and (data.get('decaf_method') or data.get('decaf_method_id')):
        decaf_method_result = resolve_lookup_field(data, 'decaf_method', factory.get_decaf_method_repository(user_id))
    
    # Create product data - only store ID fields per schema
    # Generate default product_name if not provided
    product_name = data.get('product_name')
    if not product_name:
        # Generate a name from roaster and bean type if available
        roaster_name = roaster_result.get('name', 'Unknown Roaster')
        bean_type_names = bean_type_result.get('names', [])
        if bean_type_names:
            product_name = f"{roaster_name} {' '.join(bean_type_names)}"
        else:
            product_name = f"{roaster_name} Coffee"
    
    product_data = {
        'roaster_id': roaster_result['id'],
        'bean_type_id': bean_type_result['ids'],
        'country_id': country_result['id'],
        'region_id': region_result['ids'],
        'product_name': product_name,
        'roast_type': safe_int(data.get('roast_type')),
        'description': data.get('description'),
        'url': data.get('url'),
        'image_url': data.get('image_url'),
        'decaf': data.get('decaf', False),
        'decaf_method_id': decaf_method_result['id'],
        'rating': safe_float(data.get('rating')),
        'bean_process': data.get('bean_process'),
        'notes': data.get('notes')
    }
    
    product = factory.get_product_repository(user_id).create(product_data)
    enriched_product = enrich_product_with_lookups(product, factory, user_id)
    return jsonify(enriched_product), 201


@products_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    data = request.json
    
    # Check if product exists
    product_repo = factory.get_product_repository(user_id)
    existing_product = product_repo.find_by_id(product_id)
    if not existing_product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Validate required fields
    if not data.get('roaster') and not data.get('roaster_id') and not data.get('roaster_name'):
        return jsonify({'error': 'Roaster is required'}), 400
    
    # Resolve lookup fields using new helper
    roaster_result = resolve_lookup_field(data, 'roaster', factory.get_roaster_repository(user_id))
    if not roaster_result['item']:
        return jsonify({'error': 'Invalid roaster'}), 400
    
    bean_type_result = resolve_lookup_field(data, 'bean_type', factory.get_bean_type_repository(user_id), allow_multiple=True)
    country_result = resolve_lookup_field(data, 'country', factory.get_country_repository(user_id))
    region_result = resolve_lookup_field(data, 'region', factory.get_region_repository(user_id), allow_multiple=True, country_id=country_result['id'])
    
    # Handle decaf method
    decaf_method_result = {'item': None, 'id': None, 'name': None}
    if data.get('decaf') and (data.get('decaf_method') or data.get('decaf_method_id')):
        decaf_method_result = resolve_lookup_field(data, 'decaf_method', factory.get_decaf_method_repository(user_id))
    
    # Update product data - only store ID fields per schema
    product_data = {
        'roaster_id': roaster_result['id'],
        'bean_type_id': bean_type_result['ids'],
        'country_id': country_result['id'],
        'region_id': region_result['ids'],
        'product_name': data.get('product_name'),
        'roast_type': safe_int(data.get('roast_type')),
        'description': data.get('description'),
        'url': data.get('url'),
        'image_url': data.get('image_url'),
        'decaf': data.get('decaf', False),
        'decaf_method_id': decaf_method_result['id'],
        'rating': safe_float(data.get('rating')),
        'bean_process': data.get('bean_process'),
        'notes': data.get('notes')
    }
    
    product = product_repo.update(product_id, product_data)
    enriched_product = enrich_product_with_lookups(product, factory, user_id)
    return jsonify(enriched_product)


@products_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product and all related batches and brew sessions."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    
    # Check if product exists
    product_repo = factory.get_product_repository(user_id)
    product = product_repo.find_by_id(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Delete related brew sessions and batches
    batch_repo = factory.get_batch_repository(user_id)
    brew_session_repo = factory.get_brew_session_repository(user_id)
    
    brew_session_repo.delete_by_product(product_id)
    batch_repo.delete_by_product(product_id)
    
    # Delete product
    product_repo.delete(product_id)
    
    return '', 204


@products_bp.route('/products/<int:product_id>/batches', methods=['GET', 'POST'])
def handle_product_batches(product_id):
    """Get all batches for a specific product or create a new batch."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    
    # Check if product exists
    product_repo = factory.get_product_repository(user_id)
    product = product_repo.find_by_id(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    if request.method == 'GET':
        # Check if smart ordering is requested
        smart_order = request.args.get('smart_order', 'false').lower() == 'true'
        batch_repo = factory.get_batch_repository(user_id)
        
        if smart_order:
            batches = batch_repo.find_by_product_with_smart_ordering(product_id)
        else:
            batches = batch_repo.find_by_product(product_id)
        
        # Enrich with product information and calculate price per cup
        enriched_product = enrich_product_with_lookups(product, factory, user_id)
        for batch in batches:
            roaster_name = enriched_product.get('roaster', {}).get('name', 'N/A') if enriched_product.get('roaster') else 'N/A'
            bean_type_names = ', '.join([bt.get('name', 'N/A') for bt in enriched_product.get('bean_type', [])]) if enriched_product.get('bean_type') else 'N/A'
            batch['product_name'] = f"{roaster_name} - {bean_type_names}"
            batch['price_per_cup'] = calculate_price_per_cup(batch.get('price'), batch.get('amount_grams'))
        
        return jsonify(batches)
    
    elif request.method == 'POST':
        """Create a new batch for the specified product."""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract fields from request
        roast_date = data.get('roast_date')
        if roast_date == '' or roast_date is None:  # Handle empty string or missing field
            # Default to today's date if not provided
            roast_date = datetime.now().strftime('%Y-%m-%d')
            
        purchase_date = data.get('purchase_date')
        if purchase_date == '':  # Handle empty string
            purchase_date = None
        
        batch_data = {
            'product_id': product_id,  # Use product_id from URL
            'roast_date': roast_date,
            'purchase_date': purchase_date,
            'amount_grams': safe_float(data.get('amount_grams')),
            'price': safe_float(data.get('price')),
            'seller': data.get('seller'),
            'notes': data.get('notes'),
            'rating': safe_float(data.get('rating')),
            'is_active': data.get('is_active', True)  # Default to active
        }
        
        batch_repo = factory.get_batch_repository(user_id)
        batch = batch_repo.create(batch_data)
        
        # Enrich with product information and calculate price per cup
        enriched_product = enrich_product_with_lookups(product, factory, user_id)
        roaster_name = enriched_product.get('roaster', {}).get('name', 'N/A') if enriched_product.get('roaster') else 'N/A'
        bean_type_names = ', '.join([bt.get('name', 'N/A') for bt in enriched_product.get('bean_type', [])]) if enriched_product.get('bean_type') else 'N/A'
        batch['product_name'] = f"{roaster_name} - {bean_type_names}"
        batch['price_per_cup'] = calculate_price_per_cup(batch.get('price'), batch.get('amount_grams'))
        
        return jsonify(batch), 201


@products_bp.route('/products/<int:product_id>/brew_recommendations', methods=['GET'])
def get_brew_recommendations(product_id):
    """Get brew recommendations for a specific product."""
    # Get and validate user_id
    user_id = get_user_id_from_request()
    is_valid, error_msg = validate_user_id(user_id)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    factory = get_repository_factory()
    
    # Check if product exists
    product_repo = factory.get_product_repository(user_id)
    product = product_repo.find_by_id(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Get optional method filter
    method = request.args.get('method')
    
    # Create recommendation service and get recommendations
    brew_session_repo = factory.get_brew_session_repository(user_id)
    brew_method_repo = factory.get_brew_method_repository(user_id)
    rec_service = BrewRecommendationService(brew_session_repo, factory, brew_method_repo)
    recommendations = rec_service.get_recommendations(product_id, method)
    
    return jsonify(recommendations)