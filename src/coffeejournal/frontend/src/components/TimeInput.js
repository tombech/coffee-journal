import React, { useState } from 'react';

function TimeInput({ name, value, onChange, required = false, placeholder = "seconds or mm:ss", id, style }) {
  const [inputValue, setInputValue] = useState('');

  const formatTimeForDisplay = (seconds) => {
    if (seconds === null || seconds === undefined || isNaN(seconds)) return '';
    const totalSeconds = parseInt(seconds, 10);
    const minutes = Math.floor(totalSeconds / 60);
    const remainingSeconds = totalSeconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // Initialize input value from prop
  React.useEffect(() => {
    if (value !== null && value !== undefined && value !== '') {
      setInputValue(formatTimeForDisplay(value));
    } else {
      setInputValue('');
    }
  }, [value]);

  // Parse input to seconds
  const parseTimeToSeconds = (timeString) => {
    if (!timeString) return null;
    
    const trimmed = timeString.trim();
    
    // Check if it's just a number (seconds)
    if (/^\d+$/.test(trimmed)) {
      return parseInt(trimmed, 10);
    }
    
    // Check if it's mm:ss format
    if (/^\d+:\d{1,2}$/.test(trimmed)) {
      const parts = trimmed.split(':');
      const minutes = parseInt(parts[0], 10);
      const seconds = parseInt(parts[1], 10);
      
      // Validate seconds (0-59)
      if (seconds >= 0 && seconds <= 59) {
        return minutes * 60 + seconds;
      }
    }
    
    return null;
  };

  const handleInputChange = (e) => {
    const input = e.target.value;
    setInputValue(input);
  };

  const handleInputBlur = () => {
    const parsed = parseTimeToSeconds(inputValue);
    if (parsed !== null) {
      // Update the form with seconds value
      onChange({ target: { name, value: parsed } });
      // Update display to show formatted time
      setInputValue(formatTimeForDisplay(parsed));
    } else if (inputValue === '') {
      onChange({ target: { name, value: '' } });
      setInputValue('');
    } else {
      // Invalid input - revert to previous valid value
      if (value !== null && value !== undefined && value !== '') {
        setInputValue(formatTimeForDisplay(value));
      } else {
        setInputValue('');
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleInputBlur();
    }
  };

  return (
    <input
      type="text"
      id={id}
      name={name}
      value={inputValue}
      onChange={handleInputChange}
      onBlur={handleInputBlur}
      onKeyPress={handleKeyPress}
      placeholder={placeholder}
      required={required}
      style={style || {
        width: '100%',
        padding: '8px',
        border: '1px solid #ccc',
        borderRadius: '4px',
        fontSize: '14px'
      }}
      title="Enter seconds (e.g., 90) or mm:ss format (e.g., 1:30)"
    />
  );
}

export default TimeInput;