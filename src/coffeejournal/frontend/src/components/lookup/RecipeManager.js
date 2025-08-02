import React from 'react';
import { useNavigate } from 'react-router-dom';
import LookupManager from '../LookupManager';

function RecipeManager() {
  const navigate = useNavigate();

  const customFields = [
    { name: 'coffee_ratio', label: 'Coffee to Water Ratio', type: 'text', required: false },
    { name: 'brew_method', label: 'Associated Brew Method', type: 'text', required: false },
    { name: 'instructions', label: 'Brewing Instructions', type: 'textarea', required: false }
  ];

  return (
    <LookupManager
      title="Recipes"
      apiEndpoint="recipes"
      singularName="Recipe"
      onNavigateBack={() => navigate('/settings')}
      fields={customFields}
      viewRoute="/recipes"
    />
  );
}

export default RecipeManager;