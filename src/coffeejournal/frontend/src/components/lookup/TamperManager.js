import React from 'react';
import { useNavigate } from 'react-router-dom';
import LookupManager from '../LookupManager';

function TamperManager() {
  const navigate = useNavigate();

  const customFields = [
    { name: 'size', label: 'Size (54mm, 58mm, etc)', type: 'text', required: false },
    { name: 'weight', label: 'Weight (grams)', type: 'number', required: false },
    { name: 'handle_material', label: 'Handle Material', type: 'text', required: false },
    { name: 'base_material', label: 'Base Material', type: 'text', required: false },
    { name: 'brand', label: 'Brand', type: 'text', required: false }
  ];

  return (
    <LookupManager
      title="Tampers"
      apiEndpoint="tampers"
      singularName="Tamper"
      onNavigateBack={() => navigate('/settings')}
      fields={customFields}
      viewRoute="/tampers"
    />
  );
}

export default TamperManager;