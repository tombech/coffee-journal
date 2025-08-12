import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useToast } from './Toast';
import { apiFetch } from '../config';
import { ICONS } from '../config/icons';
import DateTimeInput from './DateTimeInput';
import TimeInput from './TimeInput';
import BrewRecommendations from './BrewRecommendations';

function BrewSessionForm({ product_batch_id = null, onSessionSubmitted, initialData = null, onCancel }) {
  const navigate = useNavigate();
  const { id } = useParams();
  const { addToast } = useToast();
  const [formData, setFormData] = useState({
    product_batch_id: product_batch_id,
    product_id: '',
    brew_method: '',
    recipe: '',
    brewer: '',
    grinder: '',
    grinder_setting: '',
    filter: '',
    kettle: '',
    scale: '',
    amount_coffee_grams: '',
    amount_water_grams: '',
    brew_temperature_c: '',
    // brew_ratio: '', // <-- REMOVED
    bloom_time_seconds: '',
    brew_time_seconds: '',
    sweetness: '',
    acidity: '',
    bitterness: '',
    body: '',
    aroma: '',
    flavor_profile_match: '',
    score: '',
    notes: '',
    timestamp: new Date().toISOString(), // Default to now
  });
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditMode, setIsEditMode] = useState(false);

  // State for dynamic dropdown options
  const [brewMethods, setBrewMethods] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [brewers, setBrewers] = useState([]);
  const [grinders, setGrinders] = useState([]);
  const [filters, setFilters] = useState([]);
  const [kettles, setKettles] = useState([]);
  const [scales, setScales] = useState([]);
  const [products, setProducts] = useState([]);
  const [batches, setBatches] = useState([]);

  useEffect(() => {
    const fetchAllData = async () => {
      setInitialLoading(true);
      try {
        // First, fetch all lookup data and smart defaults
        const [brewMethodsRes, recipesRes, brewersRes, grindersRes, filtersRes, kettlesRes, scalesRes, productsRes, defaultsRes] = await Promise.all([
          apiFetch('/brew_methods'),
          apiFetch('/recipes'),
          apiFetch('/brewers'),
          apiFetch('/grinders'),
          apiFetch('/filters'),
          apiFetch('/kettles'),
          apiFetch('/scales'),
          apiFetch('/products'),
          apiFetch('/brew_sessions/defaults'),
        ]);
        setBrewMethods(await brewMethodsRes.json());
        setRecipes(await recipesRes.json());
        setBrewers(await brewersRes.json());
        setGrinders(await grindersRes.json());
        setFilters(await filtersRes.json());
        setKettles(await kettlesRes.json());
        setScales(await scalesRes.json());
        const productsData = await productsRes.json();
        setProducts(productsData);
        
        // Get smart defaults
        const smartDefaults = defaultsRes.ok ? await defaultsRes.json() : {};

        // If we have an id parameter but no initialData, this is edit mode from URL
        if (id && !initialData) {
          const sessionResponse = await apiFetch(`/brew_sessions/${id}/detail`);
          if (sessionResponse.ok) {
            const sessionData = await sessionResponse.json();
            const session = sessionData.session;
            setIsEditMode(true);
            setFormData({
              ...session,
              // Extract names from lookup objects
              brew_method: session.brew_method?.name || '',
              recipe: session.recipe?.name || '',
              brewer: session.brewer?.name || '',
              grinder: session.grinder?.name || '',
              filter: session.filter?.name || '',
              kettle: session.kettle?.name || '',
              scale: session.scale?.name || '',
              timestamp: session.timestamp || new Date().toISOString(),
            });
            // Fetch batches for the product
            if (session.product_id) {
              await fetchBatchesForProduct(session.product_id);
            }
          } else {
            throw new Error('Failed to load brew session for editing');
          }
        }
        // Then, if we have a product_batch_id but no initialData, fetch batch details
        else if (product_batch_id && !initialData) {
          const batchResponse = await apiFetch(`/batches/${product_batch_id}`);
          if (batchResponse.ok) {
            const batch = await batchResponse.json();
            // Set both product_id and product_batch_id from the batch
            setFormData(prev => ({
              ...prev,
              product_id: batch.product_id,
              product_batch_id: product_batch_id,
              // Apply smart defaults for new sessions
              brew_method: smartDefaults.brew_method?.name || '',
              recipe: smartDefaults.recipe?.name || '',
              grinder: smartDefaults.grinder?.name || '',
              filter: smartDefaults.filter?.name || '',
              kettle: smartDefaults.kettle?.name || '',
              scale: smartDefaults.scale?.name || '',
            }));
            // Fetch batches for this product
            await fetchBatchesForProduct(batch.product_id);
          } else {
            throw new Error('Failed to load batch details');
          }
        }
        // Apply smart defaults for new sessions without batch ID
        else if (!id && !initialData && !product_batch_id) {
          setFormData(prev => ({
            ...prev,
            // Apply smart defaults
            brew_method: smartDefaults.brew_method?.name || '',
            recipe: smartDefaults.recipe?.name || '',
            grinder: smartDefaults.grinder?.name || '',
            filter: smartDefaults.filter?.name || '',
            kettle: smartDefaults.kettle?.name || '',
            scale: smartDefaults.scale?.name || '',
          }));
        }
      } catch (err) {
        console.error("Error fetching data:", err);
        setError(err.message || "Failed to load data.");
      } finally {
        setInitialLoading(false);
      }
    };

    fetchAllData();

    if (initialData) {
      setIsEditMode(true);
      setFormData({
        ...initialData,
        // Extract names from lookup objects
        brew_method: initialData.brew_method?.name || '',
        recipe: initialData.recipe?.name || '',
        grinder: initialData.grinder?.name || '',
        filter: initialData.filter?.name || '',
        kettle: initialData.kettle?.name || '',
        scale: initialData.scale?.name || '',
        timestamp: initialData.timestamp || new Date().toISOString(),
      });
      // If editing, fetch batches for the selected product
      if (initialData.product_id) {
        fetchBatchesForProduct(initialData.product_id);
      }
    } else if (!id) {
      // Only set default state if not in edit mode (no id parameter)
      setIsEditMode(false);
      // Defaults are now set in fetchAllData above
    }
  }, [product_batch_id, initialData, id]);

  // Fetch batches when product is selected
  const fetchBatchesForProduct = async (productId) => {
    try {
      const response = await apiFetch(`/products/${productId}/batches`);
      if (response.ok) {
        const batchData = await response.json();
        setBatches(batchData);
      }
    } catch (err) {
      console.error("Error fetching batches:", err);
    }
  };

  // Norwegian date formatting
  const formatDateNorwegian = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear().toString().slice(-2);
    return `${day}.${month}.${year}`;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    
    // If product is selected, fetch its batches
    if (name === 'product_id' && value) {
      fetchBatchesForProduct(value);
      setFormData((prev) => ({ ...prev, product_batch_id: '' })); // Reset batch selection
    }
  };

  // Handle applying brew recommendations
  const handleApplyRecommendation = (recommendedData) => {
    setFormData(prev => ({
      ...prev,
      ...recommendedData
    }));
  };



  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Validate that batch is selected (both for new sessions and edit mode)
    if (!formData.product_batch_id) {
      setError('Please select a batch');
      setLoading(false);
      return;
    }

    const method = isEditMode ? 'PUT' : 'POST';
    // URL construction handled in apiFetch call

    try {
      const response = await apiFetch(isEditMode 
        ? `/brew_sessions/${id || initialData.id}` 
        : `/batches/${formData.product_batch_id}/brew_sessions`, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`HTTP error! status: ${response.status} - ${errorData.message || 'Unknown error'}`);
      }

      addToast(`Brew session ${isEditMode ? 'updated' : 'created'} successfully!`, 'success');
      
      if (onSessionSubmitted) {
        onSessionSubmitted();
      } else if (isEditMode && id) {
        // Navigate back to detail page after editing
        navigate(`/brew-sessions/${id}`);
      }
    } catch (err) {
      setError(`Failed to ${isEditMode ? 'update' : 'create'} brew session: ` + err.message);
      console.error("Error submitting brew session:", err);
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) return <div>Loading...</div>;

  return (
    <form 
      onSubmit={handleSubmit} 
      style={{ maxWidth: '1200px' }} 
      data-testid="brew-session-form"
    >
      <h4>{isEditMode ? 'Edit Brew Session' : 'Add New Brew Session'}</h4>
      
      {error && (
        <div style={{
          padding: '12px',
          backgroundColor: '#f8d7da',
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
          color: '#721c24',
          marginBottom: '16px'
        }}>
          {error}
        </div>
      )}
      
      {/* Basic Info Section */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '12px',
        marginBottom: '16px'
      }}>
        <div>
          <label style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Timestamp
          </label>
          <DateTimeInput
            name="timestamp"
            value={formData.timestamp}
            onChange={handleChange}
            required
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        {/* Product and Batch selection - show if not tied to a specific batch OR if editing */}
        {(!product_batch_id || isEditMode) && (
          <>
            <div>
              <label style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
                Product
              </label>
              <select
                name="product_id"
                value={formData.product_id}
                onChange={handleChange}
                required
                style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
              >
                <option value="">Select a product</option>
                {products.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.product_name} ({
                      typeof product.roaster === 'object' 
                        ? product.roaster?.name || 'Unknown'
                        : product.roaster || 'Unknown'
                    })
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
                Batch
              </label>
              <select
                name="product_batch_id"
                value={formData.product_batch_id}
                onChange={handleChange}
                required
                disabled={!formData.product_id}
                style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
              >
                <option value="">Select a batch</option>
                {batches.map((batch) => (
                  <option key={batch.id} value={batch.id}>
                    Roast Date: {formatDateNorwegian(batch.roast_date)} ({batch.amount_grams}g)
                  </option>
                ))}
              </select>
            </div>
          </>
        )}
      </div>

      {/* Brew Recommendations */}
      <BrewRecommendations 
        productId={formData.product_id} 
        selectedMethod={formData.brew_method}
        onApplyRecommendation={handleApplyRecommendation}
      />

      {/* Equipment Section */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '8px',
        marginBottom: '16px',
        padding: '12px',
        backgroundColor: '#f8f9fa',
        borderRadius: '4px'
      }}>
        <div>
          <label htmlFor="brew_method" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Brew Method *
          </label>
          <select
            id="brew_method"
            name="brew_method"
            value={formData.brew_method}
            onChange={handleChange}
            required
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          >
            <option value="">Select brew method</option>
            {brewMethods.map((bm) => (
              <option key={bm.id} value={bm.name}>{bm.name}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label htmlFor="recipe" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Recipe
          </label>
          <select
            id="recipe"
            name="recipe"
            value={formData.recipe}
            onChange={handleChange}
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          >
            <option value="">Select recipe</option>
            {recipes.map((r) => (
              <option key={r.id} value={r.name}>{r.name}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label htmlFor="brewer" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Brewer/Machine
          </label>
          <select
            id="brewer"
            name="brewer"
            value={formData.brewer}
            onChange={handleChange}
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          >
            <option value="">Select brewer</option>
            {brewers.map((b) => (
              <option key={b.id} value={b.name}>{b.name}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label htmlFor="grinder" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Grinder
          </label>
          <select
            id="grinder"
            name="grinder"
            value={formData.grinder}
            onChange={handleChange}
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          >
            <option value="">Select grinder</option>
            {grinders.map((g) => (
              <option key={g.id} value={g.name}>{g.name}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label htmlFor="grinder_setting" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Grind Size
          </label>
          <input 
            type="text" 
            id="grinder_setting"
            name="grinder_setting" 
            value={formData.grinder_setting} 
            onChange={handleChange}
            placeholder="e.g., 15, Medium-Fine"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="filter" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Filter
          </label>
          <select
            id="filter"
            name="filter"
            value={formData.filter}
            onChange={handleChange}
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          >
            <option value="">Select filter</option>
            {filters.map((f) => (
              <option key={f.id} value={f.name}>{f.name}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label htmlFor="kettle" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Kettle
          </label>
          <select
            id="kettle"
            name="kettle"
            value={formData.kettle}
            onChange={handleChange}
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          >
            <option value="">Select kettle</option>
            {kettles.map((k) => (
              <option key={k.id} value={k.name}>{k.name}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label htmlFor="scale" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Scale
          </label>
          <select
            id="scale"
            name="scale"
            value={formData.scale}
            onChange={handleChange}
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          >
            <option value="">Select scale</option>
            {scales.map((s) => (
              <option key={s.id} value={s.name}>{s.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Brewing Parameters Section */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
        gap: '8px',
        marginBottom: '16px',
        padding: '12px',
        backgroundColor: '#e8f4f8',
        borderRadius: '4px'
      }}>
        <div>
          <label htmlFor="amount_coffee_grams" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Coffee Grams *
          </label>
          <input 
            type="number" 
            id="amount_coffee_grams"
            name="amount_coffee_grams" 
            value={formData.amount_coffee_grams} 
            onChange={handleChange} 
            step="0.1" 
            required
            placeholder="18"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="amount_water_grams" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Water Grams *
          </label>
          <input 
            type="number" 
            id="amount_water_grams"
            name="amount_water_grams" 
            value={formData.amount_water_grams} 
            onChange={handleChange} 
            step="0.1" 
            required
            placeholder="300"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="brew_temperature_c" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Temperature
          </label>
          <input 
            type="number" 
            id="brew_temperature_c"
            name="brew_temperature_c" 
            value={formData.brew_temperature_c} 
            onChange={handleChange} 
            step="0.1"
            placeholder="93"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Bloom Time
          </label>
          <TimeInput 
            name="bloom_time_seconds" 
            value={formData.bloom_time_seconds} 
            onChange={handleChange} 
            placeholder="0:30"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="brew_time_seconds" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Brew Time Seconds
          </label>
          <TimeInput 
            id="brew_time_seconds"
            name="brew_time_seconds" 
            value={formData.brew_time_seconds} 
            onChange={handleChange} 
            placeholder="2:30"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
      </div>

      {/* Tasting Notes Section */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
        gap: '8px',
        marginBottom: '16px',
        padding: '12px',
        backgroundColor: '#fff3cd',
        borderRadius: '4px'
      }}>
        <div>
          <label htmlFor="sweetness" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Sweetness
          </label>
          <input 
            type="number" 
            id="sweetness"
            name="sweetness" 
            value={formData.sweetness} 
            onChange={handleChange} 
            min="0" 
            max="10" 
            step="0.5"
            placeholder="0-10"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="acidity" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Acidity
          </label>
          <input 
            type="number" 
            id="acidity"
            name="acidity" 
            value={formData.acidity} 
            onChange={handleChange} 
            min="0" 
            max="10" 
            step="0.5"
            placeholder="0-10"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="bitterness" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Bitterness
          </label>
          <input 
            type="number" 
            id="bitterness"
            name="bitterness" 
            value={formData.bitterness} 
            onChange={handleChange} 
            min="0" 
            max="10" 
            step="0.5"
            placeholder="0-10"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="body" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Body
          </label>
          <input 
            type="number" 
            id="body"
            name="body" 
            value={formData.body} 
            onChange={handleChange} 
            min="0" 
            max="10" 
            step="0.5"
            placeholder="0-10"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="aroma" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Aroma
          </label>
          <input 
            type="number" 
            id="aroma"
            name="aroma" 
            value={formData.aroma} 
            onChange={handleChange} 
            min="0" 
            max="10" 
            step="0.5"
            placeholder="0-10"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="flavor_profile_match" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Profile Match
          </label>
          <input 
            type="number" 
            id="flavor_profile_match"
            name="flavor_profile_match" 
            value={formData.flavor_profile_match} 
            onChange={handleChange} 
            min="0" 
            max="10" 
            step="0.5"
            placeholder="0-10"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="score" style={{ fontSize: '12px', fontWeight: 'bold', display: 'flex', alignItems: 'center', marginBottom: '4px', gap: '4px' }}>
            Overall Score
            <span 
              style={{ 
                fontSize: '10px', 
                color: '#666', 
                cursor: 'help',
                backgroundColor: '#f0f0f0',
                borderRadius: '50%',
                width: '14px',
                height: '14px',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'bold'
              }}
              title="Optional: Leave empty to use auto-calculated score from tasting notes. Enter a value to override the automatic calculation."
              aria-label="Optional field with automatic calculation"
            >
              ?
            </span>
          </label>
          <input 
            type="number" 
            id="score"
            name="score" 
            value={formData.score} 
            onChange={handleChange} 
            min="0" 
            max="10" 
            step="0.5"
            placeholder="0-10, optional"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
      </div>

      {/* Notes Section */}
      <div style={{ marginBottom: '16px' }}>
        <label htmlFor="notes" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
          Notes
        </label>
        <textarea 
          id="notes"
          name="notes" 
          value={formData.notes} 
          onChange={handleChange} 
          rows="3"
          style={{ width: '100%', fontSize: '14px', padding: '8px', resize: 'vertical' }}
          placeholder="Tasting notes, observations, adjustments for next time..."
        />
      </div>

      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
        <button 
          type="button" 
          disabled={loading}
          data-testid="submit-brew-session"
          aria-label={loading ? 'Saving...' : (isEditMode ? 'Update' : 'Create')}
          style={{ 
            padding: '10px 15px', 
            border: 'none', 
            background: 'none', 
            cursor: loading ? 'default' : 'pointer', 
            fontSize: '20px',
            opacity: loading ? 0.5 : 1
          }}
          title={loading ? 'Saving...' : (isEditMode ? 'Update Session' : 'Log Session')}
          onClick={async (e) => {
            e.preventDefault();
            await handleSubmit(e);
          }}
        >
          {loading ? ICONS.LOADING : ICONS.SAVE}
        </button>
        
        {(onCancel || isEditMode) && (
          <button 
            type="button" 
            onClick={onCancel || (() => navigate(`/brew-sessions/${id}`))} 
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
          >
            {ICONS.CANCEL}
          </button>
        )}
      </div>
    </form>
  );
}

export default BrewSessionForm;