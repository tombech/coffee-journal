import React, { useState, useEffect } from 'react';
import { useToast } from './Toast';
import { apiFetch } from '../config';
import StarRating from './StarRating';
import DateInput from './DateInput';

function BatchForm({ productId, initialData, onBatchSubmitted, onCancel }) {
  const [formData, setFormData] = useState({
    roast_date: '',
    purchase_date: '',
    amount_grams: '',
    price: '',
    seller: '',
    notes: '',
    rating: '',
    is_active: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const isEditMode = !!initialData;
  const { addToast } = useToast();

  useEffect(() => {
    if (initialData) {
      // Convert dates to proper format for input fields
      const formatDateForInput = (dateString) => {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toISOString().split('T')[0]; // YYYY-MM-DD format
      };

      setFormData({
        roast_date: formatDateForInput(initialData.roast_date),
        purchase_date: formatDateForInput(initialData.purchase_date),
        amount_grams: initialData.amount_grams || '',
        price: initialData.price || '',
        seller: initialData.seller || '',
        notes: initialData.notes || '',
        rating: initialData.rating || '',
        is_active: initialData.is_active !== undefined ? initialData.is_active : true
      });
    }
  }, [initialData]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleRatingChange = (rating) => {
    setFormData(prev => ({ ...prev, rating: rating }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const method = isEditMode ? 'PUT' : 'POST';
    const url = isEditMode 
      ? `/batches/${initialData.id}` 
      : `/products/${productId}/batches`;

    // For edit mode, no need to modify formData
    // For create mode, product_id comes from URL, not request body
    const requestData = formData;

    try {
      const response = await apiFetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`HTTP error! status: ${response.status} - ${errorData.message || 'Unknown error'}`);
      }

      const result = await response.json();
      addToast(`Batch ${isEditMode ? 'updated' : 'added'} successfully!`, 'success');
      onBatchSubmitted(result); // Callback to refresh the batch list
    } catch (err) {
      setError(`Failed to ${isEditMode ? 'update' : 'add'} batch: ` + err.message);
      console.error("Error submitting batch:", err);
    } finally {
      setLoading(false);
    }
  };

  // Norwegian date formatting for display
  const formatDateNorwegian = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear().toString().slice(-2);
    return `${day}.${month}.${year}`;
  };

  // Calculate price per cup in real-time
  const calculatePricePerCup = () => {
    if (formData.price && formData.amount_grams && formData.amount_grams > 0) {
      const price = Number(formData.price);
      const amount = Number(formData.amount_grams);
      if (!isNaN(price) && !isNaN(amount) && amount > 0) {
        const cupsPerBatch = amount / 18.0; // 18g per cup
        if (cupsPerBatch > 0) {
          return (price / cupsPerBatch).toFixed(2);
        }
      }
    }
    return null;
  };

  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: isEditMode ? '#fff3cd' : '#f8f9fa', 
      borderRadius: '8px', 
      border: isEditMode ? '1px solid #ffeaa7' : '1px solid #ddd',
      marginBottom: '20px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
        <h4 style={{ margin: 0 }}>
          {isEditMode ? `Edit Batch #${initialData.id}` : 'Add New Batch'}
        </h4>
        {onCancel && (
          <button 
            onClick={onCancel}
            style={{ 
              padding: '6px 8px', 
              border: 'none', 
              background: 'none', 
              cursor: 'pointer', 
              fontSize: '16px' 
            }}
            title="Cancel"
          >
            ❌
          </button>
        )}
      </div>

      {error && <p className="error-message">{error}</p>}

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
          <label htmlFor="roast-date">
            Roast Date:
            <DateInput 
              id="roast-date"
              name="roast_date" 
              value={formData.roast_date} 
              onChange={handleChange} 
              required 
            />
          </label>
          
          <label htmlFor="purchase-date">
            Purchase Date:
            <DateInput 
              id="purchase-date"
              name="purchase_date" 
              value={formData.purchase_date} 
              onChange={handleChange} 
            />
          </label>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px', marginBottom: '15px' }}>
          <label htmlFor="amount-grams">
            Amount (grams):
            <input 
              id="amount-grams"
              type="number" 
              name="amount_grams" 
              value={formData.amount_grams} 
              onChange={handleChange} 
              min="1" 
              step="0.1"
              placeholder="250"
            />
          </label>
          
          <label htmlFor="price">
            Price (kr):
            <input 
              id="price"
              type="number" 
              name="price" 
              value={formData.price} 
              onChange={handleChange} 
              min="0" 
              step="0.01"
              placeholder="149.00"
            />
          </label>
          
          <label htmlFor="price-per-cup">
            Price per Cup:
            <input 
              id="price-per-cup"
              type="text" 
              value={calculatePricePerCup() ? `${calculatePricePerCup()} kr` : '-'} 
              disabled 
              style={{ backgroundColor: '#e9ecef' }}
              title="Automatically calculated based on 18g per cup"
            />
          </label>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="seller">
            Seller:
            <input 
              id="seller"
              type="text" 
              name="seller" 
              value={formData.seller} 
              onChange={handleChange}
              placeholder="e.g., Local coffee shop, Online store"
            />
          </label>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label htmlFor="batch-notes">
            Notes:
          </label>
          <textarea 
            id="batch-notes"
            name="notes" 
            value={formData.notes} 
            onChange={handleChange} 
            rows="3"
            placeholder="Any additional notes about this batch..."
            data-testid="batch-notes-input"
          />
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label>
            Rating:
            <div style={{ marginTop: '8px' }}>
              <StarRating
                rating={formData.rating}
                onRatingChange={handleRatingChange}
                maxRating={5}
                size="xlarge"
              />
            </div>
          </label>
        </div>

        {isEditMode && (
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
              />
              <span>Active batch (visible for new brew sessions)</span>
            </label>
          </div>
        )}

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button 
            type="submit" 
            disabled={loading}
            data-testid={isEditMode ? 'update-batch-btn' : 'create-batch-btn'}
            aria-label={loading ? 'Saving...' : (isEditMode ? 'Update Batch' : 'Create Batch')}
            style={{ 
              padding: '8px 16px',
              backgroundColor: loading ? '#6c757d' : '#28a745',
              color: 'white',
              border: 'none', 
              borderRadius: '4px',
              cursor: loading ? 'default' : 'pointer', 
              fontSize: '14px',
              opacity: loading ? 0.5 : 1
            }}
            title={loading ? 'Saving...' : (isEditMode ? 'Update Batch' : 'Create Batch')}
          >
            {loading ? 'Saving...' : (isEditMode ? 'Update' : 'Create')}
          </button>
          
          {onCancel && (
            <button 
              type="button" 
              onClick={onCancel} 
              disabled={loading}
              style={{ 
                padding: '8px 12px', 
                border: 'none', 
                background: 'none', 
                cursor: loading ? 'default' : 'pointer', 
                fontSize: '18px',
                opacity: loading ? 0.5 : 1
              }}
              title="Cancel"
            >
              ❌
            </button>
          )}
        </div>
      </form>
    </div>
  );
}

export default BatchForm;