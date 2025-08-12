import React from 'react';
import { useNavigate } from 'react-router-dom';
import LookupManager from '../LookupManager';

function WDTToolManager() {
  const navigate = useNavigate();

  const customFields = [
    { name: 'needle_count', label: 'Number of Needles', type: 'number', required: false },
    { name: 'needle_diameter', label: 'Needle Diameter (mm)', type: 'number', required: false },
    { name: 'handle_material', label: 'Handle Material', type: 'text', required: false },
    { name: 'brand', label: 'Brand', type: 'text', required: false }
  ];

  return (
    <LookupManager
      title="WDT Tools"
      apiEndpoint="wdt_tools"
      singularName="WDT Tool"
      onNavigateBack={() => navigate('/settings')}
      fields={customFields}
      viewRoute="/wdt_tools"
    />
  );
}

export default WDTToolManager;