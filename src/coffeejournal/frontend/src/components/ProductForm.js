import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useToast } from './Toast';
import { apiFetch } from '../config';
import { ICONS } from '../config/icons';
import StarRating from './StarRating';
import HeadlessAutocomplete from './HeadlessAutocomplete';
import HeadlessMultiAutocomplete from './HeadlessMultiAutocomplete';
import RegionMultiAutocomplete from './RegionMultiAutocomplete';

function ProductForm() {
  const { id } = useParams(); // Get ID from URL for edit mode
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [formData, setFormData] = useState({
    roaster: { id: null, name: '', isNew: false },
    bean_type: [],
    country: { id: null, name: '', isNew: false },
    region: [],
    product_name: '',
    roast_type: '',
    description: '',
    url: '',
    image_url: '',
    decaf: false,
    decaf_method: { id: null, name: '', isNew: false },
    rating: '',
    bean_process: '',
    notes: ''
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditMode, setIsEditMode] = useState(false);

  useEffect(() => {
    // If ID exists, fetch product data for editing
    if (id) {
      setIsEditMode(true);
      fetchProduct();
    } else {
      setLoading(false); // No product to load, so stop loading
    }
  }, [id]);

  const fetchProduct = async () => {
    setLoading(true);
    try {
      const response = await apiFetch(`/products/${id}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      // Convert lookup objects to the expected format
      setFormData({
        roaster: data.roaster ? { id: data.roaster.id, name: data.roaster.name, isNew: false } : { id: null, name: '', isNew: false },
        bean_type: data.bean_type?.map(bt => ({ id: bt.id, name: bt.name, isNew: false })) || [],
        country: data.country ? { id: data.country.id, name: data.country.name, isNew: false } : { id: null, name: '', isNew: false },
        region: data.region?.map(r => ({ id: r.id, name: r.name, isNew: false })) || [],
        product_name: data.product_name || '',
        roast_type: data.roast_type || '',
        description: data.description || '',
        url: data.url || '',
        image_url: data.image_url || '',
        decaf: data.decaf || false,
        decaf_method: data.decaf_method ? { id: data.decaf_method.id, name: data.decaf_method.name, isNew: false } : { id: null, name: '', isNew: false },
        rating: data.rating || '',
        bean_process: data.bean_process || '',
        notes: data.notes || ''
      });
    } catch (err) {
      setError("Failed to fetch product for editing: " + err.message);
      console.error("Error fetching product:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({ 
      ...prev, 
      [name]: type === 'checkbox' ? checked : value 
    }));
  };

  const handleRatingChange = (rating) => {
    setFormData((prev) => ({ ...prev, rating: rating }));
  };


  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Basic validation
    if (!formData.roaster.name || formData.roaster.name.trim() === '') {
      setError('Roaster is required');
      setLoading(false);
      return;
    }

    const method = isEditMode ? 'PUT' : 'POST';
    // URL construction handled in apiFetch call

    // Transform form data for submission
    const submitData = {
      // Handle roaster
      roaster_id: formData.roaster.id,
      roaster_name: formData.roaster.name,
      
      // Handle bean types (multiple)
      bean_type_id: formData.bean_type.map(bt => bt.id).filter(id => id !== null),
      bean_type_name: formData.bean_type.map(bt => bt.name).filter(name => name),
      
      // Handle country
      country_id: formData.country.id,
      country_name: formData.country.name,
      
      // Handle regions (multiple)
      region_id: formData.region.map(r => r.id).filter(id => id !== null),
      region_name: formData.region.map(r => r.name).filter(name => name),
      
      // Handle decaf method
      decaf_method_id: formData.decaf_method.id,
      decaf_method_name: formData.decaf_method.name,
      
      // Include all other fields as-is
      product_name: formData.product_name,
      roast_type: formData.roast_type,
      description: formData.description,
      url: formData.url,
      image_url: formData.image_url,
      decaf: formData.decaf,
      rating: formData.rating,
      bean_process: formData.bean_process,
      notes: formData.notes
    };

    try {
      const response = await apiFetch(isEditMode ? `/products/${id}` : '/products', {
        method: method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`HTTP error! status: ${response.status} - ${errorData.message || 'Unknown error'}`);
      }

      const result = await response.json();
      addToast(`Product ${isEditMode ? 'updated' : 'created'} successfully!`, 'success');
      
      // Redirect to product detail page for both new and edited products
      if (!isEditMode && result.id) {
        navigate(`/products/${result.id}`);
      } else if (isEditMode) {
        navigate(`/products/${id}`);
      } else {
        navigate('/products');
      }
    } catch (err) {
      setError(`Failed to ${isEditMode ? 'update' : 'create'} product: ` + err.message);
      console.error("Error submitting product:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <p className="loading-message">Loading form...</p>;

  return (
    <div data-testid="product-form-container">
      <h2 data-testid="form-title">{isEditMode ? 'Edit Coffee Product' : 'Add New Coffee Product'}</h2>
      {error && <p className="error-message">{error}</p>}
      <form onSubmit={handleSubmit} data-testid="product-form">
        <label htmlFor="roaster-input">
          Roaster *:
          <HeadlessAutocomplete
            id="roaster-input"
            lookupType="roasters"
            value={formData.roaster}
            onChange={(value) => setFormData(prev => ({ ...prev, roaster: value }))}
            placeholder="Start typing to search roasters..."
            data-testid="roaster-autocomplete"
            aria-label="Roaster"
          />
        </label>
        <label htmlFor="bean-type-input">
          Bean Type:
          <HeadlessMultiAutocomplete
            id="bean-type-input"
            lookupType="bean_types"
            value={formData.bean_type}
            onChange={(value) => setFormData(prev => ({ ...prev, bean_type: value }))}
            placeholder="Start typing to search bean types..."
            data-testid="bean-type-multiautocomplete"
            aria-label="Bean Type"
          />
        </label>
        <label htmlFor="country-input">
          Country:
          <HeadlessAutocomplete
            id="country-input"
            lookupType="countries"
            value={formData.country}
            onChange={(value) => {
              setFormData(prev => ({ 
                ...prev, 
                country: value,
                // Clear regions when country changes
                region: prev.country.id !== value.id ? [] : prev.region
              }));
            }}
            placeholder="Start typing to search countries..."
            aria-label="Country"
          />
        </label>
        <label>
          Region:
          <RegionMultiAutocomplete
            countryId={formData.country.id}
            value={formData.region}
            onChange={(value) => setFormData(prev => ({ ...prev, region: value }))}
            placeholder="Start typing to search regions..."
          />
        </label>
        <label htmlFor="bean-process-input">
          Bean Process:
          <input
            type="text"
            id="bean-process-input"
            name="bean_process"
            value={formData.bean_process}
            onChange={handleChange}
            placeholder="e.g., Washed, Natural, Honey"
            data-testid="bean-process-input"
          />
        </label>
        <label htmlFor="product-name-input">
          Product Name: (optional custom name)
          <input
            type="text"
            id="product-name-input"
            name="product_name"
            value={formData.product_name}
            onChange={handleChange}
            placeholder="e.g., My favorite morning blend"
            data-testid="product-name-input"
          />
        </label>
        <label htmlFor="roast-type-input">
          Roast Type: (1-10 scale, 1=light, 10=dark)
          <input
            id="roast-type-input"
            type="number"
            name="roast_type"
            value={formData.roast_type}
            onChange={handleChange}
            min="1"
            max="10"
            placeholder="1-10"
            aria-label="Roast Type"
          />
        </label>
        <label>
          Description:
          <textarea name="description" value={formData.description} onChange={handleChange} rows="4"></textarea>
        </label>
        <label>
          Product URL:
          <input type="url" name="url" value={formData.url} onChange={handleChange} />
        </label>
        <label>
          Image URL:
          <input type="url" name="image_url" value={formData.image_url} onChange={handleChange} />
        </label>
        
        <label htmlFor="decaf-checkbox">
          <input
            type="checkbox"
            id="decaf-checkbox"
            name="decaf"
            checked={formData.decaf}
            onChange={handleChange}
            data-testid="decaf-checkbox"
          />
          Decaffeinated
        </label>
        
        {formData.decaf && (
          <label>
            Decaf Method:
            <HeadlessAutocomplete
              lookupType="decaf_methods"
              value={formData.decaf_method}
              onChange={(value) => setFormData(prev => ({ ...prev, decaf_method: value }))}
              placeholder="Start typing to search decaf methods..."
            />
          </label>
        )}
        
        <label htmlFor="rating-stars">
          Rating:
          <div style={{ marginTop: '8px' }}>
            <StarRating
              rating={formData.rating}
              onRatingChange={handleRatingChange}
              maxRating={5}
              size="xlarge"
              data-testid="product-rating-stars"
            />
          </div>
        </label>
        <label htmlFor="notes-textarea">
          Notes:
          <textarea
            id="notes-textarea"
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            rows="3"
            placeholder="Any additional notes about this product..."
            data-testid="notes-textarea"
          />
        </label>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            type="submit" 
            disabled={loading}
            data-testid={isEditMode ? 'update-product-btn' : 'add-product-btn'}
            style={{ 
              padding: '10px 15px', 
              border: 'none', 
              background: 'none', 
              cursor: loading ? 'default' : 'pointer', 
              fontSize: '20px',
              opacity: loading ? 0.5 : 1
            }}
            title={loading ? 'Saving...' : (isEditMode ? 'Update Product' : 'Add Product')}
            aria-label={loading ? 'Saving...' : (isEditMode ? 'Update Product' : 'Create Product')}
          >
            {loading ? ICONS.LOADING : (isEditMode ? ICONS.SAVE : ICONS.CREATE)}
          </button>
          <button 
            type="button"
            onClick={() => navigate('/products')}
            style={{ 
              padding: '10px 15px', 
              border: 'none', 
              background: 'none', 
              cursor: 'pointer', 
              fontSize: '20px'
            }}
            title="Cancel"
            aria-label="Cancel"
            data-testid="cancel-btn"
          >
            {ICONS.CANCEL}
          </button>
        </div>
      </form>
    </div>
  );
}

export default ProductForm;