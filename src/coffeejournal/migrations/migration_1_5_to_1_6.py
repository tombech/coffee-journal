"""
Migration from schema version 1.5 to 1.6 - Bean Process Multiselect
"""

import os
import json
from datetime import datetime


def migrate_v1_5_to_v1_6(data_dir):
    """
    Migrate from schema version 1.5 to 1.6.

    This migration converts the products.bean_process field from a string to an array
    of standardized bean processing methods.

    Mapping:
    - "Washed" or "Vasket" → ["Washed (wet)"]
    - "Natural" → ["Natural (dry)"]
    - "Natural/Anaerobic" → ["Natural (dry)", "Anaerobic"]
    - "Honey" → ["Honey"]
    - "Washed, Natural" → ["Washed (wet)", "Natural (dry)"]
    - "Dried", "Dried whole beans", "Sun dried" → ["Natural (dry)"]
    - "Dried with and without fruit" → ["Other"]
    - "" (empty) → []

    Args:
        data_dir (str): Path to the data directory
    """
    print("🔄 Migrating from schema v1.5 to v1.6 (Bean Process Multiselect)")

    changes_made = 0

    # Define the mapping from old string values to new array values
    process_mapping = {
        "Washed": ["Washed (wet)"],
        "Vasket": ["Washed (wet)"],  # Norwegian for "Washed"
        "Natural": ["Natural (dry)"],
        "Natural/Anaerobic": ["Natural (dry)", "Anaerobic"],
        "Honey": ["Honey"],
        "Washed, Natural": ["Washed (wet)", "Natural (dry)"],
        "Dried": ["Natural (dry)"],
        "Dried whole beans": ["Natural (dry)"],
        "Sun dried": ["Natural (dry)"],
        "Dried with and without fruit": ["Other"],
        "": []  # Empty string becomes empty array
    }

    # Migrate products.json
    products_file = os.path.join(data_dir, 'products.json')

    if os.path.exists(products_file):
        try:
            with open(products_file, 'r') as f:
                products = json.load(f)

            products_updated = 0

            for product in products:
                if 'bean_process' in product:
                    old_value = product['bean_process']

                    # Handle None values
                    if old_value is None:
                        new_value = []
                    elif old_value in process_mapping:
                        # Convert string to array using mapping
                        new_value = process_mapping[old_value]
                    elif old_value.strip():
                        # Non-empty unknown value - categorize as "Other"
                        print(f"  ⚠️  Unknown bean_process value '{old_value}' for product {product.get('id', 'unknown')} - mapping to ['Other']")
                        new_value = ["Other"]
                    else:
                        # Empty string
                        new_value = []

                    # Update the product
                    product['bean_process'] = new_value
                    products_updated += 1

                    if old_value != new_value:
                        print(f"  📝 Product {product.get('id', 'unknown')}: '{old_value}' → {new_value}")

            # Write updated products back to file
            with open(products_file, 'w') as f:
                json.dump(products, f, indent=2)

            print(f"  ✅ Updated {products_updated} products in products.json")
            changes_made += products_updated

        except Exception as e:
            print(f"  ❌ Failed to migrate products.json: {e}")
            raise
    else:
        print("  ℹ️  No products.json file found - skipping product migration")

    # Update data version file
    version_file = os.path.join(data_dir, 'data_version.json')
    try:
        version_data = {
            'version': '1.6',
            'migrated_at': datetime.utcnow().isoformat(),
            'migration_notes': 'Converted bean_process from string to array of standardized processing methods'
        }

        with open(version_file, 'w') as f:
            json.dump(version_data, f, indent=2)
        print(f"  ✅ Updated data_version.json to v1.6")
        changes_made += 1
    except Exception as e:
        print(f"  ❌ Failed to update version file: {e}")
        raise

    if changes_made > 0:
        print(f"✅ Migration v1.5→v1.6 completed successfully ({changes_made} changes)")
    else:
        print("ℹ️  Migration v1.5→v1.6 completed (no changes needed)")

    return True


# Migration metadata
MIGRATION_INFO = {
    'from_version': '1.5',
    'to_version': '1.6',
    'description': 'Convert bean_process from string to array of standardized processing methods',
    'requires_backup': True,  # Data structure change requires backup
    'migrate_function': migrate_v1_5_to_v1_6
}