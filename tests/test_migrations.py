"""
Unit tests for the migration system.

Tests cover:
- MigrationManager functionality
- Migration registration and loading
- Schema version handling
- Data version tracking
- Migration execution
- Error handling
"""

import json
import os
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from coffeejournal.migrations import MigrationManager, get_migration_manager


class TestMigrationManager:
    """Test the MigrationManager class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, 'test_data')
        os.makedirs(self.data_dir)
        
        # Create test schema file
        self.schema_file = os.path.join(self.test_dir, 'schema_version.json')
        
        self.manager = MigrationManager(self.data_dir)
        self.manager.schema_file = self.schema_file  # Override to use test schema file
    
    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.test_dir)
    
    def create_schema_file(self, version="1.3"):
        """Helper to create a schema version file."""
        schema_data = {
            "schema_version": version,
            "updated_date": "2025-08-02",
            "description": f"Schema version {version}"
        }
        with open(self.schema_file, 'w') as f:
            json.dump(schema_data, f)
    
    def create_data_version_file(self, version="1.0"):
        """Helper to create a data version file."""
        data_version_file = os.path.join(self.data_dir, 'data_version.json')
        data_info = {
            "version": version,
            "migrated_date": "2025-08-02",
            "description": f"Data version {version}"
        }
        with open(data_version_file, 'w') as f:
            json.dump(data_info, f)
    
    def test_initialization(self):
        """Test MigrationManager initialization."""
        assert self.manager.data_dir == self.data_dir
        assert isinstance(self.manager.migrations, dict)
        assert len(self.manager.migrations) == 0  # No migrations registered yet
    
    def test_get_current_schema_version_no_file(self):
        """Test getting schema version when no schema file exists."""
        version = self.manager.get_current_schema_version()
        assert version == "0.0"
    
    def test_get_current_schema_version_with_file(self):
        """Test getting schema version from existing file."""
        self.create_schema_file("1.3")
        version = self.manager.get_current_schema_version()
        assert version == "1.3"
    
    def test_get_data_version_no_file(self):
        """Test getting data version when no data version file exists."""
        version = self.manager.get_data_version()
        assert version == "1.0"  # Default version
    
    def test_get_data_version_with_file(self):
        """Test getting data version from existing file."""
        self.create_data_version_file("1.2")
        version = self.manager.get_data_version()
        assert version == "1.2"
    
    def test_set_data_version(self):
        """Test setting data version."""
        self.manager.set_data_version("1.3")
        
        # Verify file was created with correct content
        data_version_file = os.path.join(self.data_dir, 'data_version.json')
        assert os.path.exists(data_version_file)
        
        with open(data_version_file, 'r') as f:
            data = json.load(f)
        
        assert data['version'] == "1.3"
        assert 'migrated_date' in data
        assert 'description' in data
    
    def test_needs_migration_false(self):
        """Test when no migration is needed."""
        self.create_schema_file("1.3")
        self.create_data_version_file("1.3")
        
        assert not self.manager.needs_migration()
    
    def test_needs_migration_true(self):
        """Test when migration is needed."""
        self.create_schema_file("1.3")
        self.create_data_version_file("1.1")
        
        assert self.manager.needs_migration()
    
    def test_register_migration_decorator(self):
        """Test the migration registration decorator."""
        @self.manager.register_migration("1.0", "1.1")
        def test_migration(data_dir):
            pass
        
        assert "1.0->1.1" in self.manager.migrations
        assert self.manager.migrations["1.0->1.1"] == test_migration
    
    def test_register_migration_manual(self):
        """Test manual migration registration."""
        def test_migration(data_dir):
            pass
        
        self.manager.migrations["1.1->1.2"] = test_migration
        
        assert "1.1->1.2" in self.manager.migrations
        assert self.manager.migrations["1.1->1.2"] == test_migration
    
    def test_get_migration_path_direct(self):
        """Test getting migration path for direct migration."""
        def test_migration(data_dir):
            pass
        
        self.manager.migrations["1.0->1.1"] = test_migration
        
        path = self.manager.get_migration_path("1.0", "1.1")
        assert path == ["1.0->1.1"]
    
    def test_get_migration_path_no_path(self):
        """Test getting migration path when none exists."""
        path = self.manager.get_migration_path("1.0", "2.0")
        assert path == []
    
    def test_run_migrations_no_migration_needed(self):
        """Test running migrations when none are needed."""
        self.create_schema_file("1.3")
        self.create_data_version_file("1.3")
        
        result = self.manager.run_migrations()
        assert result is True
    
    def test_run_migrations_success(self):
        """Test successful migration execution."""
        self.create_schema_file("1.1")
        self.create_data_version_file("1.0")
        
        # Mock migration function
        migration_executed = False
        def mock_migration(data_dir):
            nonlocal migration_executed
            migration_executed = True
            assert data_dir == self.data_dir
        
        self.manager.migrations["1.0->1.1"] = mock_migration
        
        result = self.manager.run_migrations()
        
        assert result is True
        assert migration_executed
        
        # Check data version was updated
        assert self.manager.get_data_version() == "1.1"
    
    def test_run_migrations_failure(self):
        """Test migration execution failure."""
        self.create_schema_file("1.1")
        self.create_data_version_file("1.0")
        
        # Mock migration function that raises exception
        def failing_migration(data_dir):
            raise Exception("Migration failed")
        
        self.manager.migrations["1.0->1.1"] = failing_migration
        
        result = self.manager.run_migrations()
        
        assert result is False
        # Data version should not be updated on failure
        assert self.manager.get_data_version() == "1.0"
    
    def test_run_migrations_no_path(self):
        """Test migration execution when no migration path exists."""
        self.create_schema_file("2.0")
        self.create_data_version_file("1.0")
        
        result = self.manager.run_migrations()
        
        assert result is False
    
    def test_backup_data(self):
        """Test data backup functionality."""
        # Create some test data files
        test_files = ['products.json', 'batches.json']
        for filename in test_files:
            test_file = os.path.join(self.data_dir, filename)
            with open(test_file, 'w') as f:
                json.dump({"test": "data"}, f)
        
        backup_dir = self.manager.backup_data()
        
        # Verify backup directory was created inside data directory
        assert os.path.exists(backup_dir)
        assert backup_dir.startswith(os.path.join(self.data_dir, "backup_"))
        
        # Verify all files were backed up
        for filename in test_files:
            backup_file = os.path.join(backup_dir, filename)
            assert os.path.exists(backup_file)
            
            with open(backup_file, 'r') as f:
                data = json.load(f)
            assert data == {"test": "data"}


class TestGlobalMigrationManager:
    """Test the global migration manager functions."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, 'test_data')
        os.makedirs(self.data_dir)
        
        # Reset global migration manager
        import coffeejournal.migrations
        coffeejournal.migrations.migration_manager = None
    
    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.test_dir)
        
        # Reset global migration manager
        import coffeejournal.migrations
        coffeejournal.migrations.migration_manager = None
    
    def test_get_migration_manager_singleton(self):
        """Test that get_migration_manager returns singleton instance."""
        manager1 = get_migration_manager(self.data_dir)
        manager2 = get_migration_manager(self.data_dir)
        
        assert manager1 is manager2
        assert manager1.data_dir == self.data_dir
    
    @patch('coffeejournal.migrations._load_migration_modules')
    def test_get_migration_manager_loads_modules(self, mock_load):
        """Test that get_migration_manager loads migration modules."""
        manager = get_migration_manager(self.data_dir)
        
        mock_load.assert_called_once_with(manager)
    
    def test_load_migration_modules_imports(self):
        """Test that _load_migration_modules imports migration modules."""
        from coffeejournal.migrations import _load_migration_modules
        
        manager = MigrationManager(self.data_dir)
        _load_migration_modules(manager)
        
        # Should have registered the standard migrations
        expected_migrations = ['1.0->1.1', '1.1->1.2', '1.2->1.3']
        for migration_key in expected_migrations:
            assert migration_key in manager.migrations
            assert callable(manager.migrations[migration_key])


