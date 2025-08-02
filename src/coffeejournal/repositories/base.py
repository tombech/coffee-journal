from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, date


class BaseRepository(ABC):
    """Abstract base class for repository pattern implementation."""
    
    @abstractmethod
    def find_all(self) -> List[Dict[str, Any]]:
        """Get all entities."""
        pass
    
    @abstractmethod
    def find_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new entity."""
        pass
    
    @abstractmethod
    def update(self, id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing entity."""
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete entity by ID."""
        pass


class LookupRepository(BaseRepository):
    """Base repository for lookup tables (Roaster, BeanType, etc.)"""
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find entity by name."""
        pass
    
    @abstractmethod
    def get_or_create(self, name: str) -> Dict[str, Any]:
        """Get existing entity by name or create new one."""
        pass
    
    @abstractmethod
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search entities by substring match on name and short_form (if available)."""
        pass