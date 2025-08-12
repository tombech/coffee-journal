import React from 'react';
import { useNavigate } from 'react-router-dom';
import LookupManager from '../LookupManager';

function BrewerManager() {
  const navigate = useNavigate();

  const customFields = [
    { name: 'type', label: 'Brewer Type (espresso/pourover)', type: 'text', required: false },
    { name: 'brand', label: 'Brand', type: 'text', required: false },
    { name: 'model', label: 'Model', type: 'text', required: false }
  ];

  return (
    <LookupManager
      title="Brewers"
      apiEndpoint="brewers"
      singularName="Brewer"
      onNavigateBack={() => navigate('/settings')}
      fields={customFields}
      viewRoute="/brewers"
    />
  );
}

export default BrewerManager;