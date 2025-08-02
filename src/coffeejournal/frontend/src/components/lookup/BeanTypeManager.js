import React from 'react';
import { useNavigate } from 'react-router-dom';
import LookupManager from '../LookupManager';

function BeanTypeManager() {
  const navigate = useNavigate();

  const customFields = [
    { name: 'species', label: 'Coffee Species', type: 'text', required: false },
    { name: 'processing_method', label: 'Typical Processing Method', type: 'text', required: false },
    { name: 'flavor_profile', label: 'Typical Flavor Profile', type: 'textarea', required: false }
  ];

  return (
    <LookupManager
      title="Bean Types"
      apiEndpoint="bean_types"
      singularName="Bean Type"
      onNavigateBack={() => navigate('/settings')}
      fields={customFields}
      viewRoute="/bean-types"
    />
  );
}

export default BeanTypeManager;