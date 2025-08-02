import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useToast } from './Toast';
import { apiFetch } from '../config';
import { ICONS } from '../config/icons';
import DateTimeInput from './DateTimeInput';
import TimeInput from './TimeInput';

function BrewSessionForm({ product_batch_id = null, onSessionSubmitted, initialData = null }) {
  const navigate = useNavigate();
  const { id } = useParams();
  const { addToast } = useToast();
  const [formData, setFormData] = useState({
    product_batch_id: product_batch_id,
    product_id: '',
    brew_method: '',
    recipe: '',
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
        const [brewMethodsRes, recipesRes, grindersRes, filtersRes, kettlesRes, scalesRes, productsRes, defaultsRes] = await Promise.all([
          apiFetch('/brew_methods'),
          apiFetch('/recipes'),
          apiFetch('/grinders'),
          apiFetch('/filters'),
          apiFetch('/kettles'),
          apiFetch('/scales'),
          apiFetch('/products'),
          apiFetch('/brew_sessions/defaults'),
        ]);
        setBrewMethods(await brewMethodsRes.json());
        setRecipes(await recipesRes.json());
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


  // Handle mobile datalist issues
  const handleMobileDatalistFocus = (e) => {
    // On mobile, temporarily remove the list attribute to prevent sticky dropdown
    if (/Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
      e.target.removeAttribute('list');
    }
  };

  const handleMobileDatalistBlur = (e) => {
    // Restore the list attribute after blur
    if (/Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
      const listId = e.target.getAttribute('data-list');
      if (listId) {
        e.target.setAttribute('list', listId);
      }
    }
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

  if (error) return <p className="error-message">{error}</p>;
  if (initialLoading) return <div>Loading...</div>;

  return (
    <form 
      onSubmit={handleSubmit} 
      style={{ maxWidth: '1200px' }} 
      data-testid="brew-session-form"
    >
      <h4>{isEditMode ? 'Edit Brew Session' : 'Add New Brew Session'}</h4>
      
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
          <input
            type="text"
            id="recipe"
            name="recipe"
            value={formData.recipe}
            onChange={handleChange}
            list="recipesOptions"
            data-list="recipesOptions"
            onFocus={handleMobileDatalistFocus}
            onBlur={handleMobileDatalistBlur}
            placeholder="e.g., James Hoffmann V60"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
          <datalist id="recipesOptions">
            {recipes.map((r) => (
              <option key={r.id} value={r.name} />
            ))}
          </datalist>
        </div>
        
        <div>
          <label htmlFor="grinder" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Grinder
          </label>
          <input
            type="text"
            id="grinder"
            name="grinder"
            value={formData.grinder}
            onChange={handleChange}
            list="grindersOptions"
            data-list="grindersOptions"
            onFocus={handleMobileDatalistFocus}
            onBlur={handleMobileDatalistBlur}
            placeholder="e.g., Comandante, Wilfa Uniform"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
          <datalist id="grindersOptions">
            {grinders.map((g) => (
              <option key={g.id} value={g.name} />
            ))}
          </datalist>
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
          <input
            type="text"
            id="filter"
            name="filter"
            value={formData.filter}
            onChange={handleChange}
            list="filtersOptions"
            data-list="filtersOptions"
            onFocus={handleMobileDatalistFocus}
            onBlur={handleMobileDatalistBlur}
            placeholder="e.g., Hario V60, Paper Filter"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
          <datalist id="filtersOptions">
            {filters.map((f) => (
              <option key={f.id} value={f.name} />
            ))}
          </datalist>
        </div>
        
        <div>
          <label htmlFor="kettle" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Kettle
          </label>
          <input
            type="text"
            id="kettle"
            name="kettle"
            value={formData.kettle}
            onChange={handleChange}
            list="kettlesOptions"
            data-list="kettlesOptions"
            onFocus={handleMobileDatalistFocus}
            onBlur={handleMobileDatalistBlur}
            placeholder="e.g., Hario Buono, Fellow Stagg"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
          <datalist id="kettlesOptions">
            {kettles.map((k) => (
              <option key={k.id} value={k.name} />
            ))}
          </datalist>
        </div>
        
        <div>
          <label htmlFor="scale" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Scale
          </label>
          <input
            type="text"
            id="scale"
            name="scale"
            value={formData.scale}
            onChange={handleChange}
            list="scalesOptions"
            data-list="scalesOptions"
            onFocus={handleMobileDatalistFocus}
            onBlur={handleMobileDatalistBlur}
            placeholder="e.g., Acaia Pearl, Hario V60"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
          <datalist id="scalesOptions">
            {scales.map((s) => (
              <option key={s.id} value={s.name} />
            ))}
          </datalist>
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
        padding: '12px',
        backgroundColor: '#fff3cd',
        borderRadius: '4px',
        marginBottom: '16px'
      }}>
        <h5 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>Tasting Notes (1-10)</h5>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(80px, 1fr))',
          gap: '8px',
          marginBottom: '12px'
        }}>
          <div style={{ textAlign: 'center' }}>
            <label htmlFor="sweetness" style={{ fontSize: '11px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
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
              style={{ width: '50px', fontSize: '12px', padding: '2px', textAlign: 'center' }}
            />
          </div>
          <div style={{ textAlign: 'center' }}>
            <label htmlFor="acidity" style={{ fontSize: '11px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
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
              style={{ width: '50px', fontSize: '12px', padding: '2px', textAlign: 'center' }}
            />
          </div>
          <div style={{ textAlign: 'center' }}>
            <label htmlFor="bitterness" style={{ fontSize: '11px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
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
              style={{ width: '50px', fontSize: '12px', padding: '2px', textAlign: 'center' }}
            />
          </div>
          <div style={{ textAlign: 'center' }}>
            <label htmlFor="body" style={{ fontSize: '11px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
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
              style={{ width: '50px', fontSize: '12px', padding: '2px', textAlign: 'center' }}
            />
          </div>
          <div style={{ textAlign: 'center' }}>
            <label htmlFor="aroma" style={{ fontSize: '11px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
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
              style={{ width: '50px', fontSize: '12px', padding: '2px', textAlign: 'center' }}
            />
          </div>
          <div style={{ textAlign: 'center' }}>
            <label htmlFor="flavor_profile_match" style={{ fontSize: '11px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
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
              style={{ width: '50px', fontSize: '12px', padding: '2px', textAlign: 'center' }}
            />
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ textAlign: 'center' }}>
            <label htmlFor="score" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
              Overall Score (1-10)
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
              style={{ width: '60px', fontSize: '14px', padding: '4px', textAlign: 'center' }}
            />
          </div>
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
    </form>
  );
}

export default BrewSessionForm;