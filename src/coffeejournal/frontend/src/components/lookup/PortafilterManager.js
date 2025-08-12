import React from 'react';
import { useNavigate } from 'react-router-dom';
import LookupManager from '../LookupManager';

function PortafilterManager() {
  const navigate = useNavigate();

  const customFields = [
    { name: 'size', label: 'Size (54mm, 58mm, etc)', type: 'text', required: false },
    { name: 'brand', label: 'Brand', type: 'text', required: false },
    { name: 'material', label: 'Material', type: 'text', required: false },
    { name: 'handle_type', label: 'Handle Type', type: 'text', required: false }
  ];

  return (
    <LookupManager
      title="Portafilters"
      apiEndpoint="portafilters"
      singularName="Portafilter"
      onNavigateBack={() => navigate('/settings')}
      fields={customFields}
      viewRoute="/portafilters"
    />
  );
}

export default PortafilterManager;