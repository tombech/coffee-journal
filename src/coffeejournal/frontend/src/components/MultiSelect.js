import React, { useState, useRef, useEffect } from 'react';
import { 
  isAndroidTablet, 
  getBrowserInfo, 
  hasVirtualKeyboardAPI, 
  getViewportHeight,
  shouldDisableDropdownSearch 
} from '../utils/androidDetection';

function MultiSelect({ name, values = [], onChange, options = [], placeholder = "Type to add..." }) {
  const [inputValue, setInputValue] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [keyboardHeight, setKeyboardHeight] = useState(0);
  const containerRef = useRef(null);
  
  // Android tablet specific state
  const isAndroidDevice = isAndroidTablet();
  const browserInfo = getBrowserInfo();
  const disableSearch = shouldDisableDropdownSearch();
  
  // Ensure values is always an array
  const safeValues = Array.isArray(values) ? values : [];
  const safeOptions = Array.isArray(options) ? options : [];

  // Comprehensive dropdown dismissal fix
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };

    const handleFocusChange = (event) => {
      // Close dropdown when focus moves to other form elements
      if (event.target && event.target.tagName && 
          ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName) &&
          containerRef.current && !containerRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };

    const handleKeyboardResize = () => {
      if (hasVirtualKeyboardAPI() && navigator.virtualKeyboard) {
        const keyboardRect = navigator.virtualKeyboard.boundingRect;
        setKeyboardHeight(keyboardRect.height);
      } else {
        const currentHeight = getViewportHeight();
        const expectedHeight = window.screen.height;
        const keyboardDetected = currentHeight < expectedHeight * 0.8;
        setKeyboardHeight(keyboardDetected ? expectedHeight - currentHeight : 0);
      }
    };

    // Universal dismissal handling (works on all devices)
    document.addEventListener('touchstart', handleClickOutside, { passive: true });
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('focusin', handleFocusChange);
    
    // Keyboard detection for mobile devices
    if (isAndroidDevice) {
      if (hasVirtualKeyboardAPI() && navigator.virtualKeyboard) {
        navigator.virtualKeyboard.addEventListener('geometrychange', handleKeyboardResize);
      } else {
        window.addEventListener('resize', handleKeyboardResize);
        window.addEventListener('orientationchange', handleKeyboardResize);
      }
    }

    return () => {
      document.removeEventListener('touchstart', handleClickOutside);
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('focusin', handleFocusChange);
      if (isAndroidDevice) {
        if (hasVirtualKeyboardAPI() && navigator.virtualKeyboard) {
          navigator.virtualKeyboard.removeEventListener('geometrychange', handleKeyboardResize);
        } else {
          window.removeEventListener('resize', handleKeyboardResize);
          window.removeEventListener('orientationchange', handleKeyboardResize);
        }
      }
    };
  }, [isAndroidDevice]);

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
    
    // Android tablet: disable search if problematic
    if (disableSearch && e.target.value.trim()) {
      return;
    }
    
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

  const handleCloseDropdown = () => {
    setShowSuggestions(false);
  };

  const filteredOptions = safeOptions
    .filter(opt => opt && opt.name && typeof opt.name === 'string' && opt.name.toLowerCase().includes(inputValue.toLowerCase()))
    .filter(opt => opt && opt.name && !safeValues.includes(opt.name));

  return (
    <div ref={containerRef} style={{ position: 'relative' }}>
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
          placeholder={safeValues.length === 0 ? (disableSearch ? `${placeholder} (Type to add)` : placeholder) : ""}
          readOnly={disableSearch}
          style={{
            border: 'none',
            outline: 'none',
            flex: '1',
            minWidth: '100px',
            padding: '4px'
          }}
        />
      </div>
      
      {!disableSearch && showSuggestions && inputValue && filteredOptions.length > 0 && (
        <div style={{
          // Android tablet: Use different positioning strategies per browser
          position: isAndroidDevice ? 'absolute' : 'fixed',
          // Add close button container styling
          paddingTop: isAndroidDevice ? '30px' : '0',
          
          // Calculate smart positioning
          ...(containerRef.current ? (() => {
            const rect = containerRef.current.getBoundingClientRect();
            const viewportHeight = getViewportHeight();
            const availableHeight = viewportHeight - keyboardHeight;
            const spaceBelow = availableHeight - rect.bottom;
            const spaceAbove = rect.top;
            
            // Android-specific positioning logic
            if (isAndroidDevice) {
              if (browserInfo === 'chrome' || browserInfo === 'brave') {
                return {
                  position: 'absolute',
                  bottom: 'calc(100% + 2px)',
                  left: 0,
                  right: 0,
                  maxHeight: Math.min(150, spaceAbove - 20),
                  borderTop: '1px solid #ccc',
                  borderBottom: 'none',
                  borderRadius: '4px 4px 0 0'
                };
              }
            }
            
            // Standard positioning logic
            if (spaceBelow > 150 || spaceBelow > spaceAbove) {
              return {
                [isAndroidDevice ? 'top' : 'top']: isAndroidDevice ? '100%' : rect.bottom + 2,
                left: isAndroidDevice ? 0 : rect.left,
                [isAndroidDevice ? 'right' : 'width']: isAndroidDevice ? 0 : rect.width,
                maxHeight: Math.min(150, spaceBelow - 20),
                borderTop: 'none',
                borderRadius: '0 0 4px 4px'
              };
            } else {
              return {
                [isAndroidDevice ? 'bottom' : 'bottom']: isAndroidDevice ? '100%' : viewportHeight - rect.top + 2,
                left: isAndroidDevice ? 0 : rect.left,
                [isAndroidDevice ? 'right' : 'width']: isAndroidDevice ? 0 : rect.width,
                maxHeight: Math.min(150, spaceAbove - 20),
                borderTop: '1px solid #ccc',
                borderBottom: 'none',
                borderRadius: '4px 4px 0 0'
              };
            }
          })() : { top: '100%', left: 0, right: 0 }),
          
          backgroundColor: 'white',
          border: '1px solid #ccc',
          overflowY: 'auto',
          zIndex: isAndroidDevice ? 9999 : 1000
        }}>
          {/* Close button for Android tablets */}
          {isAndroidDevice && (
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '30px',
              backgroundColor: '#f8f9fa',
              borderBottom: '1px solid #dee2e6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 8px',
              fontSize: '12px',
              color: '#6c757d'
            }}>
              <span>Select an option or type to add</span>
              <button
                type="button"
                onClick={handleCloseDropdown}
                onTouchEnd={handleCloseDropdown}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '18px',
                  cursor: 'pointer',
                  padding: '2px 6px',
                  color: '#6c757d',
                  lineHeight: '1'
                }}
                aria-label="Close dropdown"
              >
                ×
              </button>
            </div>
          )}
          
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