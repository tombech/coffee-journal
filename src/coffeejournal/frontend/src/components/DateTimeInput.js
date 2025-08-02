import React, { useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

function DateTimeInput({ name, value, onChange, required = false, placeholder = "dd.mm hh:mm" }) {
  const [inputValue, setInputValue] = useState('');
  const [isPickerOpen, setIsPickerOpen] = useState(false);
  
  // Convert string value to Date object
  const dateValue = value ? new Date(value) : null;

  const formatDateTimeForDisplay = (date) => {
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${day}.${month} ${hours}:${minutes}`;
  };

  const handleDatePickerChange = (date) => {
    if (date) {
      // Convert Date object back to ISO string for form handling (using local timezone)
      const isoString = date.toISOString();
      onChange({ target: { name, value: isoString } });
      setInputValue(formatDateTimeForDisplay(date));
    } else {
      onChange({ target: { name, value: '' } });
      setInputValue('');
    }
    setIsPickerOpen(false);
  };

  // Initialize input value from prop
  React.useEffect(() => {
    if (value) {
      const date = new Date(value);
      setInputValue(formatDateTimeForDisplay(date));
    } else {
      setInputValue('');
    }
  }, [value]);

  // Custom date parsing to handle dd.mm hh:mm format
  const parseDateTime = (dateTimeString) => {
    if (!dateTimeString) return null;
    
    // Handle "dd.mm hh:mm" format
    const parts = dateTimeString.trim().split(' ');
    if (parts.length >= 1) {
      const datePart = parts[0];
      const timePart = parts[1] || '12:00'; // Default to noon if no time provided
      
      const dateComponents = datePart.split('.');
      if (dateComponents.length >= 2) {
        let [day, month, year] = dateComponents;
        
        // If no year provided, use current year
        if (!year || year === '') {
          year = new Date().getFullYear();
        } else if (year.length === 2) {
          // Convert yy to yyyy (assume 21st century for years 00-99)
          const currentYear = new Date().getFullYear();
          const currentCentury = Math.floor(currentYear / 100) * 100;
          year = currentCentury + parseInt(year, 10);
        }
        
        const timeComponents = timePart.split(':');
        let [hours, minutes] = timeComponents;
        hours = hours || '12';
        minutes = minutes || '00';
        
        const parsedDay = parseInt(day, 10);
        const parsedMonth = parseInt(month, 10);
        const parsedYear = parseInt(year, 10);
        const parsedHours = parseInt(hours, 10);
        const parsedMinutes = parseInt(minutes, 10);
        
        // Validate the date and time parts
        if (parsedDay >= 1 && parsedDay <= 31 && 
            parsedMonth >= 1 && parsedMonth <= 12 &&
            parsedHours >= 0 && parsedHours <= 23 &&
            parsedMinutes >= 0 && parsedMinutes <= 59) {
          return new Date(parsedYear, parsedMonth - 1, parsedDay, parsedHours, parsedMinutes);
        }
      }
    }
    
    return null;
  };

  const handleInputChange = (e) => {
    const input = e.target.value;
    setInputValue(input);
  };

  const handleInputBlur = () => {
    // Always parse on blur to catch time changes
    const parsed = parseDateTime(inputValue);
    if (parsed && !isNaN(parsed)) {
      handleDatePickerChange(parsed);
    } else if (inputValue === '') {
      handleDatePickerChange(null);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleInputBlur();
    }
  };

  return (
    <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
      <input
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        onBlur={handleInputBlur}
        onKeyPress={handleKeyPress}
        placeholder={placeholder}
        required={required}
        style={{
          width: '100%',
          padding: '8px',
          paddingRight: '35px',
          border: '1px solid #ccc',
          borderRadius: '4px',
          fontSize: '14px'
        }}
      />
      <button
        type="button"
        onClick={() => setIsPickerOpen(!isPickerOpen)}
        style={{
          position: 'absolute',
          right: '5px',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          fontSize: '16px',
          padding: '4px',
          color: '#666'
        }}
        title="Open date/time picker"
      >
        🕐
      </button>
      
      {isPickerOpen && (
        <DatePicker
          selected={dateValue}
          onChange={handleDatePickerChange}
          onClickOutside={() => setIsPickerOpen(false)}
          showTimeSelect
          timeFormat="HH:mm"
          timeIntervals={15}
          dateFormat="dd.MM.yyyy HH:mm"
          showYearDropdown
          yearDropdownItemNumber={15}
          scrollableYearDropdown
          minDate={new Date(2000, 0, 1)}
          maxDate={new Date(2050, 11, 31)}
          inline
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            zIndex: 1000
          }}
        />
      )}
    </div>
  );
}

export default DateTimeInput;