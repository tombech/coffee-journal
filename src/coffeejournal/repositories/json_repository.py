import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timezone
from pathlib import Path
import threading
import tempfile
from filelock import FileLock, Timeout
import jsonschema
from jsonschema import validate, ValidationError
from .base import BaseRepository, LookupRepository
from .schemas import get_schema_for_entity, SchemaValidationError


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime and date objects."""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


class JSONRepositoryBase(BaseRepository):
    """Base class for JSON file-based repository implementation with cross-process locking."""
    
    def __init__(self, data_dir: str, filename: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.filepath = self.data_dir / filename
        self.filename = filename
        self.entity_name = filename[:-5] if filename.endswith('.json') else filename
        
        # Create cross-process lock file in system temp directory to avoid permissions issues
        lock_dir = Path(tempfile.gettempdir()) / "coffeejournal_locks"
        lock_dir.mkdir(exist_ok=True)
        # Use hash of full path to ensure unique lock files for different user directories
        lock_name = f"{filename}_{abs(hash(str(self.filepath)))}.lock"
        self.lock_filepath = lock_dir / lock_name
        
        # Keep threading lock for backwards compatibility within single process
        self._thread_lock = threading.Lock()
        
        # In-memory cache for performance
        self._cache = None
        self._cache_mtime = None
        
        # Schema validation settings
        self._enable_validation = os.environ.get('DISABLE_SCHEMA_VALIDATION', '').lower() != 'true'
        self._schema = None
        
        self._ensure_file_exists()
    
    def _get_lock(self, timeout: float = 10.0) -> FileLock:
        """Get a cross-process file lock with specified timeout."""
        return FileLock(str(self.lock_filepath), timeout=timeout)
    
    def invalidate_cache(self):
        """Invalidate the in-memory cache, forcing a reload on next read."""
        with self._thread_lock:
            self._cache = None
            self._cache_mtime = None
    
    def _ensure_file_exists(self):
        """Create file with empty list if it doesn't exist (cross-process safe)."""
        if not self.filepath.exists():
            try:
                # Use shorter timeout for file creation to avoid test delays
                with self._get_lock(timeout=5.0):
                    # Double-check after acquiring lock to prevent race conditions
                    if not self.filepath.exists():
                        with open(self.filepath, 'w') as f:
                            json.dump([], f)
            except Timeout:
                # If we can't get the lock quickly, another process is likely creating the file
                # Wait briefly and check again
                import time
                time.sleep(0.2)
                if not self.filepath.exists():
                    raise RuntimeError(f"Could not create or access {self.filepath} - timeout acquiring lock")
    
    def _read_data(self) -> List[Dict[str, Any]]:
        """Read data from JSON file with cross-process locking and caching."""
        # Check if we have a valid cache (thread-safe)
        with self._thread_lock:
            if self._cache is not None and self.filepath.exists():
                try:
                    current_mtime = os.path.getmtime(self.filepath)
                    if self._cache_mtime == current_mtime:
                        # Cache is still valid, return cached data
                        return self._cache.copy()  # Return copy to prevent external modifications
                except OSError:
                    # File might have been deleted, continue to read from disk
                    pass
        
        # Cache is invalid or doesn't exist, read from disk
        try:
            with self._get_lock(timeout=5.0):
                if not self.filepath.exists():
                    # Update cache and return empty list
                    with self._thread_lock:
                        self._cache = []
                        self._cache_mtime = None
                    return []
                
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    # Update cache (thread-safe)
                    with self._thread_lock:
                        self._cache = data
                        self._cache_mtime = os.path.getmtime(self.filepath)
                    return data.copy()  # Return copy to prevent external modifications
        except Timeout:
            raise RuntimeError(f"Timeout waiting for read lock on {self.filepath}")
        except (FileNotFoundError, json.JSONDecodeError):
            # File was deleted or corrupted between existence check and read
            with self._thread_lock:
                self._cache = []
                self._cache_mtime = None
            return []
    
    def _write_data(self, data: List[Dict[str, Any]]):
        """Write data to JSON file with cross-process locking and atomic writes."""
        # SAFEGUARD: Always strip enriched fields before writing to prevent corruption
        cleaned_data = []
        for item in data:
            cleaned_item = self._strip_enriched_fields(item)
            cleaned_data.append(cleaned_item)
        
        try:
            with self._get_lock(timeout=10.0):
                # Atomic write: write to temp file, then rename for crash safety
                temp_file = self.filepath.with_suffix('.tmp')
                try:
                    with open(temp_file, 'w') as f:
                        json.dump(cleaned_data, f, indent=2, cls=JSONEncoder)
                        # Force write to disk immediately
                        f.flush()
                        os.fsync(f.fileno())
                    # Atomic rename - works on all platforms
                    temp_file.replace(self.filepath)
                    
                    # Update cache with the cleaned data (thread-safe)
                    with self._thread_lock:
                        self._cache = cleaned_data.copy()
                        self._cache_mtime = os.path.getmtime(self.filepath)
                    
                    # Ensure directory entry is synced
                    try:
                        dir_fd = os.open(str(self.filepath.parent), os.O_RDONLY)
                        os.fsync(dir_fd)
                        os.close(dir_fd)
                    except (OSError, AttributeError):
                        # Some filesystems don't support directory sync
                        pass
                except Exception:
                    # Clean up temp file on error
                    if temp_file.exists():
                        temp_file.unlink()
                    raise
        except Timeout:
            raise RuntimeError(f"Timeout waiting for write lock on {self.filepath}")
    
    def _get_schema(self):
        """Get the JSON schema for this repository's entity type."""
        if self._schema is None:
            self._schema = get_schema_for_entity(self.entity_name)
        return self._schema
    
    def _validate_entity(self, entity: Dict[str, Any], skip_fields: List[str] = None) -> None:
        """Validate an entity against its schema."""
        if not self._enable_validation:
            return
        
        schema = self._get_schema()
        if not schema:
            return  # No schema defined for this entity
        
        # Create a copy for validation to avoid modifying the original
        entity_copy = entity.copy()
        
        # Remove fields that should be skipped (e.g., calculated fields)
        if skip_fields:
            for field in skip_fields:
                entity_copy.pop(field, None)
        
        try:
            validate(instance=entity_copy, schema=schema)
        except ValidationError as e:
            # Add debugging info for troubleshooting
            print(f"DEBUG: Validation failed for {self.entity_name}")
            print(f"DEBUG: Entity data: {entity_copy}")
            print(f"DEBUG: Error: {e.message}")
            print(f"DEBUG: Error path: {e.absolute_path}")
            raise SchemaValidationError(f"Schema validation failed for {self.entity_name}: {e.message}")
    
    def _validate_all_data(self, data: List[Dict[str, Any]]) -> List[str]:
        """Validate all entities in the dataset and return any validation errors."""
        if not self._enable_validation:
            return []
        
        errors = []
        for i, entity in enumerate(data):
            try:
                self._validate_entity(entity)
            except ValueError as e:
                errors.append(f"Record {i} (ID: {entity.get('id', 'unknown')}): {e}")
        
        return errors
    
    def _strip_enriched_fields(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Remove any fields that are not in the schema (enriched/calculated fields)."""
        schema = self._get_schema()
        if not schema or 'properties' not in schema:
            return entity
        
        allowed_fields = set(schema['properties'].keys())
        cleaned = {}
        for key, value in entity.items():
            if key in allowed_fields:
                cleaned[key] = value
        
        return cleaned
    
    def _get_next_id(self, data: List[Dict[str, Any]]) -> int:
        """Get next available ID."""
        if not data:
            return 1
        return max(item['id'] for item in data) + 1
    
    def find_all(self) -> List[Dict[str, Any]]:
        """Get all entities."""
        return self._read_data()
    
    def find_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """Get entity by ID with optimized caching."""
        # First ensure cache is up to date
        data = self._read_data()
        for item in data:
            if item['id'] == id:
                return item.copy()  # Return copy to prevent external modifications
        return None
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new entity."""
        # Strip any enriched fields that shouldn't be saved
        cleaned_data = self._strip_enriched_fields(data)
        
        all_data = self._read_data()
        new_item = cleaned_data.copy()
        new_item['id'] = self._get_next_id(all_data)
        
        # Add audit timestamps
        now = datetime.now(timezone.utc).isoformat()
        new_item['created_at'] = now
        new_item['updated_at'] = now
        
        # Validate before saving
        self._validate_entity(new_item)
        
        all_data.append(new_item)
        self._write_data(all_data)
        return new_item
    
    def update(self, id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing entity."""
        # Strip any enriched fields that shouldn't be saved
        cleaned_data = self._strip_enriched_fields(data)
        
        all_data = self._read_data()
        for i, item in enumerate(all_data):
            if item['id'] == id:
                # First strip any enriched fields from the existing item
                cleaned_existing = self._strip_enriched_fields(item)
                # Start with the cleaned existing item
                updated_item = cleaned_existing.copy()
                # Merge in the cleaned update data
                updated_item.update(cleaned_data)
                # Ensure ID is preserved
                updated_item['id'] = id
                
                # Preserve created_at, update updated_at
                updated_item['created_at'] = item.get('created_at', datetime.now(timezone.utc).isoformat())
                updated_item['updated_at'] = datetime.now(timezone.utc).isoformat()
                
                # Validate before saving
                self._validate_entity(updated_item)
                
                all_data[i] = updated_item
                self._write_data(all_data)
                return updated_item
        return None
    
    def delete(self, id: int) -> bool:
        """Delete entity by ID."""
        all_data = self._read_data()
        original_len = len(all_data)
        all_data = [item for item in all_data if item['id'] != id]
        if len(all_data) < original_len:
            self._write_data(all_data)
            return True
        return False


class JSONLookupRepository(JSONRepositoryBase, LookupRepository):
    """JSON repository for lookup tables."""
    
    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find entity by name (case-insensitive, whitespace-trimmed)."""
        if not name:
            return None
        normalized_name = name.strip().lower()
        data = self._read_data()
        for item in data:
            if item.get('name') and item['name'].strip().lower() == normalized_name:
                return item
        return None
    
    def find_by_short_form(self, short_form: str) -> Optional[Dict[str, Any]]:
        """Find entity by short_form."""
        if not short_form:  # Skip empty strings and None
            return None
        data = self._read_data()
        for item in data:
            if item.get('short_form') == short_form:
                return item
        return None
    
    def find_by_name_or_short_form(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Find entity by name or short_form."""
        # Try name first
        result = self.find_by_name(identifier)
        if result:
            return result
        # Then try short_form
        return self.find_by_short_form(identifier)
    
    def get_or_create(self, name: str, **kwargs) -> Dict[str, Any]:
        """Get existing entity by name or create new one."""
        existing = self.find_by_name(name)
        if existing:
            return existing
        data = {'name': name}
        data.update(kwargs)
        return self.create(data)
    
    def get_or_create_by_identifier(self, identifier: str, **kwargs) -> Dict[str, Any]:
        """Get existing entity by name or short_form, or create new one."""
        # First try to find by name or short_form
        existing = self.find_by_name_or_short_form(identifier)
        if existing:
            return existing
        
        # If not found, create new one with the identifier as name
        data = {'name': identifier}
        data.update(kwargs)
        return self.create(data)
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search entities by substring match on name and short_form (if available)."""
        if not query:
            return []
        
        query_lower = query.lower()
        results = []
        
        for entity in self.find_all():
            # Check name field
            if entity.get('name') and query_lower in entity['name'].lower():
                results.append(entity)
                continue
            
            # Check short_form field if it exists
            if entity.get('short_form') and query_lower in entity['short_form'].lower():
                results.append(entity)
        
        return results
    
    def find_default(self) -> Optional[Dict[str, Any]]:
        """Find the default item (is_default=True)."""
        data = self._read_data()
        for item in data:
            if item.get('is_default') is True:
                return item
        return None
    
    def set_default(self, item_id: int) -> Dict[str, Any]:
        """Set an item as default, clearing any existing default."""
        all_data = self._read_data()
        updated_item = None
        
        # First pass: clear all existing defaults and find the item to set as default
        for item in all_data:
            if item['id'] == item_id:
                item['is_default'] = True
                updated_item = item
            elif item.get('is_default') is True:
                item['is_default'] = False
        
        if updated_item is None:
            raise ValueError(f"Item with id {item_id} not found")
        
        # Write back the changes
        self._write_data(all_data)
        return updated_item
    
    def clear_default(self, item_id: int) -> Dict[str, Any]:
        """Clear the default flag from an item."""
        all_data = self._read_data()
        updated_item = None
        
        for item in all_data:
            if item['id'] == item_id:
                item['is_default'] = False
                updated_item = item
                break
        
        if updated_item is None:
            raise ValueError(f"Item with id {item_id} not found")
        
        # Write back the changes
        self._write_data(all_data)
        return updated_item
    
    def get_smart_default(self, factory=None, user_id=None) -> Optional[Dict[str, Any]]:
        """Get smart default based on usage frequency and recency."""
        # First check if there's a manually set default
        manual_default = self.find_default()
        if manual_default:
            return manual_default
        
        # If no manual default, calculate smart default
        return self._calculate_smart_default(factory, user_id)
    
    def _calculate_smart_default(self, factory=None, user_id=None) -> Optional[Dict[str, Any]]:
        """Calculate smart default based on usage patterns."""
        # This is the base implementation - subclasses should override for specific logic
        items = self.find_all()
        if not items:
            return None
        
        # If only one item, return it
        if len(items) == 1:
            return items[0]
        
        # Default fallback: return the first item
        return items[0]
    
    def _calculate_equipment_smart_default(self, field_name: str, factory=None, user_id=None) -> Optional[Dict[str, Any]]:
        """Generic smart default calculation for equipment based on brew session usage."""
        if factory is None:
            from .factory import get_repository_factory
            factory = get_repository_factory()
        
        items = self.find_all()
        if not items:
            return None
        
        if len(items) == 1:
            return items[0]
        
        # Get all brew sessions to calculate usage (user-specific if user_id provided)
        sessions = factory.get_brew_session_repository(user_id).find_all()
        
        # Calculate frequency and recency scores
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        item_scores = {}
        
        for item in items:
            item_id = item['id']
            item_sessions = [s for s in sessions if s.get(field_name) == item_id]
            
            frequency_score = len(item_sessions)
            recency_score = 0
            
            # Calculate recency score based on most recent session
            for session in item_sessions:
                if 'created_at' in session:
                    try:
                        created_at = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00'))
                        days_ago = (now - created_at).days
                        # Higher score for more recent items (max 7 days = score 1.0)
                        recency_score = max(recency_score, max(0, 1.0 - (days_ago / 7.0)))
                    except:
                        pass
            
            # Combined score: 60% frequency, 40% recency
            combined_score = (frequency_score * 0.6) + (recency_score * 0.4)
            item_scores[item_id] = combined_score
        
        # Return the item with highest score
        if item_scores and max(item_scores.values()) > 0:
            best_item_id = max(item_scores.keys(), key=lambda x: item_scores[x])
            return next(i for i in items if i['id'] == best_item_id)
        
        # Fallback to first item
        return items[0]


class RoasterRepository(JSONLookupRepository):
    """Repository for Roaster entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'roasters.json')
    
    def _calculate_smart_default(self, factory=None, user_id=None) -> Optional[Dict[str, Any]]:
        """Calculate smart default based on product usage patterns."""
        if factory is None:
            from .factory import get_repository_factory
            factory = get_repository_factory()
        
        roasters = self.find_all()
        if not roasters:
            return None
        
        if len(roasters) == 1:
            return roasters[0]
        
        # Get all products to calculate roaster usage
        products = factory.get_product_repository().find_all()
        
        # Calculate frequency and recency scores
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        roaster_scores = {}
        
        for roaster in roasters:
            roaster_id = roaster['id']
            roaster_products = [p for p in products if p.get('roaster_id') == roaster_id]
            
            frequency_score = len(roaster_products)
            recency_score = 0
            
            # Calculate recency score based on most recent product created_at
            for product in roaster_products:
                if 'created_at' in product:
                    try:
                        created_at = datetime.fromisoformat(product['created_at'].replace('Z', '+00:00'))
                        days_ago = (now - created_at).days
                        # Higher score for more recent items (max 30 days = score 1.0)
                        recency_score = max(recency_score, max(0, 1.0 - (days_ago / 30.0)))
                    except:
                        pass
            
            # Combined score: 70% frequency, 30% recency
            combined_score = (frequency_score * 0.7) + (recency_score * 0.3)
            roaster_scores[roaster_id] = combined_score
        
        # Return the roaster with highest score
        if roaster_scores:
            best_roaster_id = max(roaster_scores.keys(), key=lambda x: roaster_scores[x])
            return next(r for r in roasters if r['id'] == best_roaster_id)
        
        # Fallback to first roaster
        return roasters[0]


class BeanTypeRepository(JSONLookupRepository):
    """Repository for BeanType entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'bean_types.json')


class CountryRepository(JSONLookupRepository):
    """Repository for Country entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'countries.json')


class RegionRepository(JSONLookupRepository):
    """Repository for Region entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'regions.json')
    
    def find_by_country(self, country_id: int) -> List[Dict[str, Any]]:
        """Find all regions for a specific country."""
        regions = self.find_all()
        return [region for region in regions if region.get('country_id') == country_id]
    
    def get_or_create(self, name: str, country_id: int = None, **kwargs) -> Dict[str, Any]:
        """Get existing region by name and country_id, or create new one."""
        regions = self.find_all()
        existing = next(
            (region for region in regions 
             if region['name'] == name and region.get('country_id') == country_id), 
            None
        )
        
        if existing:
            return existing
        
        # Create new region
        region_data = {'name': name, 'country_id': country_id, **kwargs}
        return self.create(region_data)


class BrewMethodRepository(JSONLookupRepository):
    """Repository for BrewMethod entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'brew_methods.json')
    
    def _calculate_smart_default(self, factory=None, user_id=None) -> Optional[Dict[str, Any]]:
        """Calculate smart default based on brew session usage patterns."""
        return self._calculate_equipment_smart_default('brew_method_id', factory, user_id)


class RecipeRepository(JSONLookupRepository):
    """Repository for Recipe entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'recipes.json')
    
    def _calculate_smart_default(self, factory=None, user_id=None) -> Optional[Dict[str, Any]]:
        """Calculate smart default based on brew session usage patterns."""
        return self._calculate_equipment_smart_default('recipe_id', factory, user_id)


