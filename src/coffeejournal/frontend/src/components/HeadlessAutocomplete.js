import React, { useState, useEffect, useRef } from 'react';
import { Combobox } from '@headlessui/react';
import { apiFetch } from '../config';
import MobileSearchModal from './MobileSearchModal';
import { 
  isAndroidTablet, 
  isDefinitelyAndroidTablet,
  getBrowserInfo, 
  hasVirtualKeyboardAPI, 
  getViewportHeight, 
  isVirtualKeyboardOpen,
  shouldDisableDropdownSearch 
} from '../utils/androidDetection';

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
  const [keyboardHeight, setKeyboardHeight] = useState(0);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isMobileModalOpen, setIsMobileModalOpen] = useState(false);
  const containerRef = useRef(null);
  
  // Mobile detection - Android tablets always use mobile modal (even in desktop mode)
  const isMobileDevice = window.innerWidth <= 768 || isDefinitelyAndroidTablet();
  const isAndroidDevice = isDefinitelyAndroidTablet();
  const browserInfo = getBrowserInfo();
  const disableSearch = shouldDisableDropdownSearch();
  
  console.log('HeadlessAutocomplete debug:', { isMobileDevice, isAndroidDevice, browserInfo, disableSearch });

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

  // Comprehensive dropdown dismissal fix
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
        const comboboxInput = containerRef.current.querySelector('[role="combobox"]');
        if (comboboxInput) {
          comboboxInput.blur();
        }
      }
    };

    const handleFocusChange = (event) => {
      // Close dropdown when focus moves to other form elements
      if (event.target && event.target.tagName && 
          ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName) &&
          containerRef.current && !containerRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
        const comboboxInput = containerRef.current.querySelector('[role="combobox"]');
        if (comboboxInput) {
          comboboxInput.blur();
        }
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
      setIsDropdownOpen(false);
    }
  };

  const handleCloseDropdown = () => {
    setIsDropdownOpen(false);
    const comboboxInput = containerRef.current?.querySelector('[role="combobox"]');
    if (comboboxInput) {
      comboboxInput.blur();
    }
  };

  const handleInputChange = (inputValue) => {
    setQuery(inputValue);
    
    // On mobile, open modal instead of dropdown
    if (isMobileDevice && inputValue && !isMobileModalOpen) {
      setIsMobileModalOpen(true);
      return;
    }
    
    // Android tablet: disable search if problematic
    if (disableSearch && inputValue.trim()) {
      return;
    }
    
    // If user clears the input, clear the selection
    if (!inputValue.trim()) {
      onChange({ id: null, name: '', isNew: false });
      setIsDropdownOpen(false);
    } else if (!isMobileDevice) {
      setIsDropdownOpen(true);
    }
  };
  
  const handleInputFocus = () => {
    if (isMobileDevice) {
      setIsMobileModalOpen(true);
    }
  };
  
  const handleMobileModalChange = (selectedValue) => {
    onChange(selectedValue);
    setQuery(selectedValue.name);
    setIsMobileModalOpen(false);
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
    <>
    <Combobox value={value || { id: null, name: '' }} onChange={handleSelectionChange}>
      <div ref={containerRef} style={{ position: 'relative' }}>
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
          onFocus={handleInputFocus}
          onBlur={handleInputBlur}
          readOnly={isMobileDevice}
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
          static={process.env.NODE_ENV === 'test' || disableSearch}
          style={{
            // Add close button container styling
            paddingTop: isAndroidDevice ? '30px' : '0',
            // Android tablet: Use different positioning strategies per browser
            position: isAndroidDevice ? 'absolute' : 'fixed',
            
            // Calculate smart positioning
            ...(containerRef.current ? (() => {
              const rect = containerRef.current.getBoundingClientRect();
              const viewportHeight = getViewportHeight();
              const availableHeight = viewportHeight - keyboardHeight;
              const spaceBelow = availableHeight - rect.bottom;
              const spaceAbove = rect.top;
              
              // Android-specific positioning logic
              if (isAndroidDevice) {
                // Chrome/Brave on Android: Use absolute positioning with special handling
                if (browserInfo === 'chrome' || browserInfo === 'brave') {
                  // Always show above input on Android to avoid keyboard
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
              
              // Standard positioning logic for non-Android or other browsers
              if (spaceBelow > 200 || spaceBelow > spaceAbove) {
                return {
                  [isAndroidDevice ? 'top' : 'top']: isAndroidDevice ? '100%' : rect.bottom + 2,
                  left: isAndroidDevice ? 0 : rect.left,
                  [isAndroidDevice ? 'right' : 'width']: isAndroidDevice ? 0 : rect.width,
                  maxHeight: Math.min(200, spaceBelow - 20),
                  borderTop: 'none',
                  borderRadius: '0 0 4px 4px'
                };
              } else {
                return {
                  [isAndroidDevice ? 'bottom' : 'bottom']: isAndroidDevice ? '100%' : viewportHeight - rect.top + 2,
                  left: isAndroidDevice ? 0 : rect.left,
                  [isAndroidDevice ? 'right' : 'width']: isAndroidDevice ? 0 : rect.width,
                  maxHeight: Math.min(200, spaceAbove - 20),
                  borderTop: '1px solid #ccc',
                  borderBottom: 'none',
                  borderRadius: '4px 4px 0 0'
                };
              }
            })() : { top: '100%', left: 0, right: 0 }),
            
            backgroundColor: 'white',
            border: '1px solid #ccc',
            overflowY: 'auto',
            zIndex: isAndroidDevice ? 9999 : 1000,
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            
            // Hide dropdown entirely if search is disabled and we're typing
            display: (disableSearch && query.trim()) ? 'none' : 'block'
          }}
        >
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
              <span>Select an option or type to create new</span>
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
    
    {/* Mobile Search Modal */}
    {isMobileDevice && (
      <MobileSearchModal
        isOpen={isMobileModalOpen}
        onClose={() => setIsMobileModalOpen(false)}
        lookupType={lookupType}
        value={value}
        onChange={handleMobileModalChange}
        placeholder={placeholder}
        multiSelect={false}
      />
    )}
    </>
  );
}

export default HeadlessAutocomplete;