from flask import Flask
from flask_cors import CORS
import os
import logging
from logging.handlers import RotatingFileHandler
from .repositories.factory import init_repository_factory
from .migrations import get_migration_manager


def setup_logging(app, data_dir):
    """Set up logging with both file and console handlers."""
    # Create logs directory
    logs_dir = os.path.join(data_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    # Set up the main application logger
    app.logger.setLevel(logging.INFO)

    # Clear any existing handlers
    app.logger.handlers.clear()

    # Console handler for Docker/development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    app.logger.addHandler(console_handler)

    # File handler with rotation
    log_file = os.path.join(logs_dir, 'coffeejournal.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    app.logger.addHandler(file_handler)

    # Set up migration logger
    migration_logger = logging.getLogger('coffeejournal.migrations')
    migration_logger.setLevel(logging.INFO)
    # Only add handlers if not already present (avoid duplication)
    if not migration_logger.handlers:
        migration_logger.addHandler(console_handler)
        migration_logger.addHandler(file_handler)
    migration_logger.propagate = False  # Prevent duplicate logging

    app.logger.info(f"Logging initialized - Console and file: {log_file}")
    return migration_logger


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

    # Set up logging
    migration_logger = setup_logging(app, app.config['DATA_DIR'])

    # Initialize repository factory
    init_repository_factory(
        storage_type='json',
        data_dir=app.config['DATA_DIR']
    )
    
    # Check and run migrations if needed
    try:
        migration_logger.info(f"🔄 Initializing migration system for data directory: {app.config['DATA_DIR']}")

        # Check if data directory exists
        if not os.path.exists(app.config['DATA_DIR']):
            migration_logger.warning(f"⚠️  Data directory does not exist: {app.config['DATA_DIR']}")
        else:
            migration_logger.info(f"✅ Data directory found: {app.config['DATA_DIR']}")

        migration_manager = get_migration_manager(app.config['DATA_DIR'])

        # Get schema file path and check if it exists
        schema_file = migration_manager.schema_file
        migration_logger.info(f"📋 Schema file location: {schema_file}")
        if not os.path.exists(schema_file):
            migration_logger.warning(f"⚠️  Schema file not found: {schema_file}")
        else:
            # Read and log schema file contents
            try:
                import json
                with open(schema_file, 'r') as f:
                    schema_content = json.load(f)
                migration_logger.info(f"📄 Schema file content version: {schema_content.get('schema_version', 'unknown')}")
            except Exception as e:
                migration_logger.warning(f"⚠️  Could not read schema file: {e}")

        current_schema = migration_manager.get_current_schema_version()
        current_data = migration_manager.get_data_version()
        migration_logger.info(f"📊 Schema version: {current_schema}, Data version: {current_data}")

        # Check available migrations
        available_migrations = list(migration_manager.migrations.keys())
        migration_logger.info(f"🔧 Available migrations: {available_migrations}")

        # Log specific migration we're looking for
        expected_migration = f"{current_data}->{current_schema}" if current_data != current_schema else "none needed"
        migration_logger.info(f"🎯 Expected migration: {expected_migration}")

        # Check if 1.5->1.6 migration is registered
        if "1.5->1.6" not in available_migrations:
            migration_logger.warning(f"⚠️  1.5->1.6 migration not found in registered migrations!")

        if migration_manager.needs_migration():
            migration_logger.info(f"🚀 Data migration required: {current_data} -> {current_schema}")

            # Check if specific migration exists
            migration_key = f"{current_data}->{current_schema}"
            if migration_key in migration_manager.migrations:
                migration_logger.info(f"✅ Migration found: {migration_key}")
            else:
                migration_logger.error(f"❌ Migration not found: {migration_key}")

            migration_logger.info("💾 Creating backup and running migrations...")
            backup_dir = migration_manager.backup_data()
            migration_logger.info(f"📁 Data backed up to: {backup_dir}")

            if migration_manager.run_migrations():
                migration_logger.info("✅ Data migration completed successfully")

                # Invalidate all repository caches to ensure updated schemas are used
                from .repositories.factory import get_repository_factory
                factory = get_repository_factory()
                factory.invalidate_all_caches()
                migration_logger.info("🔄 Repository caches invalidated after migration")
            else:
                migration_logger.error("❌ Data migration failed - check logs for details")
        else:
            migration_logger.info("✅ Data schema is up to date - no migration needed")
    except Exception as e:
        migration_logger.error(f"❌ Error during migration check: {str(e)}")
        migration_logger.error("Application will continue with potentially outdated data schema")
    
    # Register blueprints
    from .main import api
    app.register_blueprint(api)
    
    return app