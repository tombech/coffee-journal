"""
Lookup management module for Coffee Journal.

This module contains Flask blueprints for managing all lookup tables
used in the coffee journal application, organized by category.
"""

from flask import Blueprint
from .common import validate_lookup_data, validate_user_context
from .basic_lookups import basic_lookups_bp
from .equipment import equipment_bp
from .espresso_equipment import espresso_equipment_bp


def create_lookups_blueprint():
    """Create and configure the main lookups blueprint."""
    
    # Create main lookups blueprint
    lookups = Blueprint('lookups', __name__)
    
    # Register sub-blueprints
    lookups.register_blueprint(basic_lookups_bp)
    lookups.register_blueprint(equipment_bp) 
    lookups.register_blueprint(espresso_equipment_bp)
    
    return lookups


# For backward compatibility
lookups = create_lookups_blueprint()