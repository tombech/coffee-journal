import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useToast } from '../Toast';
import { apiFetch } from '../../config';

function ShotSessionForm({ initialData, onShotSessionSubmitted, onCancel }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [formData, setFormData] = useState({
    title: '',
    product_id: '',
    product_batch_id: '',
    brewer_id: '',
    notes: ''
  });
  const [products, setProducts] = useState([]);
  const [batches, setBatches] = useState([]);
  const [brewers, setBrewers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditMode, setIsEditMode] = useState(false);

  // Initialize form data and fetch lookups
  useEffect(() => {
    const initializeForm = async () => {
      setInitialLoading(true);
      try {
        // First fetch all lookups
        await Promise.all([
          fetchProducts(),
          fetchBrewers()
        ]);

        // If we have an id parameter but no initialData, this is edit mode from URL
        if (id && !initialData) {
          console.log('ShotSessionForm: Edit mode detected via URL, fetching shot session:', id);
          const response = await apiFetch(`/shot_sessions/${id}`);
          if (response.ok) {
            const shotSessionData = await response.json();
            console.log('ShotSessionForm: Fetched shot session data:', shotSessionData);
            setIsEditMode(true);
            setFormData({
              title: shotSessionData.title || '',
              product_id: shotSessionData.product_id || '',
              product_batch_id: shotSessionData.product_batch_id || '',
              brewer_id: shotSessionData.brewer_id || '',
              notes: shotSessionData.notes || ''
            });
            console.log('ShotSessionForm: Set form data from API with product_batch_id:', shotSessionData.product_batch_id);
            
            // Fetch batches for the product if we have product_id
            if (shotSessionData.product_id) {
              await fetchBatches(shotSessionData.product_id);
            }
          } else {
            setError(`Failed to fetch shot session: ${response.status}`);
          }
        } else if (initialData) {
          // Edit mode with provided data (inline editing)
          console.log('ShotSessionForm: Initializing with provided data:', initialData);
          setIsEditMode(true);
          setFormData({
            title: initialData.title || '',
            product_id: initialData.product_id || '',
            product_batch_id: initialData.product_batch_id || '',
            brewer_id: initialData.brewer_id || '',
            notes: initialData.notes || ''
          });
          console.log('ShotSessionForm: Set form data with product_batch_id:', initialData.product_batch_id);
          
          // Fetch batches for the product if we have product_id
          if (initialData.product_id) {
            await fetchBatches(initialData.product_id);
          }
        }
      } catch (err) {
        console.error('Error initializing form:', err);
        setError('Failed to initialize form: ' + err.message);
      } finally {
        setInitialLoading(false);
      }
    };

    initializeForm();
  }, [id, initialData]);

  // Fetch batches when product changes
  useEffect(() => {
    console.log('ShotSessionForm: Product ID changed to:', formData.product_id);
    if (formData.product_id) {
      fetchBatches(formData.product_id);
    } else {
      setBatches([]);
      console.log('ShotSessionForm: Clearing product_batch_id due to no product_id');
      setFormData(prev => ({ ...prev, product_batch_id: '' }));
    }
  }, [formData.product_id]);

  const fetchProducts = async () => {
    try {
      const response = await apiFetch('/products');
      if (!response.ok) throw new Error('Failed to fetch products');
      const data = await response.json();
      setProducts(data);
    } catch (err) {
      console.error('Error fetching products:', err);
    }
  };

  const fetchBatches = async (productId) => {
    try {
      console.log('ShotSessionForm: Fetching batches for product:', productId);
      const response = await apiFetch(`/products/${productId}/batches`);
      if (!response.ok) throw new Error('Failed to fetch batches');
      const data = await response.json();
      console.log('ShotSessionForm: Fetched batches:', data);
      setBatches(data);
    } catch (err) {
      console.error('Error fetching batches:', err);
      setBatches([]);
    }
  };

  const fetchBrewers = async () => {
    try {
      const response = await apiFetch('/brewers');
      if (!response.ok) throw new Error('Failed to fetch brewers');
      const data = await response.json();
      setBrewers(data);
    } catch (err) {
      console.error('Error fetching brewers:', err);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Validation
      if (!formData.title.trim()) {
        throw new Error('Session name is required');
      }

      console.log('ShotSessionForm: Submitting form data:', formData);
      const method = (initialData || id) ? 'PUT' : 'POST';
      const url = (initialData || id) ? `/shot_sessions/${initialData?.id || id}` : '/shot_sessions';
      
      const response = await apiFetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      console.log('ShotSessionForm: API response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save shot session');
      }

      const result = await response.json();
      addToast(
        (initialData || id) ? 'Shot session updated successfully!' : 'Shot session created successfully!', 
        'success'
      );
      
      if (onShotSessionSubmitted) {
        onShotSessionSubmitted(result);
      } else if (id && !initialData) {
        // URL-based editing - navigate back to detail page
        navigate(`/shot-sessions/${id}`);
      }
    } catch (err) {
      setError(err.message);
      console.error('Error saving shot session:', err);
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) {
    return <p className="loading-message">Loading shot session form...</p>;
  }

  return (
    <div>
      <h3>{(initialData || isEditMode) ? 'Edit Shot Session' : 'Create New Shot Session'}</h3>
      
      {error && (
        <div style={{ 
          color: '#dc3545', 
          backgroundColor: '#f8d7da', 
          border: '1px solid #f5c6cb', 
          borderRadius: '4px',
          padding: '10px', 
          marginBottom: '15px' 
        }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gap: '15px' }}>
          {/* Session Name */}
          <div>
            <label htmlFor="title" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Session Name *
            </label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              required
              placeholder="e.g., Morning Dialing, Weekend Practice"
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '5px',
                fontSize: '16px'
              }}
            />
          </div>

          {/* Product Selection */}
          <div>
            <label htmlFor="product_id" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Product
            </label>
            <select
              id="product_id"
              name="product_id"
              value={formData.product_id}
              onChange={handleInputChange}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '5px',
                fontSize: '16px'
              }}
            >
              <option value="">Select a product...</option>
              {products.map(product => (
                <option key={product.id} value={product.id}>
                  {product.product_name}
                </option>
              ))}
            </select>
          </div>

          {/* Batch Selection */}
          <div>
            <label htmlFor="product_batch_id" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Batch
            </label>
            <select
              id="product_batch_id"
              name="product_batch_id"
              value={formData.product_batch_id}
              onChange={handleInputChange}
              disabled={!formData.product_id}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '5px',
                fontSize: '16px',
                backgroundColor: !formData.product_id ? '#f8f9fa' : 'white'
              }}
            >
              <option value="">Select a batch...</option>
              {batches.map(batch => (
                <option key={batch.id} value={batch.id}>
                  Batch #{batch.id} - {batch.roast_date}
                </option>
              ))}
            </select>
          </div>

          {/* Brewer Selection */}
          <div>
            <label htmlFor="brewer_id" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Brewer/Machine
            </label>
            <select
              id="brewer_id"
              name="brewer_id"
              value={formData.brewer_id}
              onChange={handleInputChange}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '5px',
                fontSize: '16px'
              }}
            >
              <option value="">Select a brewer...</option>
              {brewers.map(brewer => (
                <option key={brewer.id} value={brewer.id}>
                  {brewer.name}
                </option>
              ))}
            </select>
          </div>

          {/* Notes */}
          <div>
            <label htmlFor="notes" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Session Notes
            </label>
            <textarea
              id="notes"
              name="notes"
              value={formData.notes}
              onChange={handleInputChange}
              rows={4}
              placeholder="Session goals, observations, etc..."
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '5px',
                fontSize: '16px',
                resize: 'vertical'
              }}
            />
          </div>
        </div>

        {/* Form Actions */}
        <div style={{ marginTop: '20px', display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
          <button
            type="button"
            onClick={onCancel}
            style={{
              padding: '10px 20px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            data-testid="submit-shot-session"
            style={{
              padding: '10px 20px',
              backgroundColor: loading ? '#6c757d' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Saving...' : ((initialData || isEditMode) ? 'Update Session' : 'Create Session')}
          </button>
        </div>
      </form>
    </div>
  );
}

export default ShotSessionForm;