import React from 'react';
import { useNavigate } from 'react-router-dom';
import LookupManager from '../LookupManager';

function LevelingToolManager() {
  const navigate = useNavigate();

  const customFields = [
    { name: 'size', label: 'Size (54mm, 58mm, etc)', type: 'text', required: false },
    { name: 'adjustment_type', label: 'Adjustment Type (fixed/adjustable)', type: 'text', required: false },
    { name: 'depth_range', label: 'Depth Range (mm)', type: 'text', required: false },
    { name: 'brand', label: 'Brand', type: 'text', required: false }
  ];

  return (
    <LookupManager
      title="Leveling Tools"
      apiEndpoint="leveling_tools"
      singularName="Leveling Tool"
      onNavigateBack={() => navigate('/settings')}
      fields={customFields}
      viewRoute="/leveling_tools"
    />
  );
}

export default LevelingToolManager;