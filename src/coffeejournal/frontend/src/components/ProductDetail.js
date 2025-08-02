import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import BatchForm from './BatchForm';
import BrewSessionTable from './BrewSessionTable';
import { useToast } from './Toast';
import { apiFetch } from '../config';
import { ICONS } from '../config/icons';
import StarRating from './StarRating';

function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [product, setProduct] = useState(null);
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showBatchForm, setShowBatchForm] = useState(false);
  const [editingBatch, setEditingBatch] = useState(null);
  const [brewSessions, setBrewSessions] = useState([]);

  useEffect(() => {
    fetchProductDetails();
    fetchBatches();
    fetchBrewSessions();
  }, [id]);

  const fetchProductDetails = async () => {
    setLoading(true);
    try {
      const response = await apiFetch(`/products/${id}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log('Product data received:', data);
      setProduct(data);
    } catch (err) {
      setError("Failed to fetch product details: " + err.message);
      console.error("Error fetching product details:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchBatches = async () => {
    console.log('DEBUG: fetchBatches called');
    try {
      // Add cache-busting timestamp
      const timestamp = new Date().getTime();
      const response = await apiFetch(`/products/${id}/batches?t=${timestamp}`, {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log('DEBUG: fetchBatches received data:', data);
      setBatches(data);
    } catch (err) {
      setError("Failed to fetch batches: " + err.message);
      console.error("Error fetching batches:", err);
    }
  };

  const fetchBrewSessions = async () => {
    try {
      const response = await apiFetch('/brew_sessions');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      // Filter sessions for this product
      const productSessions = data.filter(session => session.product_id === parseInt(id));
      setBrewSessions(productSessions);
    } catch (err) {
      console.error("Error fetching brew sessions:", err);
    }
  };


  const handleDeleteProduct = async () => {
    if (window.confirm("Are you sure you want to delete this product and all its batches?")) {
      try {
        const response = await apiFetch(`/products/${id}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        addToast("Product deleted successfully!", 'success');
        navigate('/products'); // Redirect to products list
      } catch (err) {
        setError("Failed to delete product: " + err.message);
        console.error("Error deleting product:", err);
      }
    }
  };

  const handleDeleteBatch = async (batchId) => {
    if (window.confirm("Are you sure you want to delete this batch?")) {
      try {
        const response = await apiFetch(`/batches/${batchId}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        addToast("Batch deleted successfully!", 'success');
        fetchBatches(); // Refresh batches list
      } catch (err) {
        setError("Failed to delete batch: " + err.message);
        console.error("Error deleting batch:", err);
      }
    }
  };

  const handleEditBatch = (batch) => {
    setEditingBatch(batch);
    setShowBatchForm(false); // Close add form if open
  };

  const handleBatchSubmitted = (newBatch) => {
    setShowBatchForm(false);
    setEditingBatch(null);
    fetchBatches(); // Refresh the batches list
    if (newBatch && newBatch.id) {
      // Navigate to the new batch detail page
      navigate(`/batches/${newBatch.id}`);
    }
  };

  const handleCancelBatchForm = () => {
    setShowBatchForm(false);
    setEditingBatch(null);
  };



  // Norwegian date formatting
  const formatDateNorwegian = (dateString) => {
    const date = new Date(dateString);
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear().toString().slice(-2);
    return `${day}.${month}.${year}`;
  };

  // Roast degree visualization
  const getRoastVisualization = (roastType) => {
    if (!roastType) return '☕☕☕☕☕'; // Default light outline
    
    const normalizedValue = Math.max(1, Math.min(10, roastType)); // Clamp between 1-10
    const filledBeans = Math.ceil(normalizedValue / 2); // Each bean represents 2 levels
    const darkBeans = Math.floor(normalizedValue / 2); // How many should be dark
    
    let visualization = '';
    for (let i = 0; i < 5; i++) {
      if (i < darkBeans) {
        visualization += '🫘'; // Dark roasted bean
      } else if (i < filledBeans) {
        visualization += '🤎'; // Medium/light roasted bean
      } else {
        visualization += '☕'; // Bean outline
      }
    }
    return visualization;
  };

  // Calculate comprehensive score for brew sessions
  const calculateBrewScore = (session) => {
    // Use overall score if available
    if (session.score && session.score > 0) {
      return session.score;
    }
    
    // Otherwise calculate from tasting notes (bitterness is negative, others positive)
    const tastingNotes = [
      session.sweetness,
      session.acidity,
      session.body,
      session.aroma,
      session.flavor_profile_match
    ].filter(score => score && score > 0);
    
    // Bitterness is subtracted (inverted)
    const bitternessScore = session.bitterness ? (10 - session.bitterness) : 0;
    if (bitternessScore > 0) tastingNotes.push(bitternessScore);
    
    return tastingNotes.length > 0 ? tastingNotes.reduce((sum, score) => sum + score, 0) / tastingNotes.length : 0;
  };

  // Get top 5 brew sessions
  const getTopBrewSessions = () => {
    return brewSessions
      .map(session => ({
        ...session,
        calculatedScore: calculateBrewScore(session)
      }))
      .filter(session => session.calculatedScore > 0)
      .sort((a, b) => b.calculatedScore - a.calculatedScore)
      .slice(0, 5);
  };

  // Get bottom 5 brew sessions
  const getBottomBrewSessions = () => {
    return brewSessions
      .map(session => ({
        ...session,
        calculatedScore: calculateBrewScore(session)
      }))
      .filter(session => session.calculatedScore > 0)
      .sort((a, b) => a.calculatedScore - b.calculatedScore)
      .slice(0, 5);
  };

  // Format seconds to minutes:seconds
  const formatSecondsToMinSec = (seconds) => {
    if (!seconds) return 'N/A';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes > 0) {
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    return `${seconds}s`;
  };


  // Calculate average tasting notes for radar chart
  const getTastingAverages = () => {
    if (brewSessions.length === 0) return null;
    
    const validSessions = brewSessions.filter(session => 
      session.sweetness || session.acidity || session.bitterness || session.body || session.aroma
    );
    
    if (validSessions.length === 0) return null;
    
    const totals = {
      sweetness: 0,
      acidity: 0,
      bitterness: 0,
      body: 0,
      aroma: 0
    };
    
    const counts = {
      sweetness: 0,
      acidity: 0,
      bitterness: 0,
      body: 0,
      aroma: 0
    };
    
    validSessions.forEach(session => {
      ['sweetness', 'acidity', 'bitterness', 'body', 'aroma'].forEach(attribute => {
        if (session[attribute] && session[attribute] > 0) {
          totals[attribute] += session[attribute];
          counts[attribute]++;
        }
      });
    });
    
    return {
      sweetness: counts.sweetness > 0 ? totals.sweetness / counts.sweetness : 0,
      acidity: counts.acidity > 0 ? totals.acidity / counts.acidity : 0,
      bitterness: counts.bitterness > 0 ? totals.bitterness / counts.bitterness : 0,
      body: counts.body > 0 ? totals.body / counts.body : 0,
      aroma: counts.aroma > 0 ? totals.aroma / counts.aroma : 0,
      sessionCount: validSessions.length
    };
  };

  // Radar Chart Component
  const RadarChart = ({ data }) => {
    if (!data) return null;
    
    const size = 200;
    const center = size / 2;
    const maxRadius = 80;
    const angles = [0, 72, 144, 216, 288]; // 5 points, 72 degrees apart
    const labels = ['Sweetness', 'Acidity', 'Body', 'Aroma', 'Bitterness'];
    const values = [data.sweetness, data.acidity, data.body, data.aroma, data.bitterness];
    
    // Convert polar coordinates to cartesian
    const getPoint = (angle, radius) => {
      const radians = (angle - 90) * Math.PI / 180; // -90 to start at top
      return {
        x: center + radius * Math.cos(radians),
        y: center + radius * Math.sin(radians)
      };
    };
    
    // Generate grid circles
    const gridCircles = [2, 4, 6, 8, 10].map(level => (
      <circle
        key={level}
        cx={center}
        cy={center}
        r={(level / 10) * maxRadius}
        fill="none"
        stroke="#e0e0e0"
        strokeWidth="1"
      />
    ));
    
    // Generate axis lines
    const axisLines = angles.map((angle, index) => {
      const point = getPoint(angle, maxRadius);
      return (
        <line
          key={index}
          x1={center}
          y1={center}
          x2={point.x}
          y2={point.y}
          stroke="#e0e0e0"
          strokeWidth="1"
        />
      );
    });
    
    // Generate data polygon
    const dataPoints = values.map((value, index) => {
      const radius = (value / 10) * maxRadius;
      return getPoint(angles[index], radius);
    });
    
    const polygonPoints = dataPoints.map(point => `${point.x},${point.y}`).join(' ');
    
    // Generate labels
    const labelElements = labels.map((label, index) => {
      const point = getPoint(angles[index], maxRadius + 20);
      return (
        <text
          key={index}
          x={point.x}
          y={point.y}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="11"
          fill="#666"
        >
          {label}
        </text>
      );
    });
    
    return (
      <div style={{ textAlign: 'center' }}>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '14px' }}>
          Tasting Profile ({data.sessionCount} sessions)
        </h4>
        <svg width={size + 40} height={size + 40} viewBox={`0 0 ${size + 40} ${size + 40}`}>
          <g transform="translate(20, 20)">
            {gridCircles}
            {axisLines}
            <polygon
              points={polygonPoints}
              fill="rgba(54, 162, 235, 0.2)"
              stroke="rgba(54, 162, 235, 0.8)"
              strokeWidth="2"
            />
            {dataPoints.map((point, index) => (
              <circle
                key={index}
                cx={point.x}
                cy={point.y}
                r="3"
                fill="rgba(54, 162, 235, 0.8)"
              />
            ))}
            {labelElements}
          </g>
        </svg>
      </div>
    );
  };

  console.log('Render state:', { loading, error, product });
  
  if (loading) return <p className="loading-message">Loading product details...</p>;
  if (error) return <p className="error-message">{error}</p>;
  if (!product) return <p>Product not found.</p>;

  return (
    <div>
      <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <h2 style={{ margin: 0, marginRight: 'auto' }} id="product-title">{product.product_name}</h2>
        <button 
          onClick={() => navigate(`/products/edit/${product.id}`)}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px',
            marginRight: '5px'
          }}
          title="Edit Product"
          aria-label="Edit Product"
        >
          {ICONS.EDIT}
        </button>
        <button 
          onClick={() => handleDeleteProduct()}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px'
          }}
          title="Delete Product"
          aria-label="Delete Product"
        >
          {ICONS.DELETE}
        </button>
      </div>

      {/* Product Details */}
      <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 15px', alignItems: 'start' }}>
          <strong>Roaster:</strong>
          <span>{product.roaster?.name || '-'}</span>
          
          <strong>Bean Type:</strong>
          <span>{product.bean_type?.map(bt => bt.name).join(', ') || '-'}</span>
          
          <strong>Country:</strong>
          <span data-testid="product-country">{product.country?.name || '-'}</span>
          
          <strong>Region:</strong>
          <span>{product.region?.map(r => r.name).join(', ') || '-'}</span>
          
          <strong>Bean Process:</strong>
          <span>{product.bean_process || '-'}</span>
          
          <strong>Product Name:</strong>
          <span>{product.product_name || '-'}</span>
          
          <strong>Roast Type:</strong>
          <span>{product.roast_type ? `${getRoastVisualization(product.roast_type)} (${product.roast_type})` : '-'}</span>
          
          <strong>Decaffeinated:</strong>
          <span>
            {product.decaf ? (
              <span style={{ color: '#1976d2', fontWeight: 'bold' }}>
                Yes {product.decaf_method && `(${product.decaf_method.name})`}
              </span>
            ) : 'No'}
          </span>
          
          <strong>Rating:</strong>
          <span>
            {product.rating ? (
              <StarRating rating={product.rating} readOnly={true} maxRating={5} />
            ) : '-'}
          </span>
          
          <strong>Description:</strong>
          <span>{product.description || '-'}</span>
          
          <strong>Notes:</strong>
          <span style={{ whiteSpace: 'pre-wrap' }}>{product.notes || '-'}</span>
          
          <strong>Product URL:</strong>
          <span>
            {product.url ? (
              <a href={product.url} target="_blank" rel="noopener noreferrer">{product.url}</a>
            ) : '-'}
          </span>
          
          <strong>Image:</strong>
          <span>
            {product.image_url ? (
              <img src={product.image_url} alt={product.bean_type?.map(bt => bt.name).join(', ') || 'Coffee'} style={{ maxWidth: '200px', borderRadius: '8px' }} />
            ) : '-'}
          </span>
        </div>
      </div>

      <div className="detail-section">
        <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h3 style={{ margin: 0, marginRight: 'auto' }}>Batches for this Product</h3>
          <button 
            onClick={() => setShowBatchForm(!showBatchForm)}
            data-testid={showBatchForm ? 'cancel-batch-form' : 'add-batch-button'}
            aria-label={showBatchForm ? 'Cancel adding batch' : 'Add new batch'}
            style={{ 
              padding: '8px 16px',
              backgroundColor: showBatchForm ? '#6c757d' : '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
            title={showBatchForm ? 'Cancel' : 'Add New Batch'}
            aria-label={showBatchForm ? 'Cancel' : 'Add New Batch'}
          >
            {showBatchForm ? ICONS.CANCEL : ICONS.CREATE}
          </button>
        </div>
        {batches.length === 0 ? (
          <p>No batches registered for this product.</p>
        ) : (
          <div className="batch-list">
            {batches.map(batch => (
              <div key={batch.id} style={{ 
                marginBottom: '20px', 
                padding: '15px', 
                border: '1px solid #ddd', 
                borderRadius: '8px', 
                backgroundColor: '#fafafa' 
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <h4 style={{ margin: 0 }}>
                    <Link to={`/batches/${batch.id}`} style={{ textDecoration: 'none', color: 'inherit', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {ICONS.VIEW} Batch #{batch.id}
                    </Link>
                  </h4>
                  <div>
                    <button 
                      onClick={() => handleEditBatch(batch)}
                      style={{ 
                        padding: '4px 6px', 
                        border: 'none', 
                        background: 'none', 
                        cursor: 'pointer', 
                        fontSize: '14px',
                        marginRight: '5px'
                      }}
                      title="Edit Batch"
                      aria-label="Edit Batch"
                    >
                      {ICONS.EDIT}
                    </button>
                    <button 
                      onClick={() => handleDeleteBatch(batch.id)}
                      style={{ 
                        padding: '4px 6px', 
                        border: 'none', 
                        background: 'none', 
                        cursor: 'pointer', 
                        fontSize: '14px'
                      }}
                      title="Delete Batch"
                      aria-label="Delete Batch"
                    >
                      {ICONS.DELETE}
                    </button>
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 15px', alignItems: 'start' }}>
                  <strong>Roast Date:</strong>
                  <span>{batch.roast_date ? formatDateNorwegian(batch.roast_date) : 'Unknown'}</span>
                  
                  <strong>Purchase Date:</strong>
                  <span>{batch.purchase_date ? formatDateNorwegian(batch.purchase_date) : '-'}</span>
                  
                  <strong>Amount:</strong>
                  <span>{batch.amount_grams ? `${batch.amount_grams}g` : '-'}</span>
                  
                  <strong>Price:</strong>
                  <span>{batch.price != null && !isNaN(batch.price) ? `${Number(batch.price).toFixed(2)} kr` : '-'}</span>
                  
                  <strong>Price per Cup:</strong>
                  <span>{batch.price_per_cup != null && !isNaN(batch.price_per_cup) ? `${Number(batch.price_per_cup).toFixed(2)} kr` : '-'}</span>
                  
                  <strong>Seller:</strong>
                  <span>{batch.seller || '-'}</span>
                  
                  <strong>Rating:</strong>
                  <span>
                    {batch.rating ? (
                      <StarRating rating={batch.rating} readOnly={true} maxRating={5} />
                    ) : '-'}
                  </span>
                  
                  <strong>Notes:</strong>
                  <span>{batch.notes || '-'}</span>
                </div>
              </div>
            ))}
          </div>
        )}
        {showBatchForm && (
          <BatchForm 
            productId={id}
            onBatchSubmitted={handleBatchSubmitted}
            onCancel={handleCancelBatchForm}
          />
        )}
        
        {editingBatch && (
          <BatchForm 
            productId={id}
            initialData={editingBatch}
            onBatchSubmitted={handleBatchSubmitted}
            onCancel={handleCancelBatchForm}
          />
        )}
      </div>

      {/* Brew Analytics Section */}
      {brewSessions.length > 0 && (
        <div style={{ marginTop: '40px' }}>
          {/* Top 5 Brews */}
          <BrewSessionTable 
            sessions={getTopBrewSessions()} 
            title="🏆 Top 5 Brews"
            showProduct={false}
            showActions={false}
            showFilters={false}
            showAddButton={false}
            preserveOrder={true}
            onDelete={() => {}}
            onDuplicate={() => {}}
            onEdit={() => {}}
          />

          {/* Bottom 5 Brews */}
          <BrewSessionTable 
            sessions={getBottomBrewSessions()} 
            title="💩 Bottom 5 Brews"
            showProduct={false}
            showActions={false}
            showFilters={false}
            showAddButton={false}
            preserveOrder={true}
            onDelete={() => {}}
            onDuplicate={() => {}}
            onEdit={() => {}}
          />

          {/* Radar Chart */}
          <div style={{ 
            padding: '20px', 
            borderRadius: '8px',
            border: '1px solid #ddd',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            marginBottom: '30px'
          }}>
            <h3 style={{ margin: '0 0 15px 0', textAlign: 'center' }}>📊 Flavor Profile</h3>
            {getTastingAverages() ? (
              <RadarChart data={getTastingAverages()} />
            ) : (
              <p style={{ color: '#666', fontStyle: 'italic', textAlign: 'center' }}>
                No tasting notes recorded yet
              </p>
            )}
          </div>
        </div>
      )}

    </div>
  );
}

export default ProductDetail;