class ProductRepository(JSONRepositoryBase):
    """Repository for CoffeeBeanProduct entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'products.json')
    
    def _calculate_smart_default(self, factory=None, user_id=None) -> Optional[Dict[str, Any]]:
        """Calculate smart default product based on brew session usage patterns."""
        if factory is None:
            from .factory import get_repository_factory
            factory = get_repository_factory()
        
        products = self.find_all()
        if not products:
            return None
        
        if len(products) == 1:
            return products[0]
        
        # Get all brew sessions to calculate product usage
        sessions = factory.get_brew_session_repository(user_id).find_all()
        
        # Calculate frequency and recency scores
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        product_scores = {}
        
        for product in products:
            product_id = product['id']
            sessions_with_product = [s for s in sessions if s.get('product_id') == product_id]
            
            if not sessions_with_product:
                # No usage, give minimal score
                product_scores[product_id] = {'frequency': 0, 'recency': 0, 'total': 0}
                continue
            
            # Frequency score (normalized)
            frequency_score = len(sessions_with_product)
            
            # Recency score - higher score for more recent usage
            recency_score = 0
            for session in sessions_with_product:
                try:
                    session_time = datetime.fromisoformat(session['timestamp'].replace('Z', '+00:00'))
                    days_ago = (now - session_time).days
                    # Exponential decay: more recent = higher score
                    recency_score += max(0, 100 * (0.95 ** days_ago))
                except (ValueError, TypeError, KeyError):
                    continue
            
            # Combined score: 70% frequency, 30% recency
            total_score = (0.7 * frequency_score) + (0.3 * recency_score)
            product_scores[product_id] = {
                'frequency': frequency_score,
                'recency': recency_score,
                'total': total_score
            }
        
        # Find product with highest score
        if not product_scores or all(score['total'] == 0 for score in product_scores.values()):
            # No usage data, return first product
            return products[0]
        
        best_product_id = max(product_scores.keys(), key=lambda pid: product_scores[pid]['total'])
        return next(p for p in products if p['id'] == best_product_id)
    
    def get_products_with_batch_status(self, factory=None, user_id=None) -> List[Dict[str, Any]]:
        """Get all products with active batch status and smart ordering."""
        if factory is None:
            from .factory import get_repository_factory
            factory = get_repository_factory()
        
        products = self.find_all()
        batch_repo = factory.get_batch_repository(user_id)
        
        # Enhance products with batch status
        enhanced_products = []
        for product in products:
            batches = batch_repo.find_by_product(product['id'])
            active_batches = [b for b in batches if b.get('is_active', True)]  # Default True if not specified
            
            enhanced_product = product.copy()
            enhanced_product['has_active_batches'] = len(active_batches) > 0
            enhanced_product['total_batches'] = len(batches)
            enhanced_product['active_batch_count'] = len(active_batches)
            enhanced_products.append(enhanced_product)
        
        # Get usage-based ordering using smart default logic
        sessions = factory.get_brew_session_repository(user_id).find_all()
        
        # Calculate scores for all products
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        for product in enhanced_products:
            product_id = product['id']
            sessions_with_product = [s for s in sessions if s.get('product_id') == product_id]
            
            if not sessions_with_product:
                product['usage_score'] = 0
                continue
            
            # Calculate usage score (frequency + recency)
            frequency_score = len(sessions_with_product)
            recency_score = 0
            
            for session in sessions_with_product:
                try:
                    session_time = datetime.fromisoformat(session['timestamp'].replace('Z', '+00:00'))
                    days_ago = (now - session_time).days
                    recency_score += max(0, 100 * (0.95 ** days_ago))
                except (ValueError, TypeError, KeyError):
                    continue
            
            product['usage_score'] = (0.7 * frequency_score) + (0.3 * recency_score)
        
        # Sort: active products first (by usage), then inactive products (by usage)
        active_products = [p for p in enhanced_products if p['has_active_batches']]
        inactive_products = [p for p in enhanced_products if not p['has_active_batches']]
        
        # Sort each group by usage score (highest first)
        active_products.sort(key=lambda p: p['usage_score'], reverse=True)
        inactive_products.sort(key=lambda p: p['usage_score'], reverse=True)
        
        return active_products + inactive_products
    
    def get_smart_default(self, factory=None, user_id=None) -> Optional[Dict[str, Any]]:
        """Get smart default product based on usage patterns."""
        return self._calculate_smart_default(factory, user_id)
    


class BatchRepository(JSONRepositoryBase):
    """Repository for CoffeeBatch entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'batches.json')
    
    def find_by_product(self, product_id: int) -> List[Dict[str, Any]]:
        """Find all batches for a product."""
        batches = self.find_all()
        return [b for b in batches if b.get('product_id') == product_id]
    
    def find_by_product_with_smart_ordering(self, product_id: int) -> List[Dict[str, Any]]:
        """Find all batches for a product with smart ordering (active first, then by roast date)."""
        batches = self.find_by_product(product_id)
        
        if not batches:
            return []
        
        # Separate active and inactive batches
        active_batches = [b for b in batches if b.get('is_active', True)]  # Default True if not specified
        inactive_batches = [b for b in batches if not b.get('is_active', True)]
        
        # Sort active batches by roast_date (newest first)
        active_batches.sort(key=lambda b: b.get('roast_date', ''), reverse=True)
        
        # Sort inactive batches by roast_date (newest first)  
        inactive_batches.sort(key=lambda b: b.get('roast_date', ''), reverse=True)
        
        # Return active first, then inactive
        return active_batches + inactive_batches
    
    def delete_by_product(self, product_id: int) -> int:
        """Delete all batches for a product."""
        all_data = self._read_data()
        original_len = len(all_data)
        all_data = [item for item in all_data if item.get('product_id') != product_id]
        deleted_count = original_len - len(all_data)
        if deleted_count > 0:
            self._write_data(all_data)
        return deleted_count


