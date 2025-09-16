import React, { useState, useRef, useEffect } from 'react';

const BEAN_PROCESS_OPTIONS = [
  "Washed (wet)",
  "Natural (dry)",
  "Honey",
  "Semi-washed (wet-hulled)",
  "Anaerobic",
  "Carbonic Maceration",
  "Other"
];

function BeanProcessMultiSelect({
  value = [],
  onChange,
  placeholder = "Select processing methods...",
  disabled = false,
  id,
  'aria-label': ariaLabel,
  'data-testid': testId,
  ...rest
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const containerRef = useRef(null);
  const inputRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const selectedValues = Array.isArray(value) ? value : (value ? [value] : []);

  const filteredOptions = BEAN_PROCESS_OPTIONS.filter(option =>
    option.toLowerCase().includes(searchTerm.toLowerCase()) &&
    !selectedValues.includes(option)
  );

  const handleToggleOption = (option) => {
    let newValue;
    if (selectedValues.includes(option)) {
      // Remove the option
      newValue = selectedValues.filter(v => v !== option);
    } else {
      // Add the option
      newValue = [...selectedValues, option];
    }

    if (onChange) {
      onChange(newValue);
    }

    // Clear search and keep dropdown open for multiple selections
    setSearchTerm('');
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  const handleRemoveChip = (optionToRemove) => {
    const newValue = selectedValues.filter(v => v !== optionToRemove);
    if (onChange) {
      onChange(newValue);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      setSearchTerm('');
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredOptions.length === 1) {
        handleToggleOption(filteredOptions[0]);
      }
    } else if (e.key === 'Backspace' && searchTerm === '' && selectedValues.length > 0) {
      // Remove last chip when backspacing with empty search
      handleRemoveChip(selectedValues[selectedValues.length - 1]);
    }
  };

  return (
    <div
      ref={containerRef}
      style={{ position: 'relative', width: '100%' }}
      {...rest}
    >
      <div
        onClick={() => !disabled && setIsOpen(true)}
        style={{
          minHeight: '38px',
          padding: '8px 12px',
          border: '1px solid #ced4da',
          borderRadius: '4px',
          backgroundColor: disabled ? '#f8f9fa' : '#fff',
          cursor: disabled ? 'not-allowed' : 'text',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: '4px',
          fontSize: '14px'
        }}
      >
        {/* Render selected items as chips */}
        {selectedValues.map((item) => (
          <div
            key={item}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              backgroundColor: '#e3f2fd',
              border: '1px solid #90caf9',
              borderRadius: '12px',
              padding: '2px 8px',
              fontSize: '12px',
              margin: '1px',
              maxWidth: '200px'
            }}
          >
            <span style={{
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              marginRight: '4px'
            }}>
              {item}
            </span>
            {!disabled && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemoveChip(item);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '0',
                  marginLeft: '4px',
                  color: '#666',
                  fontSize: '16px',
                  lineHeight: '1'
                }}
                aria-label={`Remove ${item}`}
              >
                ×
              </button>
            )}
          </div>
        ))}

        {/* Search input */}
        <input
          ref={inputRef}
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => !disabled && setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={selectedValues.length === 0 ? placeholder : ''}
          disabled={disabled}
          id={id}
          aria-label={ariaLabel}
          data-testid={testId}
          style={{
            border: 'none',
            outline: 'none',
            flex: 1,
            minWidth: '120px',
            fontSize: '14px',
            backgroundColor: 'transparent'
          }}
        />
      </div>

      {/* Dropdown */}
      {isOpen && !disabled && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            backgroundColor: '#fff',
            border: '1px solid #ced4da',
            borderTop: 'none',
            borderRadius: '0 0 4px 4px',
            maxHeight: '200px',
            overflowY: 'auto',
            zIndex: 1000,
            fontSize: '14px'
          }}
        >
          {filteredOptions.length === 0 ? (
            <div style={{ padding: '8px 12px', color: '#6c757d', fontStyle: 'italic' }}>
              {searchTerm ? 'No matching options' : 'All options selected'}
            </div>
          ) : (
            filteredOptions.map((option) => (
              <div
                key={option}
                onClick={() => handleToggleOption(option)}
                style={{
                  padding: '8px 12px',
                  cursor: 'pointer',
                  borderBottom: '1px solid #f1f3f4',
                  backgroundColor: '#fff'
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = '#f8f9fa';
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = '#fff';
                }}
              >
                {option}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default BeanProcessMultiSelect;