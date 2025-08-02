import React from 'react';
import { useNavigate } from 'react-router-dom';
import LookupManager from '../LookupManager';

function KettleManager() {
  const navigate = useNavigate();

  const customFields = [
    { name: 'brand', label: 'Brand', type: 'text', required: false },
    { name: 'capacity', label: 'Capacity (L)', type: 'number', required: false },
    { name: 'kettle_type', label: 'Type (Electric/Stovetop)', type: 'text', required: false }
  ];

  return (
    <LookupManager
      title="Kettles"
      apiEndpoint="kettles"
      singularName="Kettle"
      onNavigateBack={() => navigate('/settings')}
      fields={customFields}
      viewRoute="/kettles"
    />
  );
}

export default KettleManager;