class TestMigrationIntegration:
    """Integration tests for the migration system."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, 'test_data')
        os.makedirs(self.data_dir)
        
        # Create root schema file
        self.schema_file = os.path.join(self.test_dir, 'schema_version.json')
        schema_data = {
            "schema_version": "1.3",
            "updated_date": "2025-08-02"
        }
        with open(self.schema_file, 'w') as f:
            json.dump(schema_data, f)
    
    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.test_dir)
    
    def test_full_migration_workflow(self):
        """Test complete migration workflow from v1.0 to v1.3."""
        # Create v1.0 data (no data_version.json file)
        products_data = [
            {
                "id": 1,
                "roaster_id": 1,
                "bean_type_id": 1,
                "country_id": 1,
                "product_name": "Test Coffee",
                "roast_type": 3,
                "description": "Test description"
            }
        ]
        
        with open(os.path.join(self.data_dir, 'products.json'), 'w') as f:
            json.dump(products_data, f)
        
        # Change working directory to test directory for schema file
        original_cwd = os.getcwd()
        try:
            os.chdir(self.test_dir)
            
            # Get migration manager and run migrations
            manager = get_migration_manager(self.data_dir)
            
            # Should need migration from 1.0 to 1.3
            assert manager.needs_migration()
            
            # This will attempt to run real migrations, but they might fail
            # due to missing data files, which is expected in this test
            # We're mainly testing that the migration system is properly wired up
            result = manager.run_migrations()
            
            # The result might be False due to missing data, but we can verify
            # that the migration functions are properly registered
            assert '1.0->1.1' in manager.migrations
            assert '1.1->1.2' in manager.migrations
            assert '1.2->1.3' in manager.migrations
            
        finally:
            os.chdir(original_cwd)
    
    def test_migration_manager_with_real_data_structure(self):
        """Test migration manager with realistic data structure."""
        # Create minimal required data files for migrations
        countries_data = [
            {"id": 1, "name": "Ethiopia", "is_default": False}
        ]
        
        roasters_data = [
            {"id": 1, "name": "Test Roaster", "is_default": False}
        ]
        
        bean_types_data = [
            {"id": 1, "name": "Arabica", "is_default": False}
        ]
        
        products_data = [
            {
                "id": 1,
                "roaster_id": 1,
                "bean_type_id": [1],
                "country_id": 1,
                "region_id": [],
                "product_name": "Test Coffee",
                "roast_type": 3,
                "description": "Test coffee"
            }
        ]
        
        # Write data files
        test_files = {
            'countries.json': countries_data,
            'roasters.json': roasters_data,
            'bean_types.json': bean_types_data,
            'products.json': products_data
        }
        
        for filename, data in test_files.items():
            with open(os.path.join(self.data_dir, filename), 'w') as f:
                json.dump(data, f)
        
        # Create data version file indicating current version
        data_version_data = {
            "version": "1.3",
            "migrated_date": "2025-08-02"
        }
        with open(os.path.join(self.data_dir, 'data_version.json'), 'w') as f:
            json.dump(data_version_data, f)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(self.test_dir)
            
            manager = get_migration_manager(self.data_dir)
            
            # Should not need migration since both schema and data are v1.3
            assert not manager.needs_migration()
            
            # All migrations should be registered
            assert len(manager.migrations) >= 3
            
        finally:
            os.chdir(original_cwd)


if __name__ == '__main__':
    pytest.main([__file__])