class BrewSessionRepository(JSONRepositoryBase):
    """Repository for BrewSession entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'brew_sessions.json')
    
    def find_by_product(self, product_id: int) -> List[Dict[str, Any]]:
        """Find all brew sessions for a product."""
        sessions = self.find_all()
        return [s for s in sessions if s.get('product_id') == product_id]
    
    def find_by_batch(self, batch_id: int) -> List[Dict[str, Any]]:
        """Find all brew sessions for a batch."""
        sessions = self.find_all()
        return [s for s in sessions if s.get('product_batch_id') == batch_id]
    
    def delete_by_product(self, product_id: int) -> int:
        """Delete all brew sessions for a product."""
        all_data = self._read_data()
        original_len = len(all_data)
        all_data = [item for item in all_data if item.get('product_id') != product_id]
        deleted_count = original_len - len(all_data)
        if deleted_count > 0:
            self._write_data(all_data)
        return deleted_count
    
    def delete_by_batch(self, batch_id: int) -> int:
        """Delete all brew sessions for a batch."""
        all_data = self._read_data()
        original_len = len(all_data)
        all_data = [item for item in all_data if item.get('product_batch_id') != batch_id]
        deleted_count = original_len - len(all_data)
        if deleted_count > 0:
            self._write_data(all_data)
        return deleted_count


class GrinderRepository(JSONLookupRepository):
    """Repository for Grinder entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'grinders.json')
    
    def get_usage_stats(self, grinder_id: int, factory=None) -> Dict[str, Any]:
        """Get usage statistics for a grinder."""
        if factory is None:
            from .factory import get_repository_factory
            factory = get_repository_factory()
        
        # Get all brew sessions that used this grinder
        brew_sessions = factory.get_brew_session_repository().find_all()
        grinder_sessions = [s for s in brew_sessions if s.get('grinder_id') == grinder_id]
        
        total_grams_ground = 0
        total_brews = len(grinder_sessions)
        
        for session in grinder_sessions:
            coffee_amount = session.get('amount_coffee_grams', 0)
            if coffee_amount:
                total_grams_ground += coffee_amount
        
        # Get all shots that used this grinder
        shots = factory.get_shot_repository().find_all()
        grinder_shots = [s for s in shots if s.get('grinder_id') == grinder_id]
        
        total_shots = len(grinder_shots)
        
        for shot in grinder_shots:
            dose_amount = shot.get('dose_grams', 0)
            if dose_amount:
                total_grams_ground += dose_amount
        
        # Get grinder details to add manual offset
        grinder = self.find_by_id(grinder_id)
        manual_offset = grinder.get('manually_ground_grams') if grinder else None
        manual_offset = manual_offset if manual_offset is not None else 0
        
        total_with_offset = total_grams_ground + manual_offset
        
        return {
            'total_brews': total_brews,
            'total_shots': total_shots,
            'total_grams_ground': total_grams_ground,
            'manually_ground_grams': manual_offset,
            'total_grams_with_manual': total_with_offset,
            'total_kilos': round(total_with_offset / 1000, 2) if total_with_offset >= 1000 else 0
        }
    
    def _calculate_smart_default(self, factory=None, user_id=None) -> Optional[Dict[str, Any]]:
        """Calculate smart default based on brew session usage patterns."""
        if factory is None:
            from .factory import get_repository_factory
            factory = get_repository_factory()
        
        grinders = self.find_all()
        if not grinders:
            return None
        
        if len(grinders) == 1:
            return grinders[0]
        
        # Get all brew sessions to calculate grinder usage
        sessions = factory.get_brew_session_repository(user_id).find_all()
        
        # Calculate frequency and recency scores
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        grinder_scores = {}
        
        for grinder in grinders:
            grinder_id = grinder['id']
            grinder_sessions = [s for s in sessions if s.get('grinder_id') == grinder_id]
            
            frequency_score = len(grinder_sessions)
            recency_score = 0
            
            # Calculate recency score based on most recent session
            for session in grinder_sessions:
                if 'created_at' in session:
                    try:
                        created_at = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00'))
                        days_ago = (now - created_at).days
                        # Higher score for more recent items (max 7 days = score 1.0)
                        recency_score = max(recency_score, max(0, 1.0 - (days_ago / 7.0)))
                    except:
                        pass
            
            # Combined score: 60% frequency, 40% recency (recency more important for equipment)
            combined_score = (frequency_score * 0.6) + (recency_score * 0.4)
            grinder_scores[grinder_id] = combined_score
        
        # Return the grinder with highest score
        if grinder_scores and max(grinder_scores.values()) > 0:
            best_grinder_id = max(grinder_scores.keys(), key=lambda x: grinder_scores[x])
            return next(g for g in grinders if g['id'] == best_grinder_id)
        
        # Fallback to first grinder
        return grinders[0]


