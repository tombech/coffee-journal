#!/usr/bin/env python3
"""
CLI tool for managing Coffee Journal data migrations.

Usage:
    python migrate_data.py --check              # Check if migration is needed
    python migrate_data.py --migrate            # Run migrations
    python migrate_data.py --force-version 1.1  # Set data to specific version
    python migrate_data.py --backup             # Create backup only
"""

import argparse
import os
import sys

# Add src to path to import coffeejournal modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from coffeejournal.migrations import get_migration_manager

def main():
    parser = argparse.ArgumentParser(description='Coffee Journal Data Migration Tool')
    parser.add_argument('--data-dir', default='test_data', help='Data directory path')
    parser.add_argument('--check', action='store_true', help='Check if migration is needed')
    parser.add_argument('--migrate', action='store_true', help='Run migrations')
    parser.add_argument('--backup', action='store_true', help='Create backup only')
    parser.add_argument('--force-version', help='Force set data to specific version')
    
    args = parser.parse_args()
    
    # Convert relative paths to absolute
    if not os.path.isabs(args.data_dir):
        args.data_dir = os.path.join(os.getcwd(), args.data_dir)
    
    migration_manager = get_migration_manager(args.data_dir)
    
    if args.check:
        print(f"Schema version: {migration_manager.get_current_schema_version()}")
        print(f"Data version: {migration_manager.get_data_version()}")
        if migration_manager.needs_migration():
            print("⚠️  Migration needed")
            sys.exit(1)
        else:
            print("✅ Data is up to date")
            sys.exit(0)
    
    elif args.backup:
        backup_dir = migration_manager.backup_data()
        print(f"✅ Backup created: {backup_dir}")
    
    elif args.migrate:
        if not migration_manager.needs_migration():
            print("✅ Data is already up to date")
            sys.exit(0)
        
        print("Creating backup before migration...")
        backup_dir = migration_manager.backup_data()
        print(f"Backup created: {backup_dir}")
        
        print("Running migrations...")
        if migration_manager.run_migrations():
            print("✅ Migration completed successfully")
        else:
            print("❌ Migration failed - check logs")
            print(f"Restore from backup: {backup_dir}")
            sys.exit(1)
    
    elif args.force_version:
        print(f"Setting data version to {args.force_version}")
        migration_manager.set_data_version(args.force_version)
        print("✅ Version updated")
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()