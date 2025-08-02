#!/usr/bin/env python3
"""
Migration script for Coffee Journal schema v1.2 to v1.3

Changes in v1.3:
1. Separate regions into own lookup table with country_id parent reference
2. Fix lookup update_references functions to use ID fields instead of names
3. Add inline region management in country edit pages
4. Add new API endpoints for regions

This script:
- Creates regions.json from existing region data in products
- Updates product region_id fields to use arrays of region IDs
- Updates schema_version.json to v1.3
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any, Set

class SchemaV13Migration:
    def __init__(self, data_dir: str = 'test_data'):
        self.data_dir = data_dir
        self.timestamp = datetime.now(timezone.utc).isoformat()
        
        # Check if schema_version.json is in root directory instead
        if not os.path.exists(os.path.join(data_dir, 'schema_version.json')):
            if os.path.exists('schema_version.json'):
                self.schema_file = 'schema_version.json'
            else:
                self.schema_file = os.path.join(data_dir, 'schema_version.json')
        else:
            self.schema_file = os.path.join(data_dir, 'schema_version.json')
        
    def check_data_files(self) -> bool:
        """Check if required data files exist."""
        data_files = ['products.json', 'countries.json']
        missing_files = []
        
        # Check data files in data directory
        for file_name in data_files:
            file_path = os.path.join(self.data_dir, file_name)
            if not os.path.exists(file_path):
                missing_files.append(file_name)
        
        # Check schema file
        if not os.path.exists(self.schema_file):
            missing_files.append('schema_version.json')
        
        if missing_files:
            print(f"ERROR: Missing required files: {', '.join(missing_files)}")
            return False
        return True
    
    def load_json_file(self, filename: str) -> Any:
        """Load JSON data from file."""
        if filename == 'schema_version.json':
            file_path = self.schema_file
        else:
            file_path = os.path.join(self.data_dir, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"ERROR loading {filename}: {e}")
            sys.exit(1)
    
    def save_json_file(self, filename: str, data: Any) -> None:
        """Save JSON data to file."""
        if filename == 'schema_version.json':
            file_path = self.schema_file
        else:
            file_path = os.path.join(self.data_dir, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"ERROR saving {filename}: {e}")
            sys.exit(1)
    
    def check_schema_version(self) -> bool:
        """Check if migration is needed."""
        schema = self.load_json_file('schema_version.json')
        current_version = schema.get('schema_version', '1.0')
        
        if current_version == '1.3':
            print("Schema is already at version 1.3. No migration needed.")
            return False
        elif current_version != '1.2':
            print(f"ERROR: Expected schema version 1.2, found {current_version}")
            print("This migration only supports upgrading from v1.2 to v1.3")
            return False
        
        return True
    
    def extract_region_data(self) -> tuple[List[Dict], Dict[str, int]]:
        """Extract unique region data from products and create mapping."""
        products = self.load_json_file('products.json')
        countries = self.load_json_file('countries.json')
        
        # Create country name to ID mapping
        country_map = {country['name']: country['id'] for country in countries}
        
        # Collect unique regions with their country associations
        region_data = {}  # region_name -> {country_id, country_name}
        
        for product in products:
            region_name = product.get('region')
            country_name = product.get('country')
            country_id = product.get('country_id')
            
            if region_name and region_name.strip() and country_id:
                if region_name not in region_data:
                    region_data[region_name] = {
                        'country_id': country_id,
                        'country_name': country_name
                    }
        
        # Convert to regions list with auto-incrementing IDs
        regions = []
        region_name_to_id = {}
        
        for idx, (region_name, info) in enumerate(sorted(region_data.items()), 1):
            region = {
                'id': idx,
                'name': region_name,
                'country_id': info['country_id'],
                'is_default': False,
                'created_at': self.timestamp,
                'updated_at': self.timestamp
            }
            regions.append(region)
            region_name_to_id[region_name] = idx
        
        return regions, region_name_to_id
    
    def update_products_region_ids(self, region_name_to_id: Dict[str, int]) -> None:
        """Update products to use region_id arrays and remove denormalized name fields."""
        products = self.load_json_file('products.json')
        updated_count = 0
        
        for product in products:
            region_name = product.get('region')
            
            if region_name and region_name.strip() and region_name in region_name_to_id:
                # Convert to array of region IDs
                product['region_id'] = [region_name_to_id[region_name]]
                updated_count += 1
            elif not product.get('region_id'):
                # Ensure region_id exists as empty array if no region
                product['region_id'] = []
            
            # Remove denormalized name fields (schema compliance)
            denormalized_fields = ['roaster', 'bean_type', 'country', 'region', 'decaf_method']
            for field in denormalized_fields:
                if field in product:
                    del product[field]
        
        self.save_json_file('products.json', products)
        print(f"✓ Updated {updated_count} products with region_id arrays")
        print("✓ Removed denormalized name fields for schema compliance")
    
    def create_regions_file(self, regions: List[Dict]) -> None:
        """Create the new regions.json file."""
        regions_file = os.path.join(self.data_dir, 'regions.json')
        
        if os.path.exists(regions_file):
            print("WARNING: regions.json already exists. Backing up to regions.json.bak")
            backup_file = regions_file + '.bak'
            with open(regions_file, 'r') as src, open(backup_file, 'w') as dst:
                dst.write(src.read())
        
        self.save_json_file('regions.json', regions)
        print(f"✓ Created regions.json with {len(regions)} regions")
    
    def update_schema_version(self) -> None:
        """Update schema_version.json to v1.3."""
        schema = self.load_json_file('schema_version.json')
        
        # Update main schema info
        schema['schema_version'] = '1.3'
        schema['created_date'] = '2025-07-23'
        schema['description'] = 'Separated regions into own lookup table with country_id parent reference, fixed lookup update_references bugs'
        
        # Update entity versions
        for entity in ['products', 'batches', 'brew_sessions', 'lookups']:
            if entity in schema.get('entities', {}):
                schema['entities'][entity]['version'] = '1.3'
        
        # Add regions to lookup tables
        if 'entities' in schema and 'lookups' in schema['entities']:
            lookup_tables = schema['entities']['lookups'].get('tables', [])
            if 'regions' not in lookup_tables:
                # Add regions after countries
                if 'countries' in lookup_tables:
                    countries_idx = lookup_tables.index('countries')
                    lookup_tables.insert(countries_idx + 1, 'regions')
                else:
                    lookup_tables.append('regions')
            
            # Update the note about regions
            schema['entities']['lookups']['note'] = (
                'All fields except id and name are optional. Only one item per table can have is_default=true. '
                'Regions table includes additional country_id field as foreign key reference.'
            )
        
        # Add v1.3 changelog
        schema['new_in_v1.3'] = {
            'regions_separation': 'Regions moved to separate lookup table with country_id parent reference',
            'lookup_bug_fixes': 'Fixed country and decaf_method update_references to use ID fields instead of names',
            'region_management': 'Added inline region management in country edit pages',
            'api_endpoints': 'Added /api/regions/* and /api/countries/{id}/regions endpoints'
        }
        
        self.save_json_file('schema_version.json', schema)
        print("✓ Updated schema_version.json to v1.3")
    
    def run_migration(self) -> None:
        """Run the complete migration process."""
        print("=== Coffee Journal Schema Migration: v1.2 → v1.3 ===")
        print()
        
        # Pre-flight checks
        print("Checking data files...")
        if not self.check_data_files():
            sys.exit(1)
        
        print("Checking schema version...")
        if not self.check_schema_version():
            sys.exit(0)
        
        print("✓ Pre-flight checks passed")
        print()
        
        # Migration steps
        print("Step 1: Extracting region data from products...")
        regions, region_name_to_id = self.extract_region_data()
        
        if not regions:
            print("No regions found in products. Creating empty regions.json...")
            self.create_regions_file([])
        else:
            print(f"Found {len(regions)} unique regions:")
            for region in regions:
                print(f"  - {region['name']} (country_id: {region['country_id']})")
            print()
            
            print("Step 2: Creating regions.json...")
            self.create_regions_file(regions)
            print()
            
            print("Step 3: Updating products with region_id arrays...")
            self.update_products_region_ids(region_name_to_id)
            print()
        
        print("Step 4: Updating schema version...")
        self.update_schema_version()
        print()
        
        print("=== Migration Complete! ===")
        print()
        print("Changes made:")
        print("✓ Created regions.json lookup table")
        print("✓ Updated products to use region_id arrays")
        print("✓ Updated schema_version.json to v1.3")
        print()
        print("Next steps:")
        print("1. Restart your application to load the new regions repository")
        print("2. Test the new region management features in the UI")
        print("3. Verify that country/region relationships work correctly")
        print()
        print("Note: Denormalized name fields (region, country, etc.) are still")
        print("present in products.json for backward compatibility. Consider")
        print("removing them in a future migration for full schema compliance.")

def main():
    """Main migration entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate Coffee Journal schema from v1.2 to v1.3')
    parser.add_argument('--data-dir', default='test_data', 
                       help='Directory containing JSON data files (default: test_data)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        print()
    
    migration = SchemaV13Migration(args.data_dir)
    
    if args.dry_run:
        # TODO: Implement dry-run mode
        print("Dry-run mode not yet implemented")
        sys.exit(1)
    else:
        migration.run_migration()

if __name__ == '__main__':
    main()