class DecafMethodRepository(JSONLookupRepository):
    """Repository for DecafMethod entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'decaf_methods.json')


class FilterRepository(JSONLookupRepository):
    """Repository for Filter entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'filters.json')
    
    def _calculate_smart_default(self, factory=None, user_id=None) -> Optional[Dict[str, Any]]:
        """Calculate smart default based on brew session usage patterns."""
        return self._calculate_equipment_smart_default('filter_id', factory, user_id)


class KettleRepository(JSONLookupRepository):
    """Repository for Kettle entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'kettles.json')
    
    def _calculate_smart_default(self, factory=None, user_id=None) -> Optional[Dict[str, Any]]:
        """Calculate smart default based on brew session usage patterns."""
        return self._calculate_equipment_smart_default('kettle_id', factory, user_id)


class ScaleRepository(JSONLookupRepository):
    """Repository for Scale entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'scales.json')
    
    def _calculate_smart_default(self, factory=None, user_id=None) -> Optional[Dict[str, Any]]:
        """Calculate smart default based on brew session usage patterns."""
        return self._calculate_equipment_smart_default('scale_id', factory, user_id)


class ShotRepository(JSONRepositoryBase):
    """Repository for Shot entities (espresso shots)."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'shots.json')
    
    def create(self, shot: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new shot with calculated ratio."""
        # Add timestamps if not provided
        now = datetime.now(timezone.utc).isoformat()
        if 'created_at' not in shot:
            shot['created_at'] = now
        if 'updated_at' not in shot:
            shot['updated_at'] = now
        if 'timestamp' not in shot:
            shot['timestamp'] = now
        
        # Calculate ratio from dose and yield
        if 'dose_grams' in shot and 'yield_grams' in shot:
            dose = shot['dose_grams']
            yield_grams = shot['yield_grams']
            if dose > 0:
                ratio = round(yield_grams / dose, 2)
                shot['ratio'] = f"1:{ratio}"
        
        return super().create(shot)
    
    def update(self, shot_id: int, shot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a shot and recalculate ratio if needed."""
        # Update timestamp
        shot['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Recalculate ratio if dose or yield changed
        if 'dose_grams' in shot and 'yield_grams' in shot:
            dose = shot['dose_grams']
            yield_grams = shot['yield_grams']
            if dose > 0:
                ratio = round(yield_grams / dose, 2)
                shot['ratio'] = f"1:{ratio}"
        
        return super().update(shot_id, shot)
    
    def find_by_session(self, session_id: int) -> List[Dict[str, Any]]:
        """Find all shots in a particular shot session."""
        all_shots = self.find_all()
        return [s for s in all_shots if s.get('shot_session_id') == session_id]
    
    def find_by_product(self, product_id: int) -> List[Dict[str, Any]]:
        """Find all shots for a particular product."""
        all_shots = self.find_all()
        return [s for s in all_shots if s.get('product_id') == product_id]
    
    def find_by_batch(self, batch_id: int) -> List[Dict[str, Any]]:
        """Find all shots for a particular batch."""
        all_shots = self.find_all()
        return [s for s in all_shots if s.get('product_batch_id') == batch_id]
    
    def remove_from_session(self, shot_id: int) -> Optional[Dict[str, Any]]:
        """Remove a shot from its session (set shot_session_id to null)."""
        shot = self.find_by_id(shot_id)
        if shot:
            shot['shot_session_id'] = None
            return self.update(shot_id, shot)
        return None


class ShotSessionRepository(JSONRepositoryBase):
    """Repository for ShotSession entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'shot_sessions.json')
    
    def create(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new shot session."""
        # Add timestamps if not provided
        now = datetime.now(timezone.utc).isoformat()
        if 'created_at' not in session:
            session['created_at'] = now
        if 'updated_at' not in session:
            session['updated_at'] = now
        
        return super().create(session)
    
    def update(self, session_id: int, session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a shot session."""
        # Update timestamp
        session['updated_at'] = datetime.now(timezone.utc).isoformat()
        return super().update(session_id, session)
    
    def delete(self, session_id: int, factory=None) -> bool:
        """Delete a shot session and remove references from associated shots."""
        if factory is None:
            from .factory import get_repository_factory
            factory = get_repository_factory()
        
        # Find all shots in this session and remove the reference
        shot_repo = factory.get_shot_repository()
        shots_in_session = shot_repo.find_by_session(session_id)
        
        for shot in shots_in_session:
            shot_repo.remove_from_session(shot['id'])
        
        # Now delete the session itself
        return super().delete(session_id)


class BrewerRepository(JSONLookupRepository):
    """Repository for Brewer entities (espresso machines, V60, AeroPress, etc.)."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'brewers.json')
    
    def _calculate_smart_default(self, factory=None, user_id=None) -> Optional[Dict[str, Any]]:
        """Calculate smart default based on brew session and shot usage patterns."""
        if factory is None:
            from .factory import get_repository_factory
            factory = get_repository_factory()
        
        brewers = self.find_all()
        if not brewers:
            return None
        
        if len(brewers) == 1:
            return brewers[0]
        
        # Check both brew sessions and shots for usage
        brew_sessions = factory.get_brew_session_repository(user_id).find_all()
        brewer_scores = {}
        
        # Score based on brew session usage
        for brewer in brewers:
            brewer_id = brewer['id']
            sessions_with_brewer = [s for s in brew_sessions if s.get('brewer_id') == brewer_id]
            
            frequency_score = len(sessions_with_brewer) / max(len(brew_sessions), 1)
            recency_score = 0
            
            if sessions_with_brewer:
                sorted_sessions = sorted(sessions_with_brewer, 
                                        key=lambda x: x.get('timestamp', ''), 
                                        reverse=True)
                recent_session = sorted_sessions[0]
                try:
                    session_date = datetime.fromisoformat(recent_session['timestamp'].replace('Z', '+00:00'))
                    days_ago = (datetime.now(timezone.utc) - session_date).days
                    recency_score = max(0, 1 - (days_ago / 365))
                except:
                    pass
            
            combined_score = (frequency_score * 0.6) + (recency_score * 0.4)
            brewer_scores[brewer_id] = combined_score
        
        # Also check shots if available
        try:
            shots = factory.get_shot_repository().find_all()
            for brewer in brewers:
                brewer_id = brewer['id']
                shots_with_brewer = [s for s in shots if s.get('brewer_id') == brewer_id]
                
                if shots_with_brewer:
                    # Add shot usage to the score
                    frequency_bonus = len(shots_with_brewer) / max(len(shots), 1)
                    brewer_scores[brewer_id] = brewer_scores.get(brewer_id, 0) + (frequency_bonus * 0.3)
        except:
            pass  # Shots repository might not exist yet
        
        # Return the brewer with highest score
        if brewer_scores and max(brewer_scores.values()) > 0:
            best_brewer_id = max(brewer_scores.keys(), key=lambda x: brewer_scores[x])
            return next(b for b in brewers if b['id'] == best_brewer_id)
        
        return brewers[0]


class PortafilterRepository(JSONLookupRepository):
    """Repository for Portafilter entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'portafilters.json')


class BasketRepository(JSONLookupRepository):
    """Repository for Basket entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'baskets.json')


class TamperRepository(JSONLookupRepository):
    """Repository for Tamper entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'tampers.json')


class WDTToolRepository(JSONLookupRepository):
    """Repository for WDT Tool entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'wdt_tools.json')


class LevelingToolRepository(JSONLookupRepository):
    """Repository for Leveling Tool entities."""
    def __init__(self, data_dir: str):
        super().__init__(data_dir, 'leveling_tools.json')