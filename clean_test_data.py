#!/usr/bin/env python3
"""
Clean test data to store only IDs, not resolved names/objects.
The backend will resolve IDs to full objects when serving to frontend.
"""
import json
import os

def clean_products():
    """Clean products.json to store only IDs"""
    products_file = 'test_data/products.json'
    
    with open(products_file, 'r') as f:
        products = json.load(f)
    
    cleaned_products = []
    for product in products:
        cleaned_product = {
            "id": product["id"],
            "roaster_id": product["roaster_id"],
            "bean_type_id": product["bean_type_id"] if isinstance(product.get("bean_type_id"), list) else [product["bean_type_id"]],
            "country_id": product["country_id"],
            "region_id": product["region_id"] if isinstance(product.get("region_id"), list) else [product["region_id"]] if product.get("region_id") else [],
            "product_name": product["product_name"],
            "roast_type": product.get("roast_type"),
            "description": product.get("description", ""),
            "url": product.get("url", ""),
            "image_url": product.get("image_url"),
            "decaf": product.get("decaf", False),
            "decaf_method_id": product.get("decaf_method_id"),
            "rating": product.get("rating"),
            "bean_process": product.get("bean_process", ""),
            "notes": product.get("notes", "")
        }
        
        # Remove None values
        cleaned_product = {k: v for k, v in cleaned_product.items() if v is not None}
        cleaned_products.append(cleaned_product)
    
    with open(products_file, 'w') as f:
        json.dump(cleaned_products, f, indent=2)
    
    print(f"✅ Cleaned {products_file} - removed redundant name fields, kept only IDs")

def clean_batches():
    """Clean batches.json to store only IDs"""
    batches_file = 'test_data/batches.json'
    
    with open(batches_file, 'r') as f:
        batches = json.load(f)
    
    cleaned_batches = []
    for batch in batches:
        cleaned_batch = {
            "id": batch["id"],
            "product_id": batch["product_id"],
            "roast_date": batch.get("roast_date"),
            "purchase_date": batch.get("purchase_date"),
            "amount_grams": batch.get("amount_grams"),
            "price": batch.get("price"),
            "seller": batch.get("seller", ""),
            "rating": batch.get("rating"),
            "notes": batch.get("notes", "")
        }
        
        # Remove None values
        cleaned_batch = {k: v for k, v in cleaned_batch.items() if v is not None}
        cleaned_batches.append(cleaned_batch)
    
    with open(batches_file, 'w') as f:
        json.dump(cleaned_batches, f, indent=2)
    
    print(f"✅ Cleaned {batches_file} - stored only IDs")

def clean_brew_sessions():
    """Clean brew_sessions.json to store only IDs"""
    brew_sessions_file = 'test_data/brew_sessions.json'
    
    with open(brew_sessions_file, 'r') as f:
        sessions = json.load(f)
    
    cleaned_sessions = []
    for session in sessions:
        cleaned_session = {
            "id": session["id"],
            "timestamp": session["timestamp"],
            "product_batch_id": session.get("product_batch_id"),
            "product_id": session["product_id"],
            "brew_method_id": session.get("brew_method_id"),
            "recipe_id": session.get("recipe_id"),
            "grinder_id": session.get("grinder_id"),
            "grinder_setting": session.get("grinder_setting", ""),
            "filter_id": session.get("filter_id"),
            "kettle_id": session.get("kettle_id"),
            "scale_id": session.get("scale_id"),
            "amount_coffee_grams": session.get("amount_coffee_grams"),
            "amount_water_grams": session.get("amount_water_grams"),
            "brew_temperature_c": session.get("brew_temperature_c"),
            "bloom_time_seconds": session.get("bloom_time_seconds"),
            "brew_time_seconds": session.get("brew_time_seconds"),
            "sweetness": session.get("sweetness"),
            "acidity": session.get("acidity"),
            "bitterness": session.get("bitterness"),
            "body": session.get("body"),
            "aroma": session.get("aroma"),
            "flavor_profile_match": session.get("flavor_profile_match"),
            "score": session.get("score"),
            "notes": session.get("notes", "")
        }
        
        # Remove None values and empty strings
        cleaned_session = {k: v for k, v in cleaned_session.items() if v is not None and v != ""}
        cleaned_sessions.append(cleaned_session)
    
    with open(brew_sessions_file, 'w') as f:
        json.dump(cleaned_sessions, f, indent=2)
    
    print(f"✅ Cleaned {brew_sessions_file} - stored only IDs")

def main():
    print("🧹 Cleaning test data to store only IDs...")
    print("The backend will resolve IDs to full objects when serving to frontend.\n")
    
    clean_products()
    clean_batches()
    clean_brew_sessions()
    
    print(f"\n✅ Test data cleaned! Storage now contains only IDs.")
    print("Backend will resolve these to full objects with names when serving API responses.")

if __name__ == "__main__":
    main()