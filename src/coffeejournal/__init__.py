from flask import Flask
from flask_cors import CORS
import os
import logging
from .repositories.factory import init_repository_factory
from .migrations import get_migration_manager


def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load config
    if test_config is None:
        # Load the instance config, if it exists, when not testing
        # Use DATA_DIR environment variable or default to test_data
        default_data_dir = os.environ.get('DATA_DIR', 'test_data')
        # Convert relative paths to absolute paths based on project root
        if not os.path.isabs(default_data_dir):
            # Go up from src/coffeejournal to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            default_data_dir = os.path.join(project_root, default_data_dir)
        
        app.config.from_mapping(
            SECRET_KEY='dev',
            DATA_DIR=default_data_dir
        )
        # Note: No longer using Flask instance config files
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)
    
    # Ensure the data directory exists
    try:
        os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    except OSError:
        pass
    
    # Initialize CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize repository factory
    init_repository_factory(
        storage_type='json',
        data_dir=app.config['DATA_DIR']
    )
    
    # Check and run migrations if needed
    try:
        app.logger.info(f"Initializing migration system for data directory: {app.config['DATA_DIR']}")
        migration_manager = get_migration_manager(app.config['DATA_DIR'])
        
        current_schema = migration_manager.get_current_schema_version()
        current_data = migration_manager.get_data_version()
        app.logger.info(f"Schema version: {current_schema}, Data version: {current_data}")
        
        if migration_manager.needs_migration():
            app.logger.info(f"Data migration required: {current_data} -> {current_schema}")
            app.logger.info("Creating backup and running migrations...")
            backup_dir = migration_manager.backup_data()
            app.logger.info(f"Data backed up to: {backup_dir}")
            
            if migration_manager.run_migrations():
                app.logger.info("Data migration completed successfully")
            else:
                app.logger.error("Data migration failed - check logs for details")
        else:
            app.logger.info("Data schema is up to date - no migration needed")
    except Exception as e:
        app.logger.error(f"Error during migration check: {str(e)}")
        app.logger.error("Application will continue with potentially outdated data schema")
    
    # Register blueprints
    from .main import api
    app.register_blueprint(api)
    
    return app