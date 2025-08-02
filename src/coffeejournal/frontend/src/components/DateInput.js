import React, { useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

function DateInput({ id, name, value, onChange, required = false, placeholder = "dd.mm.yy or dd.mm" }) {
  const [inputValue, setInputValue] = useState('');
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);
  
  // Convert string value to Date object
  const dateValue = value ? new Date(value) : null;

  const formatDateForDisplay = (date) => {
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0'); // getMonth() returns 0-indexed, so we add 1
    const year = date.getFullYear().toString().slice(-2);
    return `${day}.${month}.${year}`;
  };

  const handleDatePickerChange = (date) => {
    if (date) {
      // Convert Date object back to YYYY-MM-DD string for form handling (using local timezone)
      const year = date.getFullYear();
      const month = (date.getMonth() + 1).toString().padStart(2, '0');
      const day = date.getDate().toString().padStart(2, '0');
      const isoString = `${year}-${month}-${day}`;
      
      onChange({ target: { name, value: isoString } });
      setInputValue(formatDateForDisplay(date));
    } else {
      onChange({ target: { name, value: '' } });
      setInputValue('');
    }
    setIsCalendarOpen(false);
  };

  // Initialize input value from prop
  React.useEffect(() => {
    if (value) {
      const date = new Date(value);
      setInputValue(formatDateForDisplay(date));
    } else {
      setInputValue('');
    }
  }, [value]);

  // Custom date parsing to handle dd.mm.yy and dd.mm formats
  const parseDate = (dateString) => {
    if (!dateString) return null;
    
    const parts = dateString.split('.');
    if (parts.length >= 2) {
      let [day, month, year] = parts;
      
      // If no year provided, use current year
      if (!year || year === '') {
        year = new Date().getFullYear().toString().slice(-2);
      }
      
      // Convert yy to yyyy (assume 21st century for years 00-99)
      if (year.length === 2) {
        const currentYear = new Date().getFullYear();
        const currentCentury = Math.floor(currentYear / 100) * 100;
        year = currentCentury + parseInt(year, 10);
      }
      
      const parsedDay = parseInt(day, 10);
      const parsedMonth = parseInt(month, 10);
      const parsedYear = parseInt(year, 10);
      
      // Validate the date parts
      if (parsedDay >= 1 && parsedDay <= 31 && parsedMonth >= 1 && parsedMonth <= 12) {
        // Note: JavaScript Date constructor uses 0-indexed months, so we subtract 1 from parsedMonth
        return new Date(parsedYear, parsedMonth - 1, parsedDay);
      }
    }
    
    return null;
  };

  const handleInputChange = (e) => {
    const input = e.target.value;
    setInputValue(input);
  };

  const handleInputBlur = () => {
    // Don't re-parse if the input already matches the expected format
    if (inputValue && /^\d{2}\.\d{2}\.\d{2}$/.test(inputValue)) {
      return; // Already in correct format, don't re-parse
    }
    
    const parsed = parseDate(inputValue);
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
        id={id}
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
        onClick={() => setIsCalendarOpen(!isCalendarOpen)}
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
        title="Open calendar"
      >
        📅
      </button>
      
      {isCalendarOpen && (
        <DatePicker
          selected={dateValue}
          onChange={handleDatePickerChange}
          onClickOutside={() => setIsCalendarOpen(false)}
          dateFormat="dd.MM.yy"
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

export default DateInput;