import React from 'react';
import { useNavigate } from 'react-router-dom';
import LookupManager from '../LookupManager';

function FilterManager() {
  const navigate = useNavigate();

  const customFields = [
    { name: 'material', label: 'Material', type: 'text', required: false },
    { name: 'brand', label: 'Brand', type: 'text', required: false },
    { name: 'compatibility', label: 'Compatible With', type: 'text', required: false }
  ];

  return (
    <LookupManager
      title="Filters"
      apiEndpoint="filters"
      singularName="Filter"
      onNavigateBack={() => navigate('/settings')}
      fields={customFields}
      viewRoute="/filters"
    />
  );
}

export default FilterManager;