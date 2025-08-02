"""
API package for Coffee Journal application.

This package contains all Flask blueprints for the REST API endpoints,
organized by domain:
- utils: Shared utilities and helper functions
- lookups: All lookup table endpoints (roasters, bean_types, etc.)
- products: Coffee product management
- batches: Coffee batch management  
- brew_sessions: Brewing session tracking
"""

from flask import Blueprint

def create_api_blueprint():
    """Create and configure the main API blueprint."""
    from ..lookups import lookups  # lookups.py is in the main package
    from .products import products_bp
    from .batches import batches_bp
    
    # Create main API blueprint
    api = Blueprint('api', __name__, url_prefix='/api')
    
    # Register sub-blueprints 
    api.register_blueprint(lookups)
    api.register_blueprint(products_bp)
    api.register_blueprint(batches_bp)
    
    return api