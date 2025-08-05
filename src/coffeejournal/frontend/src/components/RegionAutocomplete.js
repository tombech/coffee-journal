import React, { useState, useEffect } from 'react';
import { apiFetch } from '../config';

function RegionAutocomplete({ 
  value = [], 
  onChange, 
  countryId = null,
  placeholder = "Search regions...", 
  disabled = false,
  id,
  'aria-label': ariaLabel,
  ...rest
}) {
  const [query, setQuery] = useState('');
  const [allRegions, setAllRegions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showSearch, setShowSearch] = useState(false);

  // Ensure value is always an array for consistency
  const currentValue = value || [];

  // Fetch regions when component mounts or country changes
  useEffect(() => {
    if (countryId) {
      fetchRegionsForCountry(countryId);
    } else {
      setAllRegions([]);
    }
  }, [countryId]);

  const fetchRegionsForCountry = async (cId) => {
    setIsLoading(true);
    try {
      const response = await apiFetch(`/countries/${cId}/regions`);
      if (response.ok) {
        const results = await response.json();
        setAllRegions(results);
      } else {
        setAllRegions([]);
      }
    } catch (error) {
      console.error('Error fetching regions:', error);
      setAllRegions([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleItemToggle = (item) => {
    if (disabled) return;

    const isSelected = currentValue.some(v => v.id === item.id);
    if (isSelected) {
      // Remove item
      const newValue = currentValue.filter(v => v.id !== item.id);
      onChange(newValue);
    } else {
      // Add item
      onChange([...currentValue, item]);
    }
  };

  const handleCreateNew = () => {
    if (!query.trim() || !countryId) return;
    
    const newItem = { 
      id: null, 
      name: query.trim(), 
      country_id: countryId,
      isNew: true 
    };
    
    // Add to local options so it appears in the chip list immediately
    setAllRegions(prev => [...prev, newItem]);
    onChange([...currentValue, newItem]);
    
    setQuery('');
    setShowSearch(true);
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && query.trim()) {
      event.preventDefault();
      const exactMatch = allRegions.find(r => r.name.toLowerCase() === query.toLowerCase());
      if (exactMatch) {
        handleItemToggle(exactMatch);
      } else {
        handleCreateNew();
      }
    }
  };

  const isItemSelected = (item) => {
    return currentValue.some(v => v.id === item.id);
  };

  // Filter regions based on search query
  const filteredRegions = allRegions.filter(region => {
    if (!query.trim()) return true;
    return region.name.toLowerCase().includes(query.toLowerCase());
  });

  // Show search input if there are many options or user is searching
  const shouldShowSearch = showSearch || allRegions.length > 5 || query.trim();

  // If no country is selected, show message
  if (!countryId) {
    return (
      <div style={{
        padding: '12px',
        textAlign: 'center',
        color: '#6c757d',
        backgroundColor: '#f8f9fa',
        border: '1px solid #dee2e6',
        borderRadius: '4px',
        fontStyle: 'italic'
      }}>
        Select a country first to choose regions
      </div>
    );
  }

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
            <span>Search or add new region ({allRegions.length} available)</span>
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
          Loading regions...
        </div>
      )}

      {/* Regions as chips */}
      {!isLoading && (
        <div style={{
          maxHeight: '250px',
          overflowY: 'auto',
          border: '1px solid #dee2e6',
          borderRadius: '4px',
          padding: '8px',
          backgroundColor: '#fafafa'
        }}>
          {/* Create new region chip */}
          {query.trim() && !filteredRegions.find(r => r.name.toLowerCase() === query.toLowerCase()) && (
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
                Press Enter or click to add new region
              </div>
            </div>
          )}

          {/* Existing regions as chips */}
          <div style={{ 
            display: 'flex', 
            flexWrap: 'wrap', 
            gap: '6px',
            alignContent: 'flex-start'
          }}>
            {filteredRegions.map((region) => {
              const selected = isItemSelected(region);
              return (
                <div
                  key={region.id}
                  onClick={() => handleItemToggle(region)}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    backgroundColor: selected ? '#1976d2' : '#ffffff',
                    color: selected ? 'white' : '#495057',
                    padding: '6px 10px',
                    borderRadius: '16px',
                    fontSize: '13px',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    border: `1px solid ${selected ? '#1976d2' : '#dee2e6'}`,
                    transition: 'all 0.15s ease',
                    userSelect: 'none',
                    minHeight: '32px',
                    boxSizing: 'border-box',
                    opacity: disabled ? 0.6 : 1,
                    boxShadow: selected ? '0 1px 3px rgba(25, 118, 210, 0.3)' : '0 1px 2px rgba(0,0,0,0.1)'
                  }}
                >
                  <span>{region.name}</span>
                  {region.isNew && (
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
                  {selected && !region.isNew && (
                    <span style={{ 
                      marginLeft: '4px', 
                      fontSize: '14px',
                      fontWeight: 'bold'
                    }}>
                      ✓
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* No results message */}
          {filteredRegions.length === 0 && query.trim() && (
            <div style={{ 
              padding: '12px', 
              textAlign: 'center', 
              color: '#6c757d',
              fontSize: '14px'
            }}>
              No regions found for "{query}". {query.trim() && 'Tap "Add" above to create new.'}
            </div>
          )}

          {/* Empty state */}
          {allRegions.length === 0 && !isLoading && (
            <div style={{ 
              padding: '12px', 
              textAlign: 'center', 
              color: '#6c757d',
              fontSize: '14px'
            }}>
              No regions available for this country.
            </div>
          )}
        </div>
      )}

      {/* Selected regions summary */}
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

export default RegionAutocomplete;