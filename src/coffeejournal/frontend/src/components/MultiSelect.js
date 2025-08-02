import React, { useState } from 'react';

function MultiSelect({ name, values = [], onChange, options = [], placeholder = "Type to add..." }) {
  const [inputValue, setInputValue] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  // Ensure values is always an array
  const safeValues = Array.isArray(values) ? values : [];
  const safeOptions = Array.isArray(options) ? options : [];

  const handleAddItem = (item) => {
    if (item && !safeValues.includes(item)) {
      const newValues = [...safeValues, item];
      onChange(name, newValues);
    }
    setInputValue('');
    setShowSuggestions(false);
  };

  const handleRemoveItem = (index) => {
    const newValues = [...safeValues];
    newValues.splice(index, 1);
    onChange(name, newValues);
  };

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
    setShowSuggestions(true);
  };

  const handleInputKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddItem(inputValue.trim());
    }
  };

  const handleSuggestionClick = (optionName) => {
    handleAddItem(optionName);
  };

  const filteredOptions = safeOptions
    .filter(opt => opt && opt.name && typeof opt.name === 'string' && opt.name.toLowerCase().includes(inputValue.toLowerCase()))
    .filter(opt => opt && opt.name && !safeValues.includes(opt.name));

  return (
    <div style={{ position: 'relative' }}>
      <div style={{ 
        border: '1px solid #ccc', 
        borderRadius: '4px', 
        padding: '4px',
        minHeight: '38px',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '4px',
        alignItems: 'center'
      }}>
        {safeValues.map((value, index) => (
          <span key={index} style={{
            backgroundColor: '#e0e0e0',
            padding: '4px 8px',
            borderRadius: '3px',
            display: 'inline-flex',
            alignItems: 'center',
            fontSize: '14px'
          }}>
            {value}
            <button
              type="button"
              onClick={() => handleRemoveItem(index)}
              style={{
                marginLeft: '4px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '0 2px',
                fontSize: '16px',
                lineHeight: '1',
                color: '#666'
              }}
            >
              ×
            </button>
          </span>
        ))}
        <input
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleInputKeyDown}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
          placeholder={safeValues.length === 0 ? placeholder : ""}
          style={{
            border: 'none',
            outline: 'none',
            flex: '1',
            minWidth: '100px',
            padding: '4px'
          }}
        />
      </div>
      
      {showSuggestions && inputValue && filteredOptions.length > 0 && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          backgroundColor: 'white',
          border: '1px solid #ccc',
          borderTop: 'none',
          borderRadius: '0 0 4px 4px',
          maxHeight: '150px',
          overflowY: 'auto',
          zIndex: 1000
        }}>
          {filteredOptions.map((option) => (
            <div
              key={option.id}
              onMouseDown={(e) => {
                e.preventDefault(); // Prevent input blur
                handleSuggestionClick(option.name);
              }}
              style={{
                padding: '8px',
                cursor: 'pointer',
                backgroundColor: 'white'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
            >
              {option.name}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default MultiSelect;