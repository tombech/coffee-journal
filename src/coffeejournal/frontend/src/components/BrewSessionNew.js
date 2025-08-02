import React from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import BrewSessionForm from './BrewSessionForm';

function BrewSessionNew() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const batchId = searchParams.get('batch_id');

  const handleSessionSubmitted = () => {
    // Redirect back to the batch detail page
    if (batchId) {
      navigate(`/batches/${batchId}`);
    } else {
      navigate('/brew-sessions');
    }
  };

  return (
    <div>
      <BrewSessionForm 
        product_batch_id={batchId ? parseInt(batchId) : null}
        onSessionSubmitted={handleSessionSubmitted}
      />
    </div>
  );
}

export default BrewSessionNew;