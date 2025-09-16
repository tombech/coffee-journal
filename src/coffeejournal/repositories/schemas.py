"""
JSON Schema definitions for repository data validation.
Auto-generated from schema_version.json v1.4
"""

# Base schema for all entities with audit fields
BASE_AUDIT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"}
    }
}

# Base schema for lookup entities
BASE_LOOKUP_SCHEMA = {
    "type": "object",
    "required": ["name"],
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "name": {"type": "string", "minLength": 1},
        "short_form": {"type": ["string", "null"]},
        "description": {"type": ["string", "null"]},
        "notes": {"type": ["string", "null"]},
        "url": {"type": ["string", "null"]},
        "image_url": {"type": ["string", "null"]},
        "icon": {"type": ["string", "null"]},
        "is_default": {"type": "boolean"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"}
    },
    "additionalProperties": False
}

# Schema definitions for each repository
SCHEMAS = {
    "products": {
        "type": "object",
        "required": ["product_name"],
        "properties": {
            "id": {"type": "integer", "minimum": 1},
            "roaster_id": {"type": ["integer", "null"]},
            "bean_type_id": {
                "type": "array",
                "items": {"type": "integer"}
            },
            "country_id": {"type": ["integer", "null"]},
            "region_id": {
                "type": "array",
                "items": {"type": "integer"}
            },
            "product_name": {"type": "string", "minLength": 1},
            "roast_type": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
            "description": {"type": ["string", "null"]},
            "url": {"type": ["string", "null"]},
            "image_url": {"type": ["string", "null"]},
            "decaf": {"type": "boolean"},
            "decaf_method_id": {"type": ["integer", "null"]},
            "rating": {"type": ["number", "null"], "minimum": 0, "maximum": 5, "multipleOf": 0.5},
            "bean_process": {
                "type": ["array", "null"],
                "items": {
                    "type": "string",
                    "enum": ["Washed (wet)", "Natural (dry)", "Honey", "Semi-washed (wet-hulled)", "Anaerobic", "Carbonic Maceration", "Other"]
                },
                "uniqueItems": True,
                "default": []
            },
            "notes": {"type": ["string", "null"]},
            "created_at": {"type": "string", "format": "date-time"},
            "updated_at": {"type": "string", "format": "date-time"}
        },
        "additionalProperties": False
    },
    
    "batches": {
        "type": "object",
        "required": ["product_id", "roast_date"],
        "properties": {
            "id": {"type": "integer", "minimum": 1},
            "product_id": {"type": "integer"},
            "roast_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
            "purchase_date": {"type": ["string", "null"], "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
            "amount_grams": {"type": ["number", "null"], "minimum": 0},
            "price": {"type": ["number", "null"], "minimum": 0},
            "seller": {"type": ["string", "null"]},
            "notes": {"type": ["string", "null"]},
            "rating": {"type": ["number", "null"], "minimum": 0, "maximum": 5, "multipleOf": 0.5},
            "is_active": {"type": "boolean"},
            "created_at": {"type": "string", "format": "date-time"},
            "updated_at": {"type": "string", "format": "date-time"}
        },
        "additionalProperties": False
    },
    
    "brew_sessions": {
        "type": "object",
        "required": [],
        "properties": {
            "id": {"type": "integer", "minimum": 1},
            "timestamp": {"type": "string"},
            "product_batch_id": {"type": ["integer", "null"]},
            "product_id": {"type": ["integer", "null"]},
            "brew_method_id": {"type": ["integer", "null"]},
            "brewer_id": {"type": ["integer", "null"]},
            "recipe_id": {"type": ["integer", "null"]},
            "grinder_id": {"type": ["integer", "null"]},
            "filter_id": {"type": ["integer", "null"]},
            "kettle_id": {"type": ["integer", "null"]},
            "scale_id": {"type": ["integer", "null"]},
            "amount_coffee_grams": {"type": ["number", "null"], "minimum": 0},
            "amount_water_grams": {"type": ["number", "null"], "minimum": 0},
            "brew_temperature_c": {"type": ["number", "null"]},
            "bloom_time_seconds": {"type": ["number", "null"], "minimum": 0},
            "brew_time_seconds": {"type": ["number", "null"], "minimum": 0},
            "sweetness": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
            "acidity": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
            "bitterness": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
            "body": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
            "aroma": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
            "flavor_profile_match": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
            "notes": {"type": ["string", "null"]},
            "score": {"type": ["number", "null"], "minimum": 1.0, "maximum": 10.0},
            "grinder_setting": {"type": ["string", "number", "null"]},
            "created_at": {"type": "string", "format": "date-time"},
            "updated_at": {"type": "string", "format": "date-time"}
        },
        "additionalProperties": False
    },
    
    "shots": {
        "type": "object",
        "required": ["dose_grams", "yield_grams"],
        "properties": {
            "id": {"type": "integer", "minimum": 1},
            "timestamp": {"type": "string"},
            "product_batch_id": {"type": ["integer", "null"]},
            "product_id": {"type": ["integer", "null"]},
            "shot_session_id": {"type": ["integer", "null"]},
            "brewer_id": {"type": ["integer", "null"]},
            "grinder_id": {"type": ["integer", "null"]},
            "portafilter_id": {"type": ["integer", "null"]},
            "basket_id": {"type": ["integer", "null"]},
            "tamper_id": {"type": ["integer", "null"]},
            "wdt_tool_id": {"type": ["integer", "null"]},
            "leveling_tool_id": {"type": ["integer", "null"]},
            "scale_id": {"type": ["integer", "null"]},
            "recipe_id": {"type": ["integer", "null"]},
            "dose_grams": {"type": "number", "minimum": 0},
            "yield_grams": {"type": "number", "minimum": 0},
            "preinfusion_seconds": {"type": ["number", "null"], "minimum": 0},
            "extraction_time_seconds": {"type": ["number", "null"], "minimum": 0},
            "brew_time_seconds": {"type": ["number", "null"], "minimum": 0},
            "pressure_bars": {"type": ["number", "null"], "minimum": 0},
            "water_temperature_c": {"type": ["number", "null"]},
            "temperature_c": {"type": ["number", "null"]},
            "grinder_setting": {"type": ["string", "number", "null"]},
            "sweetness": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
            "acidity": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
            "bitterness": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
            "body": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
            "aroma": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
            "crema": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
            "flavor_profile_match": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
            "extraction_status": {
                "type": ["string", "null"],
                "enum": ["channeling", "over-extracted", "under-extracted", "perfect", "balanced", None]
            },
            "notes": {"type": ["string", "null"]},
            "score": {"type": ["number", "null"], "minimum": 1.0, "maximum": 10.0},
            "overall_score": {"type": ["number", "null"], "minimum": 0, "maximum": 10},
            "ratio": {"type": ["string", "null"]},
            "created_at": {"type": "string", "format": "date-time"},
            "updated_at": {"type": "string", "format": "date-time"}
        },
        "additionalProperties": False
    },
    
    "shot_sessions": {
        "type": "object",
        "required": ["title"],
        "properties": {
            "id": {"type": "integer", "minimum": 1},
            "title": {"type": "string", "minLength": 1},
            "product_id": {"type": ["integer", "null"]},
            "product_batch_id": {"type": ["integer", "null"]},
            "brewer_id": {"type": ["integer", "null"]},
            "notes": {"type": ["string", "null"]},
            "created_at": {"type": "string", "format": "date-time"},
            "updated_at": {"type": "string", "format": "date-time"}
        },
        "additionalProperties": False
    },
    
    # Lookup tables with standard schema
    "roasters": BASE_LOOKUP_SCHEMA,
    "bean_types": BASE_LOOKUP_SCHEMA,
    "countries": BASE_LOOKUP_SCHEMA,
    "decaf_methods": BASE_LOOKUP_SCHEMA,
    "brew_methods": {
        **BASE_LOOKUP_SCHEMA,
        "properties": {
            **BASE_LOOKUP_SCHEMA["properties"],
            "brew_time_range": {"type": ["string", "null"]},
            "water_temperature": {"type": ["string", "null"]},
            "grind_size": {"type": ["string", "null"]}
        }
    },
    "recipes": {
        **BASE_LOOKUP_SCHEMA,
        "properties": {
            **BASE_LOOKUP_SCHEMA["properties"],
            "coffee_ratio": {"type": ["string", "null"]},
            "instructions": {"type": ["string", "null"]},
            "brew_method": {"type": ["string", "null"]}
        }
    },
    "grinders": {
        **BASE_LOOKUP_SCHEMA,
        "properties": {
            **BASE_LOOKUP_SCHEMA["properties"],
            "brand": {"type": ["string", "null"]},
            "grinder_type": {"type": ["string", "null"]},
            "burr_material": {"type": ["string", "null"]},
            "product_url": {"type": ["string", "null"]},
            "manually_ground_grams": {"type": ["number", "null"], "minimum": 0}
        }
    },
    "filters": {
        **BASE_LOOKUP_SCHEMA,
        "properties": {
            **BASE_LOOKUP_SCHEMA["properties"],
            "material": {"type": ["string", "null"]},
            "brand": {"type": ["string", "null"]},
            "compatibility": {"type": ["string", "null"]}
        }
    },
    "kettles": {
        **BASE_LOOKUP_SCHEMA,
        "properties": {
            **BASE_LOOKUP_SCHEMA["properties"],
            "brand": {"type": ["string", "null"]},
            "capacity": {"type": ["string", "null"]},
            "kettle_type": {"type": ["string", "null"]},
            "product_url": {"type": ["string", "null"]}
        }
    },
    "scales": BASE_LOOKUP_SCHEMA,
    "brewers": {
        **BASE_LOOKUP_SCHEMA,
        "properties": {
            **BASE_LOOKUP_SCHEMA["properties"],
            "type": {"type": ["string", "null"]},
            "brand": {"type": ["string", "null"]},
            "model": {"type": ["string", "null"]}
        }
    },
    "portafilters": {
        **BASE_LOOKUP_SCHEMA,
        "properties": {
            **BASE_LOOKUP_SCHEMA["properties"],
            "size": {"type": ["string", "null"]},
            "size_mm": {"type": ["integer", "null"]},
            "bottomless": {"type": ["boolean", "null"]},
            "brand": {"type": ["string", "null"]},
            "material": {"type": ["string", "null"]},
            "handle_type": {"type": ["string", "null"]}
        }
    },
    "baskets": {
        **BASE_LOOKUP_SCHEMA,
        "properties": {
            **BASE_LOOKUP_SCHEMA["properties"],
            "basket_type": {"type": ["string", "null"]},
            "hole_count": {"type": ["integer", "null"]},
            "capacity_grams": {"type": ["number", "null"]},
            "pressurized": {"type": ["boolean", "null"]},
            "size": {"type": ["string", "null"]},
            "brand": {"type": ["string", "null"]},
            "material": {"type": ["string", "null"]},
            "holes": {"type": ["integer", "null"]}
        }
    },
    "tampers": {
        **BASE_LOOKUP_SCHEMA,
        "properties": {
            **BASE_LOOKUP_SCHEMA["properties"],
            "size": {"type": ["string", "null"]},
            "weight": {"type": ["number", "null"]},
            "handle_material": {"type": ["string", "null"]},
            "base_material": {"type": ["string", "null"]},
            "brand": {"type": ["string", "null"]}
        }
    },
    "wdt_tools": {
        **BASE_LOOKUP_SCHEMA,
        "properties": {
            **BASE_LOOKUP_SCHEMA["properties"],
            "needle_count": {"type": ["integer", "null"]},
            "needle_diameter": {"type": ["string", "number", "null"]},
            "brand": {"type": ["string", "null"]},
            "handle_material": {"type": ["string", "null"]}
        }
    },
    "leveling_tools": BASE_LOOKUP_SCHEMA,
    "regions": {
        **BASE_LOOKUP_SCHEMA,
        "properties": {
            **BASE_LOOKUP_SCHEMA["properties"],
            "country_id": {"type": "integer"}
        },
        "required": ["name", "country_id"]
    }
}

class SchemaValidationError(Exception):
    """Raised when data fails schema validation."""
    pass


def get_schema_for_entity(entity_name):
    """Get the JSON schema for a specific entity."""
    # Remove .json extension if present
    if entity_name.endswith('.json'):
        entity_name = entity_name[:-5]
    
    # Handle plural/singular conversions
    if entity_name in SCHEMAS:
        return SCHEMAS[entity_name]
    
    # Return None for unknown entities (don't default to base lookup)
    return None


def validate_entity_data(entity_name, data):
    """
    Validate data against the schema for the given entity.
    
    Args:
        entity_name: Name of the entity type (e.g., 'shots', 'products')
        data: The data to validate (dict)
        
    Raises:
        SchemaValidationError: If data doesn't match schema
    """
    try:
        import jsonschema
    except ImportError:
        # If jsonschema not available, skip validation
        return
        
    schema = get_schema_for_entity(entity_name)
    if schema is None:
        # No schema defined for this entity, skip validation
        return
        
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        raise SchemaValidationError(f"Schema validation failed for {entity_name}: {e.message}")
    except jsonschema.SchemaError as e:
        raise SchemaValidationError(f"Invalid schema for {entity_name}: {e.message}")