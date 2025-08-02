import React from 'react';
import { useNavigate } from 'react-router-dom';
import LookupManager from '../LookupManager';

function DecafMethodManager() {
  const navigate = useNavigate();

  const customFields = [
    { name: 'process_type', label: 'Process Type', type: 'text', required: false },
    { name: 'chemical_used', label: 'Chemical/Solvent Used', type: 'text', required: false },
    { name: 'environmental_impact', label: 'Environmental Impact', type: 'text', required: false }
  ];

  return (
    <LookupManager
      title="Decaf Methods"
      apiEndpoint="decaf_methods"
      singularName="Decaf Method"
      onNavigateBack={() => navigate('/settings')}
      fields={customFields}
      viewRoute="/decaf-methods"
    />
  );
}

export default DecafMethodManager;