#!/usr/bin/env python3
"""
Initialize Coffee Journal database with sample data for Docker deployment.
This script will only run if the database doesn't exist or is empty.
"""
import os
import sys
import sqlite3

# Add src to Python path
sys.path.insert(0, '/app/src')

from coffeejournal import create_app, db
from coffeejournal.models import (
    Roaster, BeanType, Country, BrewMethod, Recipe,
    CoffeeBeanProduct, CoffeeBatch, BrewSession
)
from datetime import datetime, date

def database_is_empty():
    """Check if database is empty by looking for any roasters."""
    try:
        return Roaster.query.count() == 0
    except:
        return True

def init_database():
    """Initialize database with sample data."""
    app = create_app()
    
    with app.app_context():
        # Check if database needs initialization
        if not database_is_empty():
            print("Database already contains data. Skipping initialization.")
            return
            
        print("Initializing database with sample data...")
        
        # Create lookup data
        roasters = [
            Roaster(name="Blue Bottle Coffee"),
            Roaster(name="Stumptown Coffee Roasters"),
            Roaster(name="Intelligentsia Coffee"),
        ]
        
        bean_types = [
            BeanType(name="Arabica"),
            BeanType(name="Robusta"),
        ]
        
        countries = [
            Country(name="Ethiopia"),
            Country(name="Colombia"),
            Country(name="Guatemala"),
        ]
        
        brew_methods = [
            BrewMethod(name="Pour Over"),
            BrewMethod(name="French Press"),
            BrewMethod(name="Espresso"),
        ]
        
        recipes = [
            Recipe(name="Standard V60"),
            Recipe(name="4:6 Method"),
            Recipe(name="Classic French Press"),
        ]
        
        # Add all lookup data
        for items in [roasters, bean_types, countries, brew_methods, recipes]:
            for item in items:
                db.session.add(item)
        
        db.session.commit()
        
        # Create sample product
        product = CoffeeBeanProduct(
            roaster_id=roasters[0].id,
            bean_type_id=bean_types[0].id,
            country_id=countries[0].id,
            product_name="Ethiopia Yirgacheffe",
            roast_type=3,  # Medium roast
            description="Bright, floral notes with citrus acidity"
        )
        db.session.add(product)
        db.session.commit()
        
        # Create sample batch
        batch = CoffeeBatch(
            product_id=product.id,
            roast_date=date(2024, 1, 15),
            amount_grams=250.0,
            price=18.50,
            seller="Direct from roaster",
            notes="First batch - excited to try!"
        )
        db.session.add(batch)
        db.session.commit()
        
        print("Database initialized successfully with sample data!")
        print(f"- {len(roasters)} roasters")
        print(f"- {len(bean_types)} bean types") 
        print(f"- {len(countries)} countries")
        print(f"- {len(brew_methods)} brew methods")
        print(f"- {len(recipes)} recipes")
        print("- 1 sample product with 1 batch")

if __name__ == "__main__":
    init_database()