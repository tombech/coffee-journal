import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link, useSearchParams } from 'react-router-dom';
import { useToast } from '../Toast';
import { apiFetch } from '../../config';
import { ICONS } from '../../config/icons';
import DateTimeInput from '../DateTimeInput';

function ShotForm({ product_batch_id = null, onShotSubmitted, initialData = null, onCancel }) {
  const navigate = useNavigate();
  const { id } = useParams();
  const [searchParams] = useSearchParams();
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
  const [currentSession, setCurrentSession] = useState(null);

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
        
        // Handle session_id URL parameter (e.g., /shots/new?session_id=5)
        const sessionIdParam = searchParams.get('session_id');
        if (sessionIdParam && !id && !initialData) {
          // First set the session ID
          setFormData(prev => ({
            ...prev,
            shot_session_id: sessionIdParam
          }));
          
          // Then pre-populate product and batch from session if available
          const sessionId = parseInt(sessionIdParam);
          const session = shotSessionsData.data ? 
            shotSessionsData.data.find(s => s.id === sessionId) :
            shotSessionsData.find(s => s.id === sessionId);
          
          if (session) {
            const sessionUpdates = {
              shot_session_id: sessionIdParam
            };
            
            // Pre-populate product from session
            if (session.product_id && !formData.product_id) {
              sessionUpdates.product_id = session.product_id;
              
              // Also pre-populate batch if session has one
              if (session.product_batch_id) {
                sessionUpdates.product_batch_id = session.product_batch_id;
                
                // Fetch batches for the product to ensure the batch dropdown is populated
                const batchesResponse = await apiFetch(`/products/${session.product_id}/batches`);
                if (batchesResponse.ok) {
                  setBatches(await batchesResponse.json());
                }
              }
            }
            
            setFormData(prev => ({
              ...prev,
              ...sessionUpdates
            }));
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
  }, [id, initialData, product_batch_id, searchParams]);

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

  // Track current session for breadcrumb and auto-populate equipment
  useEffect(() => {
    if (formData.shot_session_id && shotSessions.length > 0) {
      const session = shotSessions.find(s => s.id.toString() === formData.shot_session_id.toString());
      setCurrentSession(session || null);
      
      // Auto-populate equipment from session if fields are empty
      if (session && !isEditMode) {
        const equipmentFields = {
          brewer_id: session.brewer_id,
          grinder_id: session.grinder_id,
          portafilter_id: session.portafilter_id,
          basket_id: session.basket_id,
          scale_id: session.scale_id,
          recipe_id: session.recipe_id
        };
        
        // Only populate fields that are currently empty to avoid overriding user selections
        const updates = {};
        Object.entries(equipmentFields).forEach(([field, sessionValue]) => {
          if (sessionValue && (!formData[field] || formData[field] === '')) {
            updates[field] = sessionValue;
          }
        });
        
        if (Object.keys(updates).length > 0) {
          setFormData(prev => ({
            ...prev,
            ...updates
          }));
        }
      }
    } else {
      setCurrentSession(null);
    }
  }, [formData.shot_session_id, shotSessions, isEditMode]);

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
      } else {
        // Determine where to redirect based on origin
        const sessionIdParam = searchParams.get('session_id');
        
        if (sessionIdParam && !isEditMode) {
          // User came from a shot session page - redirect back to session
          navigate(`/shot-sessions/${sessionIdParam}`);
        } else if (formData.shot_session_id && !isEditMode) {
          // Shot is part of a session - redirect to session page
          navigate(`/shot-sessions/${formData.shot_session_id}`);
        } else if (!isEditMode) {
          // User came from "All shots" page or standalone - redirect to "All shots"
          navigate('/shots');
        } else {
          // Edit mode - stay on shot view page
          navigate(`/shots/${result.id}`);
        }
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
    <form 
      onSubmit={handleSubmit} 
      style={{ maxWidth: '1200px' }} 
      data-testid="shot-form"
    >
      <h4>{isEditMode ? 'Edit Shot' : 'Add New Shot'}</h4>
      
      {/* Session Context Breadcrumb */}
      {currentSession && (
        <div style={{
          marginBottom: '16px',
          padding: '8px 12px',
          backgroundColor: '#e9ecef',
          borderRadius: '4px',
          borderLeft: '4px solid #007bff',
          fontSize: '14px'
        }}>
          <span style={{ color: '#6c757d' }}>Part of session:</span>
          {' '}
          <Link 
            to={`/shot-sessions/${currentSession.id}`}
            style={{ 
              color: '#007bff', 
              textDecoration: 'none',
              fontWeight: 'bold'
            }}
          >
            ← {currentSession.title || `Session ${currentSession.id}`}
          </Link>
        </div>
      )}
      
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
            onChange={(value) => setFormData(prev => ({ ...prev, timestamp: value }))}
            required
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="product_id" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Product
          </label>
          <select
            id="product_id"
            name="product_id"
            value={formData.product_id}
            onChange={handleInputChange}
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
          <label htmlFor="product_batch_id" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Batch
          </label>
          <select
            id="product_batch_id"
            name="product_batch_id"
            value={formData.product_batch_id}
            onChange={handleInputChange}
            required
            disabled={!formData.product_id}
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          >
            <option value="">Select a batch</option>
            {batches.map((batch) => (
              <option key={batch.id} value={batch.id}>
                Batch #{batch.id} - {new Date(batch.roast_date).toLocaleDateString()}
              </option>
            ))}
          </select>
        </div>
        
        <div>
          <label htmlFor="shot_session_id" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Shot Session
          </label>
          <select
            id="shot_session_id"
            name="shot_session_id"
            value={formData.shot_session_id}
            onChange={handleInputChange}
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          >
            <option value="">No session (standalone)</option>
            {shotSessions.map((session) => (
              <option key={session.id} value={session.id}>
                Session {session.id} - {session.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Most Relevant Equipment Section */}
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
          <label htmlFor="brewer_id" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Brewer *
          </label>
          <select
            id="brewer_id"
            name="brewer_id"
            value={formData.brewer_id}
            onChange={handleInputChange}
            required
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          >
            <option value="">Select brewer</option>
            {brewers.map((brewer) => (
              <option key={brewer.id} value={brewer.id}>
                {brewer.name}
              </option>
            ))}
          </select>
        </div>
        
        <div>
          <label htmlFor="grinder_id" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Grinder
          </label>
          <select
            id="grinder_id"
            name="grinder_id"
            value={formData.grinder_id}
            onChange={handleInputChange}
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          >
            <option value="">Select grinder</option>
            {grinders.map((grinder) => (
              <option key={grinder.id} value={grinder.id}>
                {grinder.name}
              </option>
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
            onChange={handleInputChange}
            placeholder="e.g., 15, fine"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="portafilter_id" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Portafilter
          </label>
          <select
            id="portafilter_id"
            name="portafilter_id"
            value={formData.portafilter_id}
            onChange={handleInputChange}
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          >
            <option value="">Select portafilter</option>
            {portafilters.map((portafilter) => (
              <option key={portafilter.id} value={portafilter.id}>
                {portafilter.name}
              </option>
            ))}
          </select>
        </div>
        
        <div>
          <label htmlFor="basket_id" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Basket
          </label>
          <select
            id="basket_id"
            name="basket_id"
            value={formData.basket_id}
            onChange={handleInputChange}
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          >
            <option value="">Select basket</option>
            {baskets.map((basket) => (
              <option key={basket.id} value={basket.id}>
                {basket.name}
              </option>
            ))}
          </select>
        </div>
        
        <div>
          <label htmlFor="scale_id" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Scale
          </label>
          <select
            id="scale_id"
            name="scale_id"
            value={formData.scale_id}
            onChange={handleInputChange}
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          >
            <option value="">Select scale</option>
            {scales.map((scale) => (
              <option key={scale.id} value={scale.id}>
                {scale.name}
              </option>
            ))}
          </select>
        </div>
        
        <div>
          <label htmlFor="recipe_id" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Recipe
          </label>
          <select
            id="recipe_id"
            name="recipe_id"
            value={formData.recipe_id}
            onChange={handleInputChange}
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          >
            <option value="">Select recipe</option>
            {recipes.map((recipe) => (
              <option key={recipe.id} value={recipe.id}>
                {recipe.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Shot Parameters Section */}
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
          <label htmlFor="dose_grams" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Dose Grams *
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
            placeholder="18"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="yield_grams" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Yield Grams *
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
            placeholder="36"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="extraction_time_seconds" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Extraction Time
          </label>
          <input 
            type="number" 
            id="extraction_time_seconds"
            name="extraction_time_seconds" 
            value={formData.extraction_time_seconds} 
            onChange={handleInputChange} 
            min="0"
            placeholder="25"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="water_temperature_c" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Temperature
          </label>
          <input 
            type="number" 
            id="water_temperature_c"
            name="water_temperature_c" 
            value={formData.water_temperature_c} 
            onChange={handleInputChange} 
            step="0.1"
            min="0"
            max="100"
            placeholder="93"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="preinfusion_seconds" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Preinfusion
          </label>
          <input 
            type="number" 
            id="preinfusion_seconds"
            name="preinfusion_seconds" 
            value={formData.preinfusion_seconds} 
            onChange={handleInputChange} 
            min="0"
            step="0.1"
            placeholder="3"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="pressure_bars" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Pressure Bars
          </label>
          <input 
            type="number" 
            id="pressure_bars"
            name="pressure_bars" 
            value={formData.pressure_bars} 
            onChange={handleInputChange} 
            min="0"
            step="0.1"
            placeholder="9"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="extraction_status" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Status
          </label>
          <select
            id="extraction_status"
            name="extraction_status"
            value={formData.extraction_status}
            onChange={handleInputChange}
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          >
            <option value="">Select status</option>
            <option value="perfect">Perfect</option>
            <option value="channeling">Channeling</option>
            <option value="over-extracted">Over-extracted</option>
            <option value="under-extracted">Under-extracted</option>
          </select>
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
            onChange={handleInputChange} 
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
            onChange={handleInputChange} 
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
            onChange={handleInputChange} 
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
            onChange={handleInputChange} 
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
            onChange={handleInputChange} 
            min="0" 
            max="10" 
            step="0.5"
            placeholder="0-10"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="crema" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Crema
          </label>
          <input 
            type="number" 
            id="crema"
            name="crema" 
            value={formData.crema} 
            onChange={handleInputChange} 
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
            onChange={handleInputChange} 
            min="0" 
            max="10" 
            step="0.5"
            placeholder="0-10"
            style={{ width: '100%', fontSize: '14px', padding: '6px', height: '32px', boxSizing: 'border-box' }}
          />
        </div>
        
        <div>
          <label htmlFor="overall_score" style={{ fontSize: '12px', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>
            Overall Score
          </label>
          <input 
            type="number" 
            id="overall_score"
            name="overall_score" 
            value={formData.overall_score} 
            onChange={handleInputChange} 
            min="0" 
            max="10" 
            step="0.5"
            placeholder="0-10"
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
          onChange={handleInputChange} 
          rows="3"
          style={{ width: '100%', fontSize: '14px', padding: '8px', resize: 'vertical' }}
          placeholder="Shot observations, taste notes, adjustments for next time..."
        />
      </div>

      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
        <button 
          type="button" 
          disabled={loading}
          data-testid="submit-shot"
          aria-label={loading ? 'Saving...' : (isEditMode ? 'Update' : 'Create')}
          style={{ 
            padding: '10px 15px', 
            border: 'none', 
            background: 'none', 
            cursor: loading ? 'default' : 'pointer', 
            fontSize: '20px',
            opacity: loading ? 0.5 : 1
          }}
          title={loading ? 'Saving...' : (isEditMode ? 'Update Shot' : 'Create Shot')}
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
            onClick={onCancel || (() => navigate(`/shots/${id}`))} 
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

export default ShotForm;