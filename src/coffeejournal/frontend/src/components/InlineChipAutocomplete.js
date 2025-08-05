import React, { useState, useEffect } from 'react';
import { apiFetch } from '../config';

function InlineChipAutocomplete({ 
  lookupType, 
  value = [], 
  onChange, 
  placeholder = "Search...", 
  disabled = false,
  multiSelect = false,
  maxHeight = '200px',
  singleSelectStyle = false,
  id,
  'aria-label': ariaLabel,
  ...rest
}) {
  const [query, setQuery] = useState('');
  const [allOptions, setAllOptions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showSearch, setShowSearch] = useState(false);

  // Ensure value is always an array for consistency
  const currentValue = multiSelect ? (value || []) : (value ? [value] : []);

  // Fetch all options when component mounts
  useEffect(() => {
    fetchAllOptions();
  }, [lookupType]);

  const fetchAllOptions = async () => {
    setIsLoading(true);
    try {
      const response = await apiFetch(`/${lookupType}`);
      if (response.ok) {
        const results = await response.json();
        setAllOptions(results);
      } else {
        setAllOptions([]);
      }
    } catch (error) {
      console.error('Error fetching options:', error);
      setAllOptions([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleItemToggle = (item) => {
    if (disabled) return;

    if (multiSelect) {
      const isSelected = currentValue.some(v => v.id === item.id);
      if (isSelected) {
        // Remove item
        const newValue = currentValue.filter(v => v.id !== item.id);
        onChange(newValue);
      } else {
        // Add item
        onChange([...currentValue, item]);
      }
    } else {
      // Single select
      const isSelected = currentValue.some(v => v.id === item.id);
      if (isSelected) {
        onChange(null); // Deselect
      } else {
        onChange(item); // Select
      }
    }
  };

  const handleCreateNew = () => {
    if (!query.trim()) return;
    
    const newItem = { id: null, name: query.trim(), isNew: true };
    
    // Add to local options so it appears in the chip list immediately
    setAllOptions(prev => [...prev, newItem]);
    
    if (multiSelect) {
      onChange([...currentValue, newItem]);
    } else {
      onChange(newItem);
    }
    
    setQuery('');
    // Keep search open after creating to allow more quick additions
    setShowSearch(true);
  };

  // Also support Enter key for quick creation
  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && query.trim()) {
      event.preventDefault();
      // Check if exact match exists
      const exactMatch = allOptions.find(o => o.name.toLowerCase() === query.toLowerCase());
      if (exactMatch) {
        // Select existing item
        handleItemToggle(exactMatch);
      } else {
        // Create new item
        handleCreateNew();
      }
    }
  };

  const isItemSelected = (item) => {
    return currentValue.some(v => v.id === item.id);
  };

  // Filter options based on search query
  const filteredOptions = allOptions.filter(option => {
    if (!query.trim()) return true;
    return option.name.toLowerCase().includes(query.toLowerCase());
  });

  // Show search input if there are many options or user is searching
  const shouldShowSearch = showSearch || allOptions.length > 5 || query.trim();

  return (
    <div style={{ width: '100%' }}>
      {/* Search input (conditional) */}
      {shouldShowSearch && (
        <div style={{ marginBottom: '12px' }}>
          <input
            type="text"
            id={id}
            aria-label={ariaLabel}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setShowSearch(true)}
            placeholder={placeholder}
            disabled={disabled}
            style={{
              width: '100%',
              padding: '8px 12px',
              fontSize: '14px',
              border: '1px solid #ced4da',
              borderRadius: '4px',
              boxSizing: 'border-box'
            }}
            {...rest}
          />
        </div>
      )}

      {/* Show search button if search is hidden */}
      {!shouldShowSearch && (
        <div style={{ marginBottom: '12px' }}>
          <button
            type="button"
            onClick={() => setShowSearch(true)}
            style={{
              padding: '8px 16px',
              fontSize: '14px',
              border: '1px solid #007bff',
              borderRadius: '6px',
              backgroundColor: '#ffffff',
              color: '#007bff',
              cursor: 'pointer',
              fontWeight: '500',
              transition: 'all 0.15s ease',
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = '#007bff';
              e.target.style.color = 'white';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = '#ffffff';
              e.target.style.color = '#007bff';
            }}
          >
            <span>🔍</span>
            <span>
              {singleSelectStyle ? 'Select one' : 'Search or add new'} {lookupType.replace(/_/g, ' ').slice(0, -1)} ({allOptions.length} available)
            </span>
          </button>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div style={{ 
          padding: '12px', 
          textAlign: 'center', 
          color: '#6c757d',
          fontSize: '14px'
        }}>
          Loading {lookupType.replace(/_/g, ' ')}...
        </div>
      )}

      {/* Options as chips */}
      {!isLoading && (
        <div style={{
          maxHeight: maxHeight,
          overflowY: 'auto',
          border: '1px solid #dee2e6',
          borderRadius: '4px',
          padding: '8px',
          backgroundColor: '#fafafa'
        }}>
          {/* Create new option chip */}
          {query.trim() && !filteredOptions.find(o => o.name.toLowerCase() === query.toLowerCase()) && (
            <div style={{ marginBottom: '12px' }}>
              <div
                onClick={handleCreateNew}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  backgroundColor: '#d4edda',
                  color: '#155724',
                  padding: '8px 14px',
                  borderRadius: '18px',
                  fontSize: '14px',
                  cursor: disabled ? 'not-allowed' : 'pointer',
                  border: '2px solid #c3e6cb',
                  fontWeight: '600',
                  opacity: disabled ? 0.6 : 1,
                  boxShadow: '0 2px 4px rgba(40, 167, 69, 0.2)',
                  transition: 'all 0.15s ease'
                }}
                onMouseEnter={(e) => {
                  if (!disabled) {
                    e.target.style.backgroundColor = '#c3e6cb';
                    e.target.style.transform = 'translateY(-1px)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!disabled) {
                    e.target.style.backgroundColor = '#d4edda';
                    e.target.style.transform = 'translateY(0)';
                  }
                }}
              >
                <span style={{ marginRight: '6px', fontSize: '16px' }}>+</span>
                <span>Add "{query.trim()}"</span>
              </div>
              <div style={{ 
                fontSize: '11px', 
                color: '#6c757d', 
                marginTop: '4px',
                fontStyle: 'italic'
              }}>
                Press Enter or click to add new {lookupType.replace(/_/g, ' ').slice(0, -1)}
              </div>
            </div>
          )}

          {/* Existing options as chips */}
          <div style={{ 
            display: 'flex', 
            flexWrap: 'wrap', 
            gap: '6px',
            alignContent: 'flex-start'
          }}>
            {filteredOptions.map((option) => {
              const selected = isItemSelected(option);
              
              // Different styles for single vs multi-select
              const chipStyle = singleSelectStyle ? {
                // Single-select: Radio button style with emphasis on the selected item
                backgroundColor: selected ? '#28a745' : '#ffffff',
                color: selected ? 'white' : '#495057',
                padding: selected ? '8px 12px' : '6px 10px',
                borderRadius: selected ? '20px' : '16px',
                fontSize: selected ? '14px' : '13px',
                fontWeight: selected ? '600' : '400',
                border: selected ? '2px solid #28a745' : '1px solid #dee2e6',
                boxShadow: selected ? '0 2px 6px rgba(40, 167, 69, 0.4)' : '0 1px 2px rgba(0,0,0,0.1)',
                transform: selected ? 'translateY(-1px)' : 'none'
              } : {
                // Multi-select: Standard chip style
                backgroundColor: selected ? '#1976d2' : '#ffffff',
                color: selected ? 'white' : '#495057',
                padding: '6px 10px',
                borderRadius: '16px',
                fontSize: '13px',
                fontWeight: '400',
                border: `1px solid ${selected ? '#1976d2' : '#dee2e6'}`,
                boxShadow: selected ? '0 1px 3px rgba(25, 118, 210, 0.3)' : '0 1px 2px rgba(0,0,0,0.1)',
                transform: 'none'
              };

              return (
                <div
                  key={option.id}
                  onClick={() => handleItemToggle(option)}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    transition: 'all 0.15s ease',
                    userSelect: 'none',
                    minHeight: '32px',
                    boxSizing: 'border-box',
                    opacity: disabled ? 0.6 : 1,
                    ...chipStyle
                  }}
                >
                  <span>{option.name}</span>
                  {option.isNew && (
                    <span style={{ 
                      marginLeft: '4px', 
                      fontSize: '10px',
                      backgroundColor: selected ? 'rgba(255,255,255,0.3)' : '#28a745',
                      color: selected ? 'white' : 'white',
                      padding: '1px 4px',
                      borderRadius: '6px',
                      fontWeight: 'bold'
                    }}>
                      NEW
                    </span>
                  )}
                  {selected && !option.isNew && (
                    <span style={{ 
                      marginLeft: '4px', 
                      fontSize: singleSelectStyle ? '16px' : '14px',
                      fontWeight: 'bold'
                    }}>
                      {singleSelectStyle ? '●' : '✓'}
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* No results message */}
          {filteredOptions.length === 0 && query.trim() && (
            <div style={{ 
              padding: '12px', 
              textAlign: 'center', 
              color: '#6c757d',
              fontSize: '14px'
            }}>
              No results found for "{query}". {query.trim() && 'Tap "Create" above to add new.'}
            </div>
          )}

          {/* Empty state */}
          {allOptions.length === 0 && !isLoading && (
            <div style={{ 
              padding: '12px', 
              textAlign: 'center', 
              color: '#6c757d',
              fontSize: '14px'
            }}>
              No {lookupType.replace(/_/g, ' ')} available.
            </div>
          )}
        </div>
      )}

      {/* Selected items summary */}
      {currentValue.length > 0 && (
        <div style={{ 
          marginTop: '8px', 
          fontSize: '12px', 
          color: '#6c757d',
          textAlign: 'right'
        }}>
          {currentValue.length} selected
        </div>
      )}
    </div>
  );
}

export default InlineChipAutocomplete;