"""
Data migration framework for Coffee Journal schema versioning.
"""

import json
import os
import logging
from typing import Dict, Any, List, Callable
from packaging import version

logger = logging.getLogger(__name__)

class MigrationManager:
    """Manages data migrations between schema versions."""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.schema_file = os.path.join(os.getcwd(), 'schema_version.json')
        self.migrations: Dict[str, Callable] = {}
        
    def register_migration(self, from_version: str, to_version: str):
        """Decorator to register migration functions."""
        def decorator(func: Callable):
            self.migrations[f"{from_version}->{to_version}"] = func
            return func
        return decorator
    
    def get_current_schema_version(self) -> str:
        """Get the current schema version from schema_version.json."""
        if not os.path.exists(self.schema_file):
            return "0.0"  # No schema file means pre-versioning
            
        with open(self.schema_file, 'r') as f:
            schema_data = json.load(f)
            return schema_data.get('schema_version', '0.0')
    
    def get_data_version(self) -> str:
        """Get the version of data files (from data_version.json if exists)."""
        data_version_file = os.path.join(self.data_dir, 'data_version.json')
        if not os.path.exists(data_version_file):
            return "1.0"  # Assume current data is v1.0 if no version file
            
        with open(data_version_file, 'r') as f:
            data_info = json.load(f)
            return data_info.get('version', '1.0')
    
    def set_data_version(self, new_version: str):
        """Update the data version file."""
        data_version_file = os.path.join(self.data_dir, 'data_version.json')
        data_info = {
            'version': new_version,
            'migrated_date': '2025-07-11',
            'description': f'Data migrated to version {new_version}'
        }
        
        with open(data_version_file, 'w') as f:
            json.dump(data_info, f, indent=2)
    
    def needs_migration(self) -> bool:
        """Check if data migration is needed."""
        schema_version = self.get_current_schema_version()
        data_version = self.get_data_version()
        
        return version.parse(data_version) < version.parse(schema_version)
    
    def get_migration_path(self, from_version: str, to_version: str) -> List[str]:
        """Get the sequence of migrations needed to go from one version to another."""
        # For now, assume direct migrations only
        # This could be enhanced to handle multi-step migrations
        migration_key = f"{from_version}->{to_version}"
        if migration_key in self.migrations:
            return [migration_key]
        
        # No migration path found
        logger.warning(f"No migration path found from {from_version} to {to_version}")
        return []
    
    def run_migrations(self) -> bool:
        """Run all necessary migrations to bring data up to current schema version."""
        if not self.needs_migration():
            logger.info("Data is up to date, no migrations needed")
            return True
        
        data_version = self.get_data_version()
        schema_version = self.get_current_schema_version()
        
        logger.info(f"Starting migration process:")
        logger.info(f"  Current data version: {data_version}")
        logger.info(f"  Target schema version: {schema_version}")
        logger.info(f"  Data directory: {self.data_dir}")
        
        migration_path = self.get_migration_path(data_version, schema_version)
        
        if not migration_path:
            logger.error(f"No migration path available from {data_version} to {schema_version}")
            logger.error(f"Available migrations: {list(self.migrations.keys())}")
            return False
        
        logger.info(f"Migration path: {' -> '.join(migration_path)}")
        
        # Create backup only for certain migrations (not for safe ones like v1.3->v1.4)
        should_backup = not (data_version == "1.3" and schema_version == "1.4")
        if should_backup:
            try:
                backup_dir = self.backup_data()
                logger.info(f"Data backed up to: {backup_dir}")
            except Exception as e:
                logger.warning(f"Backup failed, but continuing migration: {e}")
        
        try:
            for i, migration_key in enumerate(migration_path, 1):
                logger.info(f"Running migration {i}/{len(migration_path)}: {migration_key}")
                migration_func = self.migrations[migration_key]
                migration_func(self.data_dir)
                logger.info(f"Migration {migration_key} completed successfully")
            
            # Update data version
            logger.info(f"Updating data version from {data_version} to {schema_version}")
            self.set_data_version(schema_version)
            logger.info(f"Migration process completed successfully to version {schema_version}")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed during {migration_key}: {str(e)}")
            logger.error(f"Migration stack trace:", exc_info=True)
            return False
    
    def backup_data(self) -> str:
        """Create a backup of current data before migration."""
        import shutil
        import datetime
        import os
        
        logger.info("Creating data backup before migration...")
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Create backup directory inside data directory to avoid permission issues
        backup_dir = os.path.join(self.data_dir, f"backup_{timestamp}")
        
        logger.info(f"Backup directory: {backup_dir}")
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        # Copy all files except existing backup directories
        files_backed_up = 0
        for item in os.listdir(self.data_dir):
            if item.startswith('backup_'):
                logger.debug(f"Skipping existing backup directory: {item}")
                continue  # Skip existing backup directories
            
            src_path = os.path.join(self.data_dir, item)
            dst_path = os.path.join(backup_dir, item)
            
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)
                files_backed_up += 1
                logger.debug(f"Backed up file: {item}")
            elif os.path.isdir(src_path):
                try:
                    shutil.copytree(src_path, dst_path)
                    files_backed_up += 1
                    logger.debug(f"Backed up directory: {item}")
                except FileExistsError:
                    logger.debug(f"Backup directory already exists, skipping: {item}")
                except Exception as e:
                    logger.warning(f"Could not backup directory {item}: {e}")
        
        logger.info(f"Data backup completed: {files_backed_up} items backed up to {backup_dir}")
        return backup_dir


# Global migration manager instance
migration_manager = None

def get_migration_manager(data_dir: str) -> MigrationManager:
    """Get or create the global migration manager instance."""
    global migration_manager
    if migration_manager is None:
        migration_manager = MigrationManager(data_dir)
        # Auto-load migration modules
        _load_migration_modules(migration_manager)
    return migration_manager

def _load_migration_modules(manager: MigrationManager):
    """Load all migration modules to register their migrations."""
    import importlib
    import pkgutil
    import sys
    
    # Import all migration modules in this package
    current_package = __name__
    
    try:
        # Load v1_0_to_v1_1 migration
        from . import v1_0_to_v1_1
        # The migration should auto-register when imported
        
        # Register the migration manually if needed
        if "1.0->1.1" not in manager.migrations:
            manager.migrations["1.0->1.1"] = v1_0_to_v1_1.migrate_1_0_to_1_1
        
        # Load v1_1_to_v1_2 migration
        from . import v1_1_to_v1_2
        if "1.1->1.2" not in manager.migrations:
            manager.migrations["1.1->1.2"] = v1_1_to_v1_2.migrate_1_1_to_1_2
        
        # Load v1_2_to_v1_3 migration
        from . import v1_2_to_v1_3
        if "1.2->1.3" not in manager.migrations:
            manager.migrations["1.2->1.3"] = v1_2_to_v1_3.migrate_1_2_to_1_3
        
        # Load v1_3_to_v1_4 migration (Espresso Support)
        from . import migration_1_3_to_1_4
        if "1.3->1.4" not in manager.migrations:
            manager.migrations["1.3->1.4"] = migration_1_3_to_1_4.migrate_v1_3_to_v1_4
            
    except ImportError as e:
        logger.warning(f"Could not load migration module: {e}")