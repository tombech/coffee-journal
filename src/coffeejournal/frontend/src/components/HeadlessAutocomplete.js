import React, { useState, useEffect } from 'react';
import { Combobox } from '@headlessui/react';
import { apiFetch } from '../config';

function HeadlessAutocomplete({ 
  lookupType, 
  value, 
  onChange, 
  placeholder = "Start typing to search...", 
  required = false, 
  disabled = false,
  id,
  'aria-label': ariaLabel,
  ...rest
}) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Initialize query from value prop
  useEffect(() => {
    if (value && typeof value === 'object' && value.name) {
      setQuery(value.name);
    } else if (typeof value === 'string') {
      setQuery(value);
    } else {
      setQuery('');
    }
  }, [value]);

  // Debounced search function
  useEffect(() => {
    const searchTimeout = setTimeout(() => {
      if (query.trim() && query.length >= 2) {
        searchLookups(query.trim());
      } else {
        setSuggestions([]);
      }
    }, 300);

    return () => clearTimeout(searchTimeout);
  }, [query, lookupType]);

  const searchLookups = async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 2) return;

    setIsLoading(true);
    try {
      const response = await apiFetch(`/${lookupType}/search?q=${encodeURIComponent(searchQuery)}`);
      if (response.ok) {
        const results = await response.json();
        setSuggestions(results);
      } else {
        setSuggestions([]);
      }
    } catch (error) {
      console.error('Error searching lookups:', error);
      setSuggestions([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectionChange = (selectedOption) => {
    if (selectedOption) {
      onChange(selectedOption);
      setQuery(selectedOption.name);
    }
  };

  const handleInputChange = (inputValue) => {
    setQuery(inputValue);
    
    // If user clears the input, clear the selection
    if (!inputValue.trim()) {
      onChange({ id: null, name: '', isNew: false });
    }
  };

  const handleInputBlur = () => {
    // If user typed something that's not in suggestions, create new item
    if (query.trim() && !suggestions.find(s => s.name.toLowerCase() === query.toLowerCase())) {
      onChange({ id: null, name: query.trim(), isNew: true });
    }
  };

  // Filter suggestions to show current query + matches
  const filteredSuggestions = suggestions.filter(suggestion =>
    suggestion.name.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <Combobox value={value || { id: null, name: '' }} onChange={handleSelectionChange}>
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
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          displayValue={(option) => option?.name || ''}
          onChange={(event) => handleInputChange(event.target.value)}
          onBlur={handleInputBlur}
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

        <Combobox.Options 
          static={process.env.NODE_ENV === 'test'}
          style={{
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
          }}
        >
          {filteredSuggestions.map((suggestion) => (
            <Combobox.Option
              key={suggestion.id}
              value={suggestion}
              style={{ padding: '8px 12px', cursor: 'pointer' }}
            >
              {({ active, selected }) => (
                <div style={{
                  backgroundColor: active ? '#f0f0f0' : 'white',
                  fontWeight: selected ? 'bold' : 'normal',
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
              value={{ id: null, name: query.trim(), isNew: true }}
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
      </div>
    </Combobox>
  );
}

export default HeadlessAutocomplete;