import os
import re
import shutil
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from .json_repository import (
    RoasterRepository, BeanTypeRepository, CountryRepository, RegionRepository,
    BrewMethodRepository, RecipeRepository, ProductRepository,
    BatchRepository, BrewSessionRepository, GrinderRepository,
    DecafMethodRepository, FilterRepository, KettleRepository,
    ScaleRepository, ShotRepository, ShotSessionRepository,
    BrewerRepository, PortafilterRepository, BasketRepository,
    TamperRepository, WDTToolRepository, LevelingToolRepository
)


class RepositoryFactory:
    """Factory for creating repository instances with multi-user support."""
    
    def __init__(self, storage_type: str = 'json', **kwargs):
        self.storage_type = storage_type
        self.config = kwargs
        self._repositories = {}
        # Thread lock removed - file locks are sufficient for cross-process safety
    
    def _validate_user_id(self, user_id: str) -> None:
        """Validate user_id for filesystem safety."""
        if not user_id:
            raise ValueError("user_id cannot be empty")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'\.\.', r'^\.', r'^\s*$', r'[/\\]', r'^-', 
            r'\s', r'[^\w\-_]'  # Allow only alphanumeric, dash, underscore
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, user_id):
                raise ValueError(f"Invalid user_id: {user_id}")
    
    def _get_data_dir(self, user_id: Optional[str] = None) -> str:
        """Get data directory path for a specific user."""
        base_dir = self.config.get('data_dir', 'data')
        
        if user_id is None:
            # No user specified - use base directory (backwards compatible)
            return base_dir
        
        # Validate user_id for safety
        self._validate_user_id(user_id)
        
        # User-specific directory
        user_dir = os.path.join(base_dir, 'users', user_id)
        
        # Create directory if it doesn't exist (cross-process safe with retry)
        self._ensure_directory_exists(user_dir)
        
        return user_dir
    
    def _ensure_directory_exists(self, directory_path: str, max_retries: int = 3) -> None:
        """Ensure directory exists with cross-process safety and retry logic."""
        dir_path = Path(directory_path)
        
        for attempt in range(max_retries):
            try:
                # No thread lock needed - file locks handle cross-process safety
                dir_path.mkdir(parents=True, exist_ok=True)
                    
                # Verify directory was created successfully
                if dir_path.exists() and dir_path.is_dir():
                    return
                    
            except (OSError, FileExistsError) as e:
                # Another process might have created the directory simultaneously
                if dir_path.exists() and dir_path.is_dir():
                    return
                    
                if attempt < max_retries - 1:
                    # Brief delay before retry to avoid thundering herd
                    import time
                    time.sleep(0.1 * (attempt + 1))
                    continue
                    
                raise RuntimeError(f"Failed to create directory {directory_path} after {max_retries} attempts: {e}")
        
        # Final check
        if not (dir_path.exists() and dir_path.is_dir()):
            raise RuntimeError(f"Directory {directory_path} was not created successfully")
    
    def initialize_user_with_test_data(self, user_id: str) -> None:
        """Initialize a user's data directory with a copy of test data."""
        if not user_id:
            raise ValueError("Cannot initialize data for default/empty user")
        
        self._validate_user_id(user_id)
        
        # Get paths
        test_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'test_data')
        user_dir = self._get_data_dir(user_id)
        
        # Copy all JSON files from test_data to user directory (no thread lock needed)
        if os.path.exists(test_data_dir):
            for file in os.listdir(test_data_dir):
                if file.endswith('.json'):
                    src = os.path.join(test_data_dir, file)
                    dst = os.path.join(user_dir, file)
                    shutil.copy2(src, dst)
    
    def delete_user(self, user_id: str) -> None:
        """Delete a user and all their data."""
        if not user_id:
            raise ValueError("Cannot delete default/empty user")
        
        self._validate_user_id(user_id)
        
        base_dir = self.config.get('data_dir', 'data')
        user_dir = os.path.join(base_dir, 'users', user_id)
        
        # Remove from cache (no thread lock needed)
        keys_to_remove = [k for k in self._repositories.keys() if k.startswith(f"{user_id}:")]
        for key in keys_to_remove:
            del self._repositories[key]
        
        # Remove directory with retry logic for file lock issues
        if os.path.exists(user_dir):
            import time
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    # First try to remove read-only attributes if on Windows
                    import stat
                    def remove_readonly(func, path, _):
                        """Clear the readonly bit and reattempt the removal."""
                        os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                        func(path)
                    
                    shutil.rmtree(user_dir, onerror=remove_readonly)
                    break  # Success, exit retry loop
                except OSError as e:
                    if attempt < max_attempts - 1:
                        # Wait a bit for file locks to release
                        time.sleep(0.5 * (attempt + 1))
                        # Try to forcefully close any open file handles
                        import gc
                        gc.collect()
                    else:
                        # Last attempt failed, raise the error
                        raise e
    
    def cleanup_test_users(self) -> int:
        """Remove all test user directories. Returns count of removed users."""
        base_dir = self.config.get('data_dir', 'data')
        users_dir = os.path.join(base_dir, 'users')
        count = 0
        
        if not os.path.exists(users_dir):
            return count
        
        # No thread lock needed - file locks handle cross-process safety
        for user_folder in os.listdir(users_dir):
            if user_folder.startswith('test_'):
                user_path = os.path.join(users_dir, user_folder)
                if os.path.isdir(user_path):
                    # Use same retry logic as delete_user
                    import time
                    max_attempts = 3
                    removed = False
                    for attempt in range(max_attempts):
                        try:
                            # First try to remove read-only attributes if on Windows
                            import stat
                            def remove_readonly(func, path, _):
                                """Clear the readonly bit and reattempt the removal."""
                                os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                                func(path)
                            
                            shutil.rmtree(user_path, onerror=remove_readonly)
                            removed = True
                            break  # Success, exit retry loop
                        except OSError as e:
                            if attempt < max_attempts - 1:
                                # Wait a bit for file locks to release
                                time.sleep(0.5 * (attempt + 1))
                                # Try to forcefully close any open file handles
                                import gc
                                gc.collect()
                            else:
                                # Last attempt failed, log error but continue with other users
                                print(f"Warning: Failed to remove test user directory {user_folder}: {e}")
                    
                    if removed:
                        count += 1
                        # Remove from cache
                        keys_to_remove = [k for k in self._repositories.keys() if k.startswith(f"{user_folder}:")]
                        for key in keys_to_remove:
                            del self._repositories[key]
        
        return count
    
    def _get_repository_key(self, repo_type: str, user_id: Optional[str] = None) -> str:
        """Get cache key for a repository instance."""
        effective_user_id = user_id if user_id else 'default'
        return f"{effective_user_id}:{repo_type}"
    
    def get_roaster_repository(self, user_id: Optional[str] = None) -> RoasterRepository:
        """Get or create roaster repository for a specific user."""
        key = self._get_repository_key('roaster', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = RoasterRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_bean_type_repository(self, user_id: Optional[str] = None) -> BeanTypeRepository:
        """Get or create bean type repository for a specific user."""
        key = self._get_repository_key('bean_type', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = BeanTypeRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_country_repository(self, user_id: Optional[str] = None) -> CountryRepository:
        """Get or create country repository for a specific user."""
        key = self._get_repository_key('country', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = CountryRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_region_repository(self, user_id: Optional[str] = None) -> RegionRepository:
        """Get or create region repository for a specific user."""
        key = self._get_repository_key('region', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = RegionRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_brew_method_repository(self, user_id: Optional[str] = None) -> BrewMethodRepository:
        """Get or create brew method repository for a specific user."""
        key = self._get_repository_key('brew_method', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = BrewMethodRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_recipe_repository(self, user_id: Optional[str] = None) -> RecipeRepository:
        """Get or create recipe repository for a specific user."""
        key = self._get_repository_key('recipe', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = RecipeRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_product_repository(self, user_id: Optional[str] = None) -> ProductRepository:
        """Get or create product repository for a specific user."""
        key = self._get_repository_key('product', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = ProductRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_batch_repository(self, user_id: Optional[str] = None) -> BatchRepository:
        """Get or create batch repository for a specific user."""
        key = self._get_repository_key('batch', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = BatchRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_brew_session_repository(self, user_id: Optional[str] = None) -> BrewSessionRepository:
        """Get or create brew session repository for a specific user."""
        key = self._get_repository_key('brew_session', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = BrewSessionRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_grinder_repository(self, user_id: Optional[str] = None) -> GrinderRepository:
        """Get or create grinder repository for a specific user."""
        key = self._get_repository_key('grinder', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = GrinderRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_decaf_method_repository(self, user_id: Optional[str] = None) -> DecafMethodRepository:
        """Get or create decaf method repository for a specific user."""
        key = self._get_repository_key('decaf_method', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = DecafMethodRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_filter_repository(self, user_id: Optional[str] = None) -> FilterRepository:
        """Get or create filter repository for a specific user."""
        key = self._get_repository_key('filter', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = FilterRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_kettle_repository(self, user_id: Optional[str] = None) -> KettleRepository:
        """Get or create kettle repository for a specific user."""
        key = self._get_repository_key('kettle', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = KettleRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_scale_repository(self, user_id: Optional[str] = None) -> ScaleRepository:
        """Get or create scale repository for a specific user."""
        key = self._get_repository_key('scale', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = ScaleRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_shot_repository(self, user_id: Optional[str] = None) -> ShotRepository:
        """Get or create shot repository for a specific user."""
        key = self._get_repository_key('shot', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = ShotRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_shot_session_repository(self, user_id: Optional[str] = None) -> ShotSessionRepository:
        """Get or create shot session repository for a specific user."""
        key = self._get_repository_key('shot_session', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = ShotSessionRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_brewer_repository(self, user_id: Optional[str] = None) -> BrewerRepository:
        """Get or create brewer repository for a specific user."""
        key = self._get_repository_key('brewer', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = BrewerRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_portafilter_repository(self, user_id: Optional[str] = None) -> PortafilterRepository:
        """Get or create portafilter repository for a specific user."""
        key = self._get_repository_key('portafilter', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = PortafilterRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_basket_repository(self, user_id: Optional[str] = None) -> BasketRepository:
        """Get or create basket repository for a specific user."""
        key = self._get_repository_key('basket', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = BasketRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_tamper_repository(self, user_id: Optional[str] = None) -> TamperRepository:
        """Get or create tamper repository for a specific user."""
        key = self._get_repository_key('tamper', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = TamperRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_wdt_tool_repository(self, user_id: Optional[str] = None) -> WDTToolRepository:
        """Get or create WDT tool repository for a specific user."""
        key = self._get_repository_key('wdt_tool', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = WDTToolRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]
    
    def get_leveling_tool_repository(self, user_id: Optional[str] = None) -> LevelingToolRepository:
        """Get or create leveling tool repository for a specific user."""
        key = self._get_repository_key('leveling_tool', user_id)
        if key not in self._repositories:
            if self.storage_type == 'json':
                self._repositories[key] = LevelingToolRepository(self._get_data_dir(user_id))
            else:
                raise NotImplementedError(f"Storage type {self.storage_type} not implemented")
        return self._repositories[key]

    def invalidate_all_caches(self, user_id: Optional[str] = None):
        """Invalidate all repository caches for a specific user or globally."""
        if user_id:
            # Invalidate caches for specific user
            keys_to_invalidate = [key for key in self._repositories.keys() if key.endswith(f":{user_id}")]
        else:
            # Invalidate all repository caches
            keys_to_invalidate = list(self._repositories.keys())

        for key in keys_to_invalidate:
            if key in self._repositories:
                self._repositories[key].invalidate_cache()


# Global factory instance
_factory = None


def get_repository_factory() -> RepositoryFactory:
    """Get the global repository factory instance."""
    global _factory
    if _factory is None:
        _factory = RepositoryFactory()
    return _factory


def init_repository_factory(storage_type: str = 'json', **kwargs):
    """Initialize the global repository factory."""
    global _factory
    _factory = RepositoryFactory(storage_type, **kwargs)