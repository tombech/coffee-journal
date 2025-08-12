import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useToast } from '../Toast';
import { apiFetch } from '../../config';
import { ICONS } from '../../config/icons';
import DateTimeInput from '../DateTimeInput';

function ShotForm({ product_batch_id = null, onShotSubmitted, initialData = null, onCancel }) {
  const navigate = useNavigate();
  const { id } = useParams();
  const { addToast } = useToast();
  const [formData, setFormData] = useState({
    product_batch_id: product_batch_id,
    product_id: '',
    shot_session_id: '',
    brewer_id: '',
    grinder_id: '',
    portafilter_id: '',
    basket_id: '',
    scale_id: '',
    recipe_id: '',
    dose_grams: '',
    yield_grams: '',
    preinfusion_seconds: '',
    extraction_time_seconds: '',
    pressure_bars: '',
    water_temperature_c: '',
    grinder_setting: '',
    sweetness: '',
    acidity: '',
    bitterness: '',
    body: '',
    aroma: '',
    crema: '',
    flavor_profile_match: '',
    extraction_status: '',
    notes: '',
    overall_score: '',
    timestamp: new Date().toISOString(),
  });
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditMode, setIsEditMode] = useState(false);

  // State for dynamic dropdown options
  const [brewers, setBrewers] = useState([]);
  const [grinders, setGrinders] = useState([]);
  const [portafilters, setPortafilters] = useState([]);
  const [baskets, setBaskets] = useState([]);
  const [scales, setScales] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [products, setProducts] = useState([]);
  const [batches, setBatches] = useState([]);
  const [shotSessions, setShotSessions] = useState([]);

  useEffect(() => {
    const fetchAllData = async () => {
      setInitialLoading(true);
      try {
        const [brewersRes, grindersRes, portafiltersRes, basketsRes, scalesRes, recipesRes, productsRes, shotSessionsRes] = await Promise.all([
          apiFetch('/brewers'),
          apiFetch('/grinders'),
          apiFetch('/portafilters'),
          apiFetch('/baskets'),
          apiFetch('/scales'),
          apiFetch('/recipes'),
          apiFetch('/products'),
          apiFetch('/shot_sessions'),
        ]);
        
        setBrewers(await brewersRes.json());
        setGrinders(await grindersRes.json());
        setPortafilters(await portafiltersRes.json());
        setBaskets(await basketsRes.json());
        setScales(await scalesRes.json());
        setRecipes(await recipesRes.json());
        const productsData = await productsRes.json();
        setProducts(productsData);
        const shotSessionsData = await shotSessionsRes.json();
        // Extract data array from paginated response
        setShotSessions(shotSessionsData.data || shotSessionsData);

        // If we have an id parameter but no initialData, this is edit mode from URL
        if (id && !initialData) {
          const shotResponse = await apiFetch(`/shots/${id}`);
          if (shotResponse.ok) {
            const shotData = await shotResponse.json();
            setIsEditMode(true);
            setFormData({
              ...shotData,
              timestamp: shotData.timestamp || new Date().toISOString(),
            });
            // Fetch batches for the product if we have product_id
            if (shotData.product_id) {
              const batchesResponse = await apiFetch(`/products/${shotData.product_id}/batches`);
              if (batchesResponse.ok) {
                setBatches(await batchesResponse.json());
              }
            }
          }
        } else if (initialData) {
          // Edit mode with provided data
          setIsEditMode(true);
          setFormData({
            ...initialData,
            timestamp: initialData.timestamp || new Date().toISOString(),
          });
          if (initialData.product_id) {
            const batchesResponse = await apiFetch(`/products/${initialData.product_id}/batches`);
            if (batchesResponse.ok) {
              setBatches(await batchesResponse.json());
            }
          }
        } else if (product_batch_id) {
          // New shot for specific batch
          const batchResponse = await apiFetch(`/batches/${product_batch_id}`);
          if (batchResponse.ok) {
            const batchData = await batchResponse.json();
            setFormData(prev => ({
              ...prev,
              product_batch_id: product_batch_id,
              product_id: batchData.product_id
            }));
            // Fetch batches for the product
            const batchesResponse = await apiFetch(`/products/${batchData.product_id}/batches`);
            if (batchesResponse.ok) {
              setBatches(await batchesResponse.json());
            }
          }
        }
      } catch (err) {
        setError("Failed to load form data: " + err.message);
        console.error("Error loading form data:", err);
      } finally {
        setInitialLoading(false);
      }
    };

    fetchAllData();
  }, [id, initialData, product_batch_id]);

  // Fetch batches when product changes
  useEffect(() => {
    if (formData.product_id) {
      const fetchBatches = async () => {
        try {
          const response = await apiFetch(`/products/${formData.product_id}/batches`);
          if (response.ok) {
            setBatches(await response.json());
          }
        } catch (err) {
          console.error("Error fetching batches:", err);
        }
      };
      fetchBatches();
    } else {
      setBatches([]);
    }
  }, [formData.product_id]);

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
      // Prepare data for submission
      const submitData = { ...formData };
      
      // Convert numeric fields
      const numericFields = [
        'dose_grams', 'yield_grams', 'preinfusion_seconds', 'extraction_time_seconds',
        'pressure_bars', 'water_temperature_c', 'sweetness', 'acidity', 'bitterness',
        'body', 'aroma', 'crema', 'flavor_profile_match', 'overall_score'
      ];
      
      numericFields.forEach(field => {
        if (submitData[field] === '') {
          delete submitData[field];
        } else if (submitData[field] !== undefined && submitData[field] !== null) {
          submitData[field] = parseFloat(submitData[field]);
        }
      });

      // Convert ID fields to integers
      const idFields = [
        'product_id', 'product_batch_id', 'shot_session_id', 'brewer_id',
        'grinder_id', 'portafilter_id', 'basket_id', 'scale_id', 'recipe_id'
      ];
      
      idFields.forEach(field => {
        if (submitData[field] === '') {
          delete submitData[field];
        } else if (submitData[field] !== undefined && submitData[field] !== null) {
          submitData[field] = parseInt(submitData[field]);
        }
      });

      // Remove empty strings and null values
      Object.keys(submitData).forEach(key => {
        if (submitData[key] === '' || submitData[key] === null) {
          delete submitData[key];
        }
      });

      let response;
      if (isEditMode) {
        const shotId = id || initialData?.id;
        response = await apiFetch(`/shots/${shotId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(submitData),
        });
      } else {
        response = await apiFetch('/shots', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(submitData),
        });
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      addToast(`Shot ${isEditMode ? 'updated' : 'created'} successfully!`, 'success');

      if (onShotSubmitted) {
        onShotSubmitted();
      } else if (!isEditMode) {
        navigate(`/shots/${result.id}`);
      } else {
        navigate(`/shots/${result.id}`);
      }
    } catch (err) {
      setError("Failed to save shot: " + err.message);
      console.error("Error saving shot:", err);
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) return <p className="loading-message">Loading shot form...</p>;

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        
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

        {/* Basic Information */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
          <div>
            <label htmlFor="product_id" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              {ICONS.COFFEE} Product *
            </label>
            <select
              id="product_id"
              name="product_id"
              value={formData.product_id}
              onChange={handleInputChange}
              required
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Select a product</option>
              {products.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.product_name} ({product.roaster?.name || 'Unknown roaster'})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="product_batch_id" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              📦 Batch *
            </label>
            <select
              id="product_batch_id"
              name="product_batch_id"
              value={formData.product_batch_id}
              onChange={handleInputChange}
              required
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Select a batch</option>
              {batches.map((batch) => (
                <option key={batch.id} value={batch.id}>
                  Batch {batch.id} - {new Date(batch.roast_date).toLocaleDateString()}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Equipment */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px' }}>
          <div>
            <label htmlFor="brewer_id" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              ☕ Brewer *
            </label>
            <select
              id="brewer_id"
              name="brewer_id"
              value={formData.brewer_id}
              onChange={handleInputChange}
              required
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Select a brewer</option>
              {brewers.map((brewer) => (
                <option key={brewer.id} value={brewer.id}>
                  {brewer.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="grinder_id" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              ⚙️ Grinder
            </label>
            <select
              id="grinder_id"
              name="grinder_id"
              value={formData.grinder_id}
              onChange={handleInputChange}
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Select a grinder</option>
              {grinders.map((grinder) => (
                <option key={grinder.id} value={grinder.id}>
                  {grinder.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="grinder_setting" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              🎛️ Grinder Setting
            </label>
            <input
              type="text"
              id="grinder_setting"
              name="grinder_setting"
              value={formData.grinder_setting}
              onChange={handleInputChange}
              placeholder="e.g., 15, fine, medium"
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            />
          </div>
        </div>

        {/* Espresso-specific Equipment */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px' }}>
          <div>
            <label htmlFor="portafilter_id" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              🔧 Portafilter
            </label>
            <select
              id="portafilter_id"
              name="portafilter_id"
              value={formData.portafilter_id}
              onChange={handleInputChange}
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Select a portafilter</option>
              {portafilters.map((portafilter) => (
                <option key={portafilter.id} value={portafilter.id}>
                  {portafilter.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="basket_id" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              🗂️ Basket
            </label>
            <select
              id="basket_id"
              name="basket_id"
              value={formData.basket_id}
              onChange={handleInputChange}
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Select a basket</option>
              {baskets.map((basket) => (
                <option key={basket.id} value={basket.id}>
                  {basket.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="scale_id" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              ⚖️ Scale
            </label>
            <select
              id="scale_id"
              name="scale_id"
              value={formData.scale_id}
              onChange={handleInputChange}
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Select a scale</option>
              {scales.map((scale) => (
                <option key={scale.id} value={scale.id}>
                  {scale.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Shot Parameters */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '15px' }}>
          <div>
            <label htmlFor="dose_grams" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              ⚖️ Dose (g) *
            </label>
            <input
              type="number"
              id="dose_grams"
              name="dose_grams"
              value={formData.dose_grams}
              onChange={handleInputChange}
              step="0.1"
              min="0"
              required
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            />
          </div>

          <div>
            <label htmlFor="yield_grams" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              ☕ Yield (g) *
            </label>
            <input
              type="number"
              id="yield_grams"
              name="yield_grams"
              value={formData.yield_grams}
              onChange={handleInputChange}
              step="0.1"
              min="0"
              required
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            />
          </div>

          <div>
            <label htmlFor="extraction_time_seconds" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              ⏱️ Extraction Time (s)
            </label>
            <input
              type="number"
              id="extraction_time_seconds"
              name="extraction_time_seconds"
              value={formData.extraction_time_seconds}
              onChange={handleInputChange}
              min="0"
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            />
          </div>

          <div>
            <label htmlFor="water_temperature_c" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              🌡️ Water Temperature (°C)
            </label>
            <input
              type="number"
              id="water_temperature_c"
              name="water_temperature_c"
              value={formData.water_temperature_c}
              onChange={handleInputChange}
              min="0"
              max="100"
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            />
          </div>
        </div>

        {/* Advanced Parameters */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
          <div>
            <label htmlFor="preinfusion_seconds" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              💧 Preinfusion (s)
            </label>
            <input
              type="number"
              id="preinfusion_seconds"
              name="preinfusion_seconds"
              value={formData.preinfusion_seconds}
              onChange={handleInputChange}
              min="0"
              step="0.1"
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            />
          </div>

          <div>
            <label htmlFor="pressure_bars" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              📊 Pressure (bars)
            </label>
            <input
              type="number"
              id="pressure_bars"
              name="pressure_bars"
              value={formData.pressure_bars}
              onChange={handleInputChange}
              min="0"
              step="0.1"
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            />
          </div>
        </div>

        {/* Tasting Notes */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr 1fr', gap: '10px' }}>
          {[
            { field: 'sweetness', label: '🍯 Sweetness', icon: '🍯' },
            { field: 'acidity', label: '🍋 Acidity', icon: '🍋' },
            { field: 'body', label: '🥛 Body', icon: '🥛' },
            { field: 'aroma', label: '👃 Aroma', icon: '👃' },
            { field: 'crema', label: '☁️ Crema', icon: '☁️' }
          ].map(({ field, label, icon }) => (
            <div key={field}>
              <label htmlFor={field} style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', fontSize: '12px' }}>
                {label}
              </label>
              <input
                type="number"
                id={field}
                name={field}
                value={formData[field]}
                onChange={handleInputChange}
                min="0"
                max="10"
                step="0.1"
                style={{ width: '100%', padding: '6px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '12px' }}
              />
            </div>
          ))}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
          <div>
            <label htmlFor="bitterness" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              🥀 Bitterness (0-10)
            </label>
            <input
              type="number"
              id="bitterness"
              name="bitterness"
              value={formData.bitterness}
              onChange={handleInputChange}
              min="0"
              max="10"
              step="0.1"
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            />
          </div>

          <div>
            <label htmlFor="flavor_profile_match" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              🎯 Flavor Profile Match (0-10)
            </label>
            <input
              type="number"
              id="flavor_profile_match"
              name="flavor_profile_match"
              value={formData.flavor_profile_match}
              onChange={handleInputChange}
              min="0"
              max="10"
              step="0.1"
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            />
          </div>
        </div>

        {/* Extraction Status and Overall Score */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
          <div>
            <label htmlFor="extraction_status" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              🎯 Extraction Status
            </label>
            <select
              id="extraction_status"
              name="extraction_status"
              value={formData.extraction_status}
              onChange={handleInputChange}
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Select status</option>
              <option value="perfect">Perfect</option>
              <option value="channeling">Channeling</option>
              <option value="over-extracted">Over-extracted</option>
              <option value="under-extracted">Under-extracted</option>
            </select>
          </div>

          <div>
            <label htmlFor="overall_score" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              ⭐ Overall Score (0-10)
            </label>
            <input
              type="number"
              id="overall_score"
              name="overall_score"
              value={formData.overall_score}
              onChange={handleInputChange}
              min="0"
              max="10"
              step="0.1"
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            />
          </div>
        </div>

        {/* Session and Recipe */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
          <div>
            <label htmlFor="shot_session_id" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              📋 Shot Session
            </label>
            <select
              id="shot_session_id"
              name="shot_session_id"
              value={formData.shot_session_id}
              onChange={handleInputChange}
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">No session (standalone shot)</option>
              {shotSessions.map((session) => (
                <option key={session.id} value={session.id}>
                  Session {session.id} - {session.title || 'Untitled'}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="recipe_id" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              📖 Recipe
            </label>
            <select
              id="recipe_id"
              name="recipe_id"
              value={formData.recipe_id}
              onChange={handleInputChange}
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Select a recipe</option>
              {recipes.map((recipe) => (
                <option key={recipe.id} value={recipe.id}>
                  {recipe.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Timestamp */}
        <div>
          <label htmlFor="timestamp" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            🕒 Shot Time
          </label>
          <DateTimeInput
            id="timestamp"
            name="timestamp"
            value={formData.timestamp}
            onChange={(value) => setFormData(prev => ({ ...prev, timestamp: value }))}
          />
        </div>

        {/* Notes */}
        <div>
          <label htmlFor="notes" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            📝 Notes
          </label>
          <textarea
            id="notes"
            name="notes"
            value={formData.notes}
            onChange={handleInputChange}
            rows="4"
            placeholder="Additional notes about this shot..."
            style={{ 
              width: '100%', 
              padding: '8px', 
              border: '1px solid #ddd', 
              borderRadius: '4px', 
              resize: 'vertical' 
            }}
          />
        </div>

        {/* Form Actions */}
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              style={{
                padding: '10px 20px',
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {ICONS.CANCEL} Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={loading}
            data-testid="submit-shot"
            style={{
              padding: '10px 20px',
              backgroundColor: loading ? '#6c757d' : '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Saving...' : (isEditMode ? `${ICONS.SAVE} Update Shot` : `${ICONS.SAVE} Create Shot`)}
          </button>
        </div>
      </form>
    </div>
  );
}

export default ShotForm;