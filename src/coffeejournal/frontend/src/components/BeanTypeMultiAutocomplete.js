import React, { useState, useEffect } from 'react';
import { apiFetch } from '../config';

function BeanTypeMultiAutocomplete({ 
  value = [], 
  onChange, 
  placeholder = "Start typing to search bean types...", 
  disabled = false,
  id,
  'aria-label': ariaLabel,
  ...rest
}) {
  const [query, setQuery] = useState('');
  const [allBeanTypes, setAllBeanTypes] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch all bean types when component mounts
  useEffect(() => {
    fetchAllBeanTypes();
  }, []); // No dependencies needed, only fetch once

  const fetchAllBeanTypes = async () => {
    setIsLoading(true);
    try {
      const response = await apiFetch('/bean_types');
      if (response.ok) {
        const results = await response.json();
        setAllBeanTypes(results);
      } else {
        setAllBeanTypes([]);
      }
    } catch (error) {
      console.error('Error fetching bean types:', error);
      setAllBeanTypes([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (event) => {
    const inputValue = event.target.value;
    setQuery(inputValue);
    
    // Check if the user selected from datalist (input value matches an option exactly)
    const matchingBeanType = allBeanTypes.find(bt => bt.name === inputValue);
    if (matchingBeanType && !value.some(item => item.id === matchingBeanType.id)) {
      // User clicked on a datalist option, select it immediately
      onChange([...value, matchingBeanType]);
      setQuery('');
    }
  };

  const handleInputKeyDown = (event) => {
    if (event.key === 'Enter' && query.trim()) {
      event.preventDefault();
      handleSelection(query.trim());
    }
  };

  const handleSelection = (selectedName) => {
    if (!selectedName || !selectedName.trim()) return;
    
    const trimmedName = selectedName.trim();
    
    // Check if already selected
    if (value.some(item => item.name.toLowerCase() === trimmedName.toLowerCase())) {
      setQuery('');
      return;
    }
    
    // Find existing bean type or create new one
    const existingBeanType = allBeanTypes.find(bt => bt.name.toLowerCase() === trimmedName.toLowerCase());
    
    const newItem = existingBeanType || { 
      id: null, 
      name: trimmedName, 
      isNew: true
    };
    
    onChange([...value, newItem]);
    setQuery('');
  };

  const handleInputBlur = () => {
    // Auto-select on blur if there's a value (for manual typing)
    if (query.trim() && !allBeanTypes.find(bt => bt.name === query.trim())) {
      handleSelection(query.trim());
    } else {
      setQuery(''); // Clear if it was just partial typing
    }
  };

  const removeItem = (indexToRemove) => {
    const newValue = value.filter((_, index) => index !== indexToRemove);
    onChange(newValue);
  };

  // Handle mobile datalist issues (borrowed from BrewSessionForm)
  const handleMobileDatalistFocus = (e) => {
    if (/Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
      e.target.removeAttribute('list');
    }
  };

  const handleMobileDatalistBlur = (e) => {
    if (/Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
      const listId = e.target.getAttribute('data-list');
      if (listId) {
        e.target.setAttribute('list', listId);
      }
    }
  };

  // Filter available bean types to exclude already selected ones
  const availableBeanTypes = allBeanTypes.filter(beanType => 
    !value.some(selected => selected.id === beanType.id)
  );

  const datalistId = `bean-types-options-${id || 'default'}`;

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

      {/* Input with datalist for adding new items */}
      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        <input
          type="text"
          id={id}
          aria-label={ariaLabel}
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleInputKeyDown}
          onBlur={(e) => {
            handleMobileDatalistBlur(e);
            handleInputBlur();
          }}
          onFocus={handleMobileDatalistFocus}
          list={datalistId}
          data-list={datalistId}
          placeholder={availableBeanTypes.length > 0 ? "Start typing or select from dropdown..." : "Type a bean type name..."}
          disabled={disabled}
          style={{
            width: '100%',
            fontSize: '14px',
            padding: '6px 48px 6px 6px', // More space for dropdown arrow
            height: '32px',
            boxSizing: 'border-box',
            border: '1px solid #ccc',
            borderRadius: '4px'
          }}
          {...rest}
        />
        
        {/* Dropdown arrow indicator */}
        {availableBeanTypes.length > 0 && (
          <div
            style={{
              position: 'absolute',
              right: query ? '28px' : '8px',
              top: '50%',
              transform: 'translateY(-50%)',
              fontSize: '12px',
              color: '#666',
              pointerEvents: 'none',
              userSelect: 'none'
            }}
            title="Available options in dropdown"
          >
            ▼
          </div>
        )}
        
        {query && (
          <button
            type="button"
            onClick={() => setQuery('')}
            style={{
              position: 'absolute',
              right: '4px',
              background: 'none',
              border: 'none',
              fontSize: '16px',
              color: '#666',
              cursor: 'pointer',
              padding: '0',
              width: '20px',
              height: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            title="Clear input"
          >
            ×
          </button>
        )}

        {isLoading && (
          <div style={{
            position: 'absolute',
            right: query ? '28px' : (availableBeanTypes.length > 0 ? '28px' : '8px'),
            top: '50%',
            transform: 'translateY(-50%)',
            fontSize: '12px',
            color: '#666'
          }}>
            Loading...
          </div>
        )}
      </div>

      {/* Datalist with available bean types */}
      <datalist id={datalistId}>
        {availableBeanTypes.map((beanType) => (
          <option key={beanType.id} value={beanType.name} />
        ))}
      </datalist>
    </div>
  );
}

export default BeanTypeMultiAutocomplete;