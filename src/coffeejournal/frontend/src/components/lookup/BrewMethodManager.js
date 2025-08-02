import React from 'react';
import { useNavigate } from 'react-router-dom';
import LookupManager from '../LookupManager';

function BrewMethodManager() {
  const navigate = useNavigate();

  const customFields = [
    { name: 'brew_time_range', label: 'Typical Brew Time Range', type: 'text', required: false },
    { name: 'water_temperature', label: 'Recommended Water Temperature (°C)', type: 'number', required: false },
    { name: 'grind_size', label: 'Recommended Grind Size', type: 'text', required: false }
  ];

  return (
    <LookupManager
      title="Brew Methods"
      apiEndpoint="brew_methods"
      singularName="Brew Method"
      onNavigateBack={() => navigate('/settings')}
      fields={customFields}
      viewRoute="/brew-methods"
    />
  );
}

export default BrewMethodManager;