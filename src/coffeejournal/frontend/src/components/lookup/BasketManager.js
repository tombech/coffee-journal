import React from 'react';
import { useNavigate } from 'react-router-dom';
import LookupManager from '../LookupManager';

function BasketManager() {
  const navigate = useNavigate();

  const customFields = [
    { name: 'basket_type', label: 'Basket Type (single/double/triple)', type: 'text', required: false },
    { name: 'hole_count', label: 'Number of Holes', type: 'number', required: false },
    { name: 'capacity_grams', label: 'Capacity (grams)', type: 'number', required: false },
    { name: 'brand', label: 'Brand', type: 'text', required: false }
  ];

  return (
    <LookupManager
      title="Baskets"
      apiEndpoint="baskets"
      singularName="Basket"
      onNavigateBack={() => navigate('/settings')}
      fields={customFields}
      viewRoute="/baskets"
    />
  );
}

export default BasketManager;