import React from 'react';
import InlineChipAutocomplete from './InlineChipAutocomplete';

function CountryAutocomplete({ 
  value, 
  onChange, 
  placeholder = "Search countries...", 
  disabled = false,
  id,
  'aria-label': ariaLabel,
  ...rest
}) {
  return (
    <InlineChipAutocomplete
      lookupType="countries"
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled}
      multiSelect={false}
      maxHeight="250px"
      id={id}
      aria-label={ariaLabel}
      {...rest}
    />
  );
}

export default CountryAutocomplete;