import React, { useState, useEffect } from 'react';
import { Combobox } from '@headlessui/react';
import { apiFetch } from '../config';

function RegionMultiAutocomplete({ 
  countryId,
  value = [], 
  onChange, 
  placeholder = "Start typing to search regions...", 
  disabled = false,
  id,
  'aria-label': ariaLabel,
  ...rest
}) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Debounced search function
  useEffect(() => {
    const searchTimeout = setTimeout(() => {
      if (query.trim() && query.length >= 2) {
        searchRegions(query.trim());
      } else {
        setSuggestions([]);
      }
    }, 300);

    return () => clearTimeout(searchTimeout);
  }, [query, countryId]);

  const searchRegions = async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 2) return;

    setIsLoading(true);
    try {
      // First get all regions from search
      const response = await apiFetch(`/regions/search?q=${encodeURIComponent(searchQuery)}`);
      if (response.ok) {
        const results = await response.json();
        
        // Filter by country if countryId is provided
        let filteredResults = results;
        if (countryId) {
          filteredResults = results.filter(region => region.country_id === countryId);
        }
        
        // Filter out already selected items
        const availableResults = filteredResults.filter(result => 
          !value.some(selected => selected.id === result.id && selected.name === result.name)
        );
        setSuggestions(availableResults);
      } else {
        setSuggestions([]);
      }
    } catch (error) {
      console.error('Error searching regions:', error);
      setSuggestions([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectionChange = (selectedOption) => {
    if (selectedOption && !value.some(item => item.id === selectedOption.id && item.name === selectedOption.name)) {
      onChange([...value, selectedOption]);
      setQuery(''); // Clear input after selection
    }
  };

  const handleInputChange = (inputValue) => {
    setQuery(inputValue);
  };

  const handleInputKeyDown = (event) => {
    if (event.key === 'Enter' && query.trim()) {
      event.preventDefault();
      // Create new item if not in suggestions
      if (!suggestions.find(s => s.name.toLowerCase() === query.toLowerCase())) {
        const newItem = { 
          id: null, 
          name: query.trim(), 
          isNew: true,
          country_id: countryId // Associate with current country
        };
        if (!value.some(item => item.name === newItem.name)) {
          onChange([...value, newItem]);
          setQuery('');
        }
      }
    }
  };

  const removeItem = (indexToRemove) => {
    const newValue = value.filter((_, index) => index !== indexToRemove);
    onChange(newValue);
  };

  // Filter suggestions to show current query + matches
  const filteredSuggestions = suggestions.filter(suggestion =>
    suggestion.name.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div>
      {/* Selected items as chips */}
      {value.length > 0 && (
        <div style={{ marginBottom: '8px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
          {value.map((item, index) => (
            <div
              key={`${item.id}-${item.name}-${index}`}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                backgroundColor: '#e3f2fd',
                color: '#1976d2',
                padding: '2px 6px',
                borderRadius: '12px',
                fontSize: '12px',
                border: '1px solid #bbdefb'
              }}
            >
              <span>{item.name}</span>
              <button
                type="button"
                onClick={() => removeItem(index)}
                style={{
                  marginLeft: '4px',
                  backgroundColor: 'transparent',
                  border: 'none',
                  color: '#1976d2',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  padding: '0',
                  lineHeight: '1'
                }}
                title={`Remove ${item.name}`}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Combobox for adding new items */}
      <Combobox value={null} onChange={handleSelectionChange}>
        <div style={{ position: 'relative' }}>
          <Combobox.Input
            id={id}
            aria-label={ariaLabel}
            style={{
              width: '100%',
              fontSize: '14px',
              padding: '6px',
              height: '32px',
              boxSizing: 'border-box',
              border: '1px solid #ccc',
              borderRadius: '4px'
            }}
            placeholder={countryId ? placeholder : "Please select a country first"}
            disabled={disabled || !countryId}
            value={query}
            onChange={(event) => handleInputChange(event.target.value)}
            onKeyDown={handleInputKeyDown}
            {...rest}
          />

          {isLoading && (
            <div style={{
              position: 'absolute',
              right: '8px',
              top: '50%',
              transform: 'translateY(-50%)',
              fontSize: '12px',
              color: '#666'
            }}>
              Searching...
            </div>
          )}

          {(filteredSuggestions.length > 0 || (query.trim() && !filteredSuggestions.find(s => s.name.toLowerCase() === query.toLowerCase()))) && (
            <Combobox.Options style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              right: 0,
              backgroundColor: 'white',
              border: '1px solid #ccc',
              borderTop: 'none',
              borderRadius: '0 0 4px 4px',
              maxHeight: '200px',
              overflowY: 'auto',
              zIndex: 1000,
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}>
              {filteredSuggestions.map((suggestion) => (
                <Combobox.Option
                  key={suggestion.id}
                  value={suggestion}
                  style={{ padding: '8px 12px', cursor: 'pointer' }}
                >
                  {({ active }) => (
                    <div style={{
                      backgroundColor: active ? '#f0f0f0' : 'white',
                      fontSize: '14px'
                    }}>
                      {suggestion.name}
                    </div>
                  )}
                </Combobox.Option>
              ))}
              
              {/* Show option to create new item if no exact match */}
              {query.trim() && !filteredSuggestions.find(s => s.name.toLowerCase() === query.toLowerCase()) && (
                <Combobox.Option
                  value={{ id: null, name: query.trim(), isNew: true, country_id: countryId }}
                  style={{ padding: '8px 12px', cursor: 'pointer' }}
                >
                  {({ active }) => (
                    <div style={{
                      backgroundColor: active ? '#f0f0f0' : 'white',
                      fontSize: '14px',
                      fontStyle: 'italic',
                      borderTop: filteredSuggestions.length > 0 ? '1px solid #eee' : 'none'
                    }}>
                      Create "{query.trim()}"
                    </div>
                  )}
                </Combobox.Option>
              )}
            </Combobox.Options>
          )}
        </div>
      </Combobox>
    </div>
  );
}

export default RegionMultiAutocomplete;