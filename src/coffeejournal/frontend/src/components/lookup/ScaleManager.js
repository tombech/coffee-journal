import React from 'react';
import { useNavigate } from 'react-router-dom';
import LookupManager from '../LookupManager';

function ScaleManager() {
  const navigate = useNavigate();

  const customFields = [
    { name: 'brand', label: 'Brand', type: 'text', required: false },
    { name: 'max_weight', label: 'Maximum Weight (g)', type: 'number', required: false },
    { name: 'precision', label: 'Precision (g)', type: 'number', required: false }
  ];

  return (
    <LookupManager
      title="Scales"
      apiEndpoint="scales"
      singularName="Scale"
      onNavigateBack={() => navigate('/settings')}
      fields={customFields}
      viewRoute="/scales"
    />
  );
}

export default ScaleManager;