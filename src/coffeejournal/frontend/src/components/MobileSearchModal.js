import React, { useState, useEffect, useRef } from 'react';
import { apiFetch } from '../config';

function MobileSearchModal({ 
  isOpen, 
  onClose, 
  lookupType, 
  value, 
  onChange, 
  placeholder = "Search...",
  multiSelect = false 
}) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedItems, setSelectedItems] = useState(multiSelect ? (value || []) : null);
  const searchInputRef = useRef(null);

  // Focus search input when modal opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      setTimeout(() => {
        searchInputRef.current.focus();
      }, 100);
    }
  }, [isOpen]);

  // Search functionality
  useEffect(() => {
    const searchTimeout = setTimeout(() => {
      if (query.trim() && query.length >= 2) {
        searchLookups(query.trim());
      } else if (query.trim().length === 0) {
        // Show all options when no query
        loadAllOptions();
      }
    }, 300);

    return () => clearTimeout(searchTimeout);
  }, [query, lookupType]);

  const loadAllOptions = async () => {
    setIsLoading(true);
    try {
      const response = await apiFetch(`/${lookupType}`);
      if (response.ok) {
        const results = await response.json();
        setSuggestions(results.slice(0, 50)); // Limit to 50 items
      }
    } catch (error) {
      console.error('Error loading options:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const searchLookups = async (searchQuery) => {
    setIsLoading(true);
    try {
      const response = await apiFetch(`/${lookupType}/search?q=${encodeURIComponent(searchQuery)}`);
      if (response.ok) {
        const results = await response.json();
        setSuggestions(results);
      }
    } catch (error) {
      console.error('Error searching:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleItemSelect = (item) => {
    if (multiSelect) {
      const isSelected = selectedItems.some(i => i.id === item.id);
      if (isSelected) {
        setSelectedItems(selectedItems.filter(i => i.id !== item.id));
      } else {
        setSelectedItems([...selectedItems, item]);
      }
    } else {
      onChange(item);
      onClose();
    }
  };

  const handleDone = () => {
    if (multiSelect) {
      onChange(selectedItems);
    }
    onClose();
  };

  const handleCreateNew = () => {
    const newItem = { id: null, name: query.trim(), isNew: true };
    if (multiSelect) {
      onChange([...selectedItems, newItem]);
    } else {
      onChange(newItem);
    }
    onClose();
  };

  if (!isOpen) return null;

  const isItemSelected = (item) => {
    if (multiSelect) {
      return selectedItems.some(i => i.id === item.id);
    }
    return value && value.id === item.id;
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'white',
      zIndex: 10000,
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        padding: '12px',
        borderBottom: '1px solid #dee2e6',
        backgroundColor: '#f8f9fa'
      }}>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '18px',
            padding: '4px 8px',
            cursor: 'pointer'
          }}
          aria-label="Cancel"
        >
          ←
        </button>
        <h3 style={{ 
          flex: 1, 
          margin: '0 12px',
          fontSize: '16px',
          fontWeight: 'normal'
        }}>
          Select {lookupType.replace(/_/g, ' ')}
        </h3>
        {multiSelect && (
          <button
            onClick={handleDone}
            style={{
              background: '#007bff',
              color: 'white',
              border: 'none',
              padding: '6px 12px',
              borderRadius: '4px',
              fontSize: '14px',
              cursor: 'pointer'
            }}
          >
            Done{selectedItems.length > 0 ? ` (${selectedItems.length})` : ''}
          </button>
        )}
      </div>

      {/* Search Input */}
      <div style={{ padding: '12px', borderBottom: '1px solid #dee2e6' }}>
        <input
          ref={searchInputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          style={{
            width: '100%',
            padding: '8px 12px',
            fontSize: '16px', // Prevents zoom on iOS
            border: '1px solid #ced4da',
            borderRadius: '4px',
            boxSizing: 'border-box'
          }}
        />
      </div>


      {/* Results as Horizontal Chips */}
      <div style={{ 
        flex: 1, 
        overflowY: 'auto',
        padding: '12px',
        WebkitOverflowScrolling: 'touch' // Smooth scrolling on iOS
      }}>
        {isLoading ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#6c757d' }}>
            Searching...
          </div>
        ) : (
          <>
            {/* Create new option as special chip */}
            {query.trim() && !suggestions.find(s => s.name.toLowerCase() === query.toLowerCase()) && (
              <div style={{ marginBottom: '12px' }}>
                <div
                  onClick={handleCreateNew}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    backgroundColor: '#fff3cd',
                    color: '#856404',
                    padding: '6px 12px',
                    borderRadius: '20px',
                    fontSize: '14px',
                    cursor: 'pointer',
                    border: '1px solid #ffeaa7',
                    fontWeight: '500'
                  }}
                >
                  + Create "{query.trim()}"
                </div>
              </div>
            )}

            {/* Existing options as chips */}
            <div style={{ 
              display: 'flex', 
              flexWrap: 'wrap', 
              gap: '8px',
              alignContent: 'flex-start'
            }}>
              {suggestions.map((item) => {
                const selected = isItemSelected(item);
                return (
                  <div
                    key={item.id}
                    onClick={() => handleItemSelect(item)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      backgroundColor: selected ? '#1976d2' : '#f8f9fa',
                      color: selected ? 'white' : '#495057',
                      padding: '8px 12px',
                      borderRadius: '20px',
                      fontSize: '14px',
                      cursor: 'pointer',
                      border: `1px solid ${selected ? '#1976d2' : '#dee2e6'}`,
                      transition: 'all 0.2s ease',
                      userSelect: 'none',
                      minHeight: '36px',
                      boxSizing: 'border-box'
                    }}
                  >
                    <span>{item.name}</span>
                    {selected && (
                      <span style={{ 
                        marginLeft: '6px', 
                        fontSize: '16px',
                        fontWeight: 'bold'
                      }}>
                        ✓
                      </span>
                    )}
                  </div>
                );
              })}
            </div>

            {suggestions.length === 0 && query.trim() && (
              <div style={{ 
                padding: '20px', 
                textAlign: 'center', 
                color: '#6c757d' 
              }}>
                No results found. {query.trim() && 'Tap "Create" above to add new.'}
              </div>
            )}

            {suggestions.length === 0 && !query.trim() && (
              <div style={{ 
                padding: '20px', 
                textAlign: 'center', 
                color: '#6c757d' 
              }}>
                Start typing to search, or tap Done to finish selecting.
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default MobileSearchModal;