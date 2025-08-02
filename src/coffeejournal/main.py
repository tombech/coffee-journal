"""
Main API module for Coffee Journal application.

This module now serves as a simple orchestration layer that imports and 
registers all the API blueprints from the api package.
"""

from .api import create_api_blueprint

# Create the main API blueprint with all sub-blueprints registered
api = create_api_blueprint()