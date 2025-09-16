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
        app.logger.info(f"🔄 Initializing migration system for data directory: {app.config['DATA_DIR']}")

        # Check if data directory exists
        if not os.path.exists(app.config['DATA_DIR']):
            app.logger.warning(f"⚠️  Data directory does not exist: {app.config['DATA_DIR']}")
        else:
            app.logger.info(f"✅ Data directory found: {app.config['DATA_DIR']}")

        migration_manager = get_migration_manager(app.config['DATA_DIR'])

        # Get schema file path and check if it exists
        schema_file = migration_manager.schema_file
        app.logger.info(f"📋 Schema file location: {schema_file}")
        if not os.path.exists(schema_file):
            app.logger.warning(f"⚠️  Schema file not found: {schema_file}")

        current_schema = migration_manager.get_current_schema_version()
        current_data = migration_manager.get_data_version()
        app.logger.info(f"📊 Schema version: {current_schema}, Data version: {current_data}")

        # Check available migrations
        available_migrations = list(migration_manager.migrations.keys())
        app.logger.info(f"🔧 Available migrations: {available_migrations}")

        if migration_manager.needs_migration():
            app.logger.info(f"🚀 Data migration required: {current_data} -> {current_schema}")

            # Check if specific migration exists
            migration_key = f"{current_data}->{current_schema}"
            if migration_key in migration_manager.migrations:
                app.logger.info(f"✅ Migration found: {migration_key}")
            else:
                app.logger.error(f"❌ Migration not found: {migration_key}")

            app.logger.info("💾 Creating backup and running migrations...")
            backup_dir = migration_manager.backup_data()
            app.logger.info(f"📁 Data backed up to: {backup_dir}")

            if migration_manager.run_migrations():
                app.logger.info("✅ Data migration completed successfully")
            else:
                app.logger.error("❌ Data migration failed - check logs for details")
        else:
            app.logger.info("✅ Data schema is up to date - no migration needed")
    except Exception as e:
        app.logger.error(f"Error during migration check: {str(e)}")
        app.logger.error("Application will continue with potentially outdated data schema")
    
    # Register blueprints
    from .main import api
    app.register_blueprint(api)
    
    return app