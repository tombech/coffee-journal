import React from 'react';
import { useNavigate } from 'react-router-dom';
import LookupManager from '../LookupManager';

function RoasterManager() {
  const navigate = useNavigate();

  const customFields = [
    { name: 'location', label: 'Location', type: 'text', required: false },
    { name: 'website', label: 'Website', type: 'url', required: false },
    { name: 'specialty', label: 'Specialty/Focus', type: 'text', required: false }
  ];

  return (
    <LookupManager
      title="Roasters"
      apiEndpoint="roasters"
      singularName="Roaster"
      onNavigateBack={() => navigate('/settings')}
      fields={customFields}
      viewRoute="/roasters"
    />
  );
}

export default RoasterManager;