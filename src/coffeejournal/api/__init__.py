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
    from ..lookups import create_lookups_blueprint  # New modular lookups system
    from .products import products_bp
    from .batches import batches_bp
    from .shots import shots_bp
    from .shot_sessions import shot_sessions_bp
    from .stats import create_stats_blueprint
    
    # Create main API blueprint
    api = Blueprint('api', __name__, url_prefix='/api')
    
    # Register sub-blueprints 
    api.register_blueprint(create_lookups_blueprint())
    api.register_blueprint(products_bp)
    api.register_blueprint(batches_bp)
    api.register_blueprint(shots_bp)
    api.register_blueprint(shot_sessions_bp)
    api.register_blueprint(create_stats_blueprint(), url_prefix='/stats')
    
    return api