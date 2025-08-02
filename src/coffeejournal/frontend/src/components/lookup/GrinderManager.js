import React from 'react';
import { useNavigate } from 'react-router-dom';
import LookupManager from '../LookupManager';

function GrinderManager() {
  const navigate = useNavigate();

  const customFields = [
    { name: 'brand', label: 'Brand', type: 'text', required: false },
    { name: 'grinder_type', label: 'Grinder Type (Burr/Blade)', type: 'text', required: false },
    { name: 'burr_material', label: 'Burr Material', type: 'text', required: false }
  ];

  return (
    <LookupManager
      title="Grinders"
      apiEndpoint="grinders"
      singularName="Grinder"
      onNavigateBack={() => navigate('/settings')}
      fields={customFields}
      viewRoute="/grinders"
    />
  );
}

export default GrinderManager;