"""
Test that half-star ratings are properly preserved for products and batches.
"""
import pytest
import json


def test_product_half_star_rating(client):
    """Test that products can have half-star ratings (e.g. 4.5)."""
    # Create a product with a half-star rating
    product_data = {
        "roaster_name": "Test Roaster",
        "bean_type_name": ["Arabica"],
        "country_name": "Brazil",
        "product_name": "Half Star Test",
        "rating": 4.5  # Half-star rating
    }
    
    response = client.post('/api/products', 
                         data=json.dumps(product_data),
                         content_type='application/json')
    assert response.status_code == 201
    
    # Get the created product ID
    created_product = response.get_json()
    product_id = created_product['id']
    
    # Verify the rating was preserved as 4.5
    assert created_product['rating'] == 4.5
    
    # Fetch the product again to ensure it's stored correctly
    response = client.get(f'/api/products/{product_id}')
    assert response.status_code == 200
    
    product = response.get_json()
    assert product['rating'] == 4.5


def test_product_update_half_star_rating(client):
    """Test that product ratings can be updated to half-star values."""
    # Create a product with a whole star rating
    product_data = {
        "roaster_name": "Test Roaster",
        "bean_type_name": ["Arabica"],
        "country_name": "Brazil",
        "product_name": "Update Rating Test",
        "rating": 4  # Whole star rating
    }
    
    response = client.post('/api/products', 
                         data=json.dumps(product_data),
                         content_type='application/json')
    assert response.status_code == 201
    
    created_product = response.get_json()
    product_id = created_product['id']
    
    # Update the rating to a half-star value
    update_data = {
        "roaster_name": "Test Roaster",
        "bean_type_name": ["Arabica"],
        "country_name": "Brazil",
        "product_name": "Update Rating Test",
        "rating": 3.5  # Half-star rating
    }
    
    response = client.put(f'/api/products/{product_id}', 
                        data=json.dumps(update_data),
                        content_type='application/json')
    assert response.status_code == 200
    
    updated_product = response.get_json()
    assert updated_product['rating'] == 3.5


def test_batch_half_star_rating(client):
    """Test that batches can have half-star ratings."""
    # First create a product
    product_data = {
        "roaster_name": "Test Roaster",
        "bean_type_name": ["Arabica"],
        "country_name": "Brazil",
        "product_name": "Batch Rating Test"
    }
    
    response = client.post('/api/products', 
                         data=json.dumps(product_data),
                         content_type='application/json')
    assert response.status_code == 201
    
    product_id = response.get_json()['id']
    
    # Create a batch with a half-star rating
    batch_data = {
        "roast_date": "2025-01-01",
        "purchase_date": "2025-01-02",
        "amount_grams": 250,
        "price": 15.00,
        "rating": 4.5  # Half-star rating
    }
    
    response = client.post(f'/api/products/{product_id}/batches', 
                         data=json.dumps(batch_data),
                         content_type='application/json')
    assert response.status_code == 201
    
    created_batch = response.get_json()
    assert created_batch['rating'] == 4.5
    
    # Fetch the batch to ensure it's stored correctly
    response = client.get(f'/api/batches/{created_batch["id"]}')
    assert response.status_code == 200
    
    batch = response.get_json()
    assert batch['rating'] == 4.5


def test_various_half_star_values(client):
    """Test various half-star values from 0.5 to 4.5."""
    half_star_values = [0.5, 1.5, 2.5, 3.5, 4.5]
    
    for rating in half_star_values:
        product_data = {
            "roaster_name": "Test Roaster",
            "bean_type_name": ["Arabica"],
            "country_name": "Brazil", 
            "product_name": f"Rating {rating} Test",
            "rating": rating
        }
        
        response = client.post('/api/products', 
                             data=json.dumps(product_data),
                             content_type='application/json')
        assert response.status_code == 201
        
        created_product = response.get_json()
        assert created_product['rating'] == rating, f"Expected rating {rating} but got {created_product['rating']}"