import React from 'react';
import InlineChipAutocomplete from './InlineChipAutocomplete';

function CountryAutocomplete({ 
  value, 
  onChange, 
  placeholder = "Select one country...", 
  disabled = false,
  id,
  'aria-label': ariaLabel,
  ...rest
}) {
  // For single-select, we want to show a more prominent selection
  // and make it clear only one can be selected
  return (
    <InlineChipAutocomplete
      lookupType="countries"
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled}
      multiSelect={false}
      maxHeight="250px"
      singleSelectStyle={true} // Pass flag to indicate single-select styling
      id={id}
      aria-label={ariaLabel}
      {...rest}
    />
  );
}

export default CountryAutocomplete;