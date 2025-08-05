import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useToast } from './Toast';
import { apiFetch } from '../config';
import { ICONS } from '../config/icons';
import StarRating from './StarRating';
import BeanTypeMultiAutocomplete from './BeanTypeMultiAutocomplete';
import CountryAutocomplete from './CountryAutocomplete';
import RegionAutocomplete from './RegionAutocomplete';
import InlineChipAutocomplete from './InlineChipAutocomplete';

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
  const [roasters, setRoasters] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch roasters for the dropdown
        const roastersResponse = await apiFetch('/roasters');
        if (roastersResponse.ok) {
          const roastersData = await roastersResponse.json();
          setRoasters(roastersData);
        }

        // If ID exists, fetch product data for editing
        if (id) {
          setIsEditMode(true);
          await fetchProduct();
        }
      } catch (err) {
        setError("Failed to load data: " + err.message);
        console.error("Error loading data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const fetchProduct = async () => {
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
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({ 
      ...prev, 
      [name]: type === 'checkbox' ? checked : value 
    }));
  };

  const convertRoastType = (input) => {
    if (!input) return '';
    
    const str = input.toString().trim();
    
    // Check if it's a fraction (contains /)
    if (str.includes('/')) {
      const parts = str.split('/');
      if (parts.length === 2) {
        const numerator = parseFloat(parts[0]);
        const denominator = parseFloat(parts[1]);
        
        if (!isNaN(numerator) && !isNaN(denominator) && denominator > 0) {
          // Convert fraction to 1-10 scale
          const ratio = numerator / denominator;
          const scaledValue = Math.round(ratio * 10);
          return Math.max(1, Math.min(10, scaledValue)); // Clamp between 1-10
        }
      }
    }
    
    // Check if it's already a number between 1-10
    const num = parseFloat(str);
    if (!isNaN(num)) {
      return Math.max(1, Math.min(10, Math.round(num)));
    }
    
    return str; // Return as-is if not convertible
  };

  const handleRoastTypeChange = (e) => {
    const inputValue = e.target.value;
    const convertedValue = convertRoastType(inputValue);
    
    setFormData((prev) => ({ 
      ...prev, 
      roast_type: convertedValue
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
    <div data-testid="product-form-container" style={{ maxWidth: '1000px', margin: '0 auto', padding: '20px' }}>
      <h2 data-testid="form-title" style={{ marginBottom: '24px', color: '#333' }}>
        {isEditMode ? 'Edit Coffee Product' : 'Add New Coffee Product'}
      </h2>
      
      {error && (
        <div 
          className="error-message"
          style={{
            padding: '12px',
            backgroundColor: '#f8d7da',
            border: '1px solid #f5c6cb',
            borderRadius: '4px',
            color: '#721c24',
            marginBottom: '20px'
          }}
          role="alert"
          aria-live="polite"
        >
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} data-testid="product-form">
        {/* Basic Info Section */}
        <div style={{
          backgroundColor: '#f8f9fa',
          padding: '20px',
          borderRadius: '8px',
          marginBottom: '20px',
          border: '1px solid #e9ecef'
        }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: '#495057', display: 'flex', alignItems: 'center', gap: '8px' }}>
            ☕ Coffee Details
          </h3>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px',
            alignItems: 'end'
          }}>
            <div>
              <label htmlFor="roaster-select" style={{ fontSize: '14px', fontWeight: '500', display: 'block', marginBottom: '6px', color: '#495057' }}>
                Roaster *
              </label>
              <select
                id="roaster-select"
                name="roaster"
                value={formData.roaster?.name || ''}
                onChange={(e) => {
                  const selectedName = e.target.value;
                  if (selectedName) {
                    // Find the roaster object or create a new one
                    const existingRoaster = roasters.find(r => r.name === selectedName);
                    if (existingRoaster) {
                      setFormData(prev => ({ ...prev, roaster: { id: existingRoaster.id, name: existingRoaster.name, isNew: false } }));
                    } else {
                      setFormData(prev => ({ ...prev, roaster: { id: null, name: selectedName, isNew: true } }));
                    }
                  } else {
                    setFormData(prev => ({ ...prev, roaster: { id: null, name: '', isNew: false } }));
                  }
                }}
                required
                data-testid="roaster-select"
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #ced4da', borderRadius: '4px', fontSize: '14px', height: '32px', boxSizing: 'border-box' }}
              >
                <option value="">Select a roaster</option>
                {roasters.map((roaster) => (
                  <option key={roaster.id} value={roaster.name}>{roaster.name}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label htmlFor="product-name-input" style={{ fontSize: '14px', fontWeight: '500', display: 'block', marginBottom: '6px', color: '#495057' }}>
                Product Name <span style={{ fontWeight: '400', color: '#6c757d' }}>(optional)</span>
              </label>
              <input
                type="text"
                id="product-name-input"
                name="product_name"
                value={formData.product_name}
                onChange={handleChange}
                placeholder="e.g., My favorite morning blend"
                data-testid="product-name-input"
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #ced4da', borderRadius: '4px', fontSize: '14px', height: '32px', boxSizing: 'border-box' }}
              />
            </div>
            
            <div style={{ display: 'flex', alignItems: 'flex-end', height: '54px', paddingLeft: '20px', paddingBottom: '-10px', position: 'relative' }}>
              <div style={{ transform: 'translateY(12px)' }}>
                <StarRating
                  rating={formData.rating}
                  onRatingChange={handleRatingChange}
                  maxRating={5}
                  size="xlarge"
                  data-testid="product-rating-stars"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Origin Section */}
        <div style={{
          backgroundColor: '#e8f5e8',
          padding: '20px',
          borderRadius: '8px',
          marginBottom: '20px',
          border: '1px solid #c3e6c3'
        }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: '#495057', display: 'flex', alignItems: 'center', gap: '8px' }}>
            🌍 Origin
          </h3>
          
          <div style={{ marginBottom: '16px' }}>
            <label htmlFor="country-input" style={{ fontSize: '14px', fontWeight: '500', display: 'block', marginBottom: '6px', color: '#495057' }}>
              Country
            </label>
            <CountryAutocomplete
              id="country-input"
              value={formData.country}
              onChange={(value) => {
                setFormData(prev => ({ 
                  ...prev, 
                  country: value,
                  // Clear regions when country changes
                  region: prev.country.id !== value.id ? [] : prev.region
                }));
              }}
              placeholder="Search countries..."
              aria-label="Country"
            />
          </div>
          
          <div>
            <label style={{ fontSize: '14px', fontWeight: '500', display: 'block', marginBottom: '6px', color: '#495057' }}>
              Region
            </label>
            <RegionAutocomplete
              countryId={formData.country.id}
              value={formData.region}
              onChange={(value) => setFormData(prev => ({ ...prev, region: value }))}
              placeholder="Search regions..."
            />
          </div>
        </div>

        {/* Bean & Processing Section */}
        <div style={{
          backgroundColor: '#e8f4f8',
          padding: '20px',
          borderRadius: '8px',
          marginBottom: '20px',
          border: '1px solid #bee5eb'
        }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: '#495057', display: 'flex', alignItems: 'center', gap: '8px' }}>
            🫘 Bean & Processing
          </h3>
          
          {/* Bean Type - Full Width to Accommodate Chips */}
          <div style={{ marginBottom: '16px' }}>
            <label htmlFor="bean-type-input" style={{ fontSize: '14px', fontWeight: '500', display: 'block', marginBottom: '6px', color: '#495057' }}>
              Bean Type
            </label>
            <BeanTypeMultiAutocomplete
              id="bean-type-input"
              value={formData.bean_type}
              onChange={(value) => setFormData(prev => ({ ...prev, bean_type: value }))}
              placeholder="Start typing to search bean types..."
              data-testid="bean-type-multiautocomplete"
              aria-label="Bean Type"
            />
          </div>
          
          {/* Processing Details - Grid Layout */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px',
            marginBottom: '16px'
          }}>
            <div>
              <label htmlFor="bean-process-input" style={{ fontSize: '14px', fontWeight: '500', display: 'block', marginBottom: '6px', color: '#495057' }}>
                Bean Process
              </label>
              <input
                type="text"
                id="bean-process-input"
                name="bean_process"
                value={formData.bean_process}
                onChange={handleChange}
                placeholder="e.g., Washed, Natural, Honey"
                data-testid="bean-process-input"
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #ced4da', borderRadius: '4px', fontSize: '14px' }}
              />
            </div>
            
            <div>
              <label htmlFor="roast-type-input" style={{ fontSize: '14px', fontWeight: '500', display: 'block', marginBottom: '6px', color: '#495057' }}>
                Roast Level <span style={{ fontWeight: '400', color: '#6c757d' }}>(1-10 or fraction like 3/7)</span>
              </label>
              <input
                id="roast-type-input"
                type="text"
                name="roast_type"
                value={formData.roast_type}
                onChange={handleRoastTypeChange}
                placeholder="e.g., 5, 3/7, 2/5"
                aria-label="Roast Type"
                style={{ width: '100%', padding: '8px 12px', border: '1px solid #ced4da', borderRadius: '4px', fontSize: '14px' }}
              />
            </div>
          </div>

          {/* Decaf Options */}
          <div>
            <div style={{ marginBottom: '12px' }}>
              <label htmlFor="decaf-checkbox" style={{ fontSize: '14px', fontWeight: '500', display: 'flex', alignItems: 'center', color: '#495057' }}>
                <input
                  type="checkbox"
                  id="decaf-checkbox"
                  name="decaf"
                  checked={formData.decaf}
                  onChange={handleChange}
                  data-testid="decaf-checkbox"
                  style={{ marginRight: '8px' }}
                />
                Decaffeinated
              </label>
            </div>
            
            {formData.decaf && (
              <div>
                <label style={{ fontSize: '14px', fontWeight: '500', display: 'block', marginBottom: '6px', color: '#495057' }}>
                  Decaf Method
                </label>
                <InlineChipAutocomplete
                  lookupType="decaf_methods"
                  value={formData.decaf_method}
                  onChange={(value) => setFormData(prev => ({ ...prev, decaf_method: value }))}
                  placeholder="Select one decaf method..."
                  multiSelect={false}
                  singleSelectStyle={true}
                  maxHeight="200px"
                  data-testid="decaf-method-autocomplete"
                  aria-label="Decaf Method"
                />
              </div>
            )}
          </div>
        </div>

        {/* Additional Info Section */}
        <div style={{
          backgroundColor: '#fff3cd',
          padding: '20px',
          borderRadius: '8px',
          marginBottom: '24px',
          border: '1px solid #ffeaa7'
        }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: '#495057', display: 'flex', alignItems: 'center', gap: '8px' }}>
            📝 Additional Information
          </h3>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr',
            gap: '16px'
          }}>
            <div>
              <label style={{ fontSize: '14px', fontWeight: '500', display: 'block', marginBottom: '6px', color: '#495057' }}>
                Description
              </label>
              <textarea 
                name="description" 
                value={formData.description} 
                onChange={handleChange} 
                rows="3"
                placeholder="Describe the coffee's flavor profile, origin story, or other details..."
                style={{ 
                  width: '100%', 
                  padding: '8px 12px', 
                  border: '1px solid #ced4da', 
                  borderRadius: '4px', 
                  fontSize: '14px',
                  resize: 'vertical'
                }}
              />
            </div>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '16px'
            }}>
              <div>
                <label style={{ fontSize: '14px', fontWeight: '500', display: 'block', marginBottom: '6px', color: '#495057' }}>
                  Product URL
                </label>
                <input 
                  type="url" 
                  name="url" 
                  value={formData.url} 
                  onChange={handleChange}
                  placeholder="https://example.com/product"
                  style={{ width: '100%', padding: '8px 12px', border: '1px solid #ced4da', borderRadius: '4px', fontSize: '14px' }}
                />
              </div>
              
              <div>
                <label style={{ fontSize: '14px', fontWeight: '500', display: 'block', marginBottom: '6px', color: '#495057' }}>
                  Image URL
                </label>
                <input 
                  type="url" 
                  name="image_url" 
                  value={formData.image_url} 
                  onChange={handleChange}
                  placeholder="https://example.com/image.jpg"
                  style={{ width: '100%', padding: '8px 12px', border: '1px solid #ced4da', borderRadius: '4px', fontSize: '14px' }}
                />
              </div>
            </div>
            
            <div>
              <label htmlFor="notes-textarea" style={{ fontSize: '14px', fontWeight: '500', display: 'block', marginBottom: '6px', color: '#495057' }}>
                Personal Notes
              </label>
              <textarea
                id="notes-textarea"
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                rows="2"
                placeholder="Your personal notes about this coffee..."
                data-testid="notes-textarea"
                style={{ 
                  width: '100%', 
                  padding: '8px 12px', 
                  border: '1px solid #ced4da', 
                  borderRadius: '4px', 
                  fontSize: '14px',
                  resize: 'vertical'
                }}
              />
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ 
          display: 'flex', 
          gap: '10px', 
          justifyContent: 'flex-end',
          paddingTop: '20px',
          borderTop: '1px solid #e9ecef'
        }}>
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
            disabled={loading}
            style={{ 
              padding: '10px 15px', 
              border: 'none', 
              background: 'none', 
              cursor: loading ? 'default' : 'pointer', 
              fontSize: '20px',
              opacity: loading ? 0.5 : 1
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