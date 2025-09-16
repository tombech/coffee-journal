import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import BatchForm from './BatchForm';
import BrewSessionTable from './BrewSessionTable';
import ShotTable from './shots/ShotTable';
import ShotSessionTable from './shotSessions/ShotSessionTable';
import BrewRecommendations from './BrewRecommendations';
import { useToast } from './Toast';
import { apiFetch } from '../config';
import { ICONS } from '../config/icons';
import StarRating from './StarRating';
import UsageStatistics from './UsageStatistics';

function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [product, setProduct] = useState(null);
  const [batches, setBatches] = useState([]);
  const [batchStats, setBatchStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showBatchForm, setShowBatchForm] = useState(false);
  const [editingBatch, setEditingBatch] = useState(null);
  const [brewSessions, setBrewSessions] = useState([]);
  const [topBrewSessions, setTopBrewSessions] = useState([]);
  const [bottomBrewSessions, setBottomBrewSessions] = useState([]);
  const [recentBrewSessions, setRecentBrewSessions] = useState([]);
  const [shots, setShots] = useState([]);
  const [topShots, setTopShots] = useState([]);
  const [bottomShots, setBottomShots] = useState([]);
  const [recentShots, setRecentShots] = useState([]);
  const [shotSessions, setShotSessions] = useState([]);
  const [topShotSessions, setTopShotSessions] = useState([]);
  const [bottomShotSessions, setBottomShotSessions] = useState([]);
  const [recentShotSessions, setRecentShotSessions] = useState([]);
  const [productStats, setProductStats] = useState(null);

  useEffect(() => {
    fetchProductDetails();
    fetchBatches();
    fetchBrewSessions();
    fetchShots();
    fetchShotSessions();
    fetchProductStats();
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

      // Fetch stats for each batch
      await fetchBatchStats(data);
    } catch (err) {
      setError("Failed to fetch batches: " + err.message);
      console.error("Error fetching batches:", err);
    }
  };

  const fetchBatchStats = async (batchList) => {
    try {
      // Fetch stats for all batches in parallel
      const statsPromises = batchList.map(async (batch) => {
        try {
          const response = await apiFetch(`/stats/batches/${batch.id}`);
          if (response.ok) {
            const stats = await response.json();
            return { batchId: batch.id, stats };
          }
        } catch (err) {
          console.warn(`Failed to fetch stats for batch ${batch.id}:`, err);
        }
        return { batchId: batch.id, stats: null };
      });

      const results = await Promise.all(statsPromises);

      // Convert to object with batch ID as key
      const statsMap = {};
      results.forEach(({ batchId, stats }) => {
        statsMap[batchId] = stats;
      });

      setBatchStats(statsMap);
    } catch (err) {
      console.warn('Failed to fetch batch stats:', err);
    }
  };

  const fetchBrewSessions = async () => {
    try {
      // Fetch recent sessions, top sessions, and bottom sessions efficiently
      const [recentResponse, topResponse, bottomResponse, recentForStatsResponse] = await Promise.all([
        apiFetch(`/brew_sessions?product_id=${id}&page_size=20&sort=timestamp&sort_direction=desc`), // Recent sessions for main display
        apiFetch(`/brew_sessions?product_id=${id}&page_size=5&sort=score&sort_direction=desc`), // Top 5 by score
        apiFetch(`/brew_sessions?product_id=${id}&page_size=5&sort=score&sort_direction=asc`), // Bottom 5 by score
        apiFetch(`/brew_sessions?product_id=${id}&page_size=5&sort=timestamp&sort_direction=desc`) // Recent 5 for stats
      ]);
      
      if (!recentResponse.ok || !topResponse.ok || !bottomResponse.ok || !recentForStatsResponse.ok) {
        throw new Error('Failed to fetch brew sessions');
      }
      
      const [recentResult, topResult, bottomResult, recentForStatsResult] = await Promise.all([
        recentResponse.json(),
        topResponse.json(),
        bottomResponse.json(),
        recentForStatsResponse.json()
      ]);
      
      setBrewSessions(recentResult.data || []);
      setTopBrewSessions(topResult.data || []);
      setBottomBrewSessions(bottomResult.data || []);
      setRecentBrewSessions(recentForStatsResult.data || []);
    } catch (err) {
      console.error("Error fetching brew sessions:", err);
    }
  };

  const fetchShots = async () => {
    try {
      // Get product_id from shots through their batches
      const [recentResponse, topResponse, bottomResponse] = await Promise.all([
        apiFetch(`/shots?product_id=${id}&page_size=20&sort=timestamp&sort_direction=desc`),
        apiFetch(`/shots?product_id=${id}&page_size=5&sort=calculated_score&sort_direction=desc`),
        apiFetch(`/shots?product_id=${id}&page_size=5&sort=calculated_score&sort_direction=asc`)
      ]);
      
      if (recentResponse.ok && topResponse.ok && bottomResponse.ok) {
        const [recentResult, topResult, bottomResult] = await Promise.all([
          recentResponse.json(),
          topResponse.json(),
          bottomResponse.json()
        ]);
        
        setShots(recentResult.data || []);
        setTopShots(topResult.data || []);
        setBottomShots(bottomResult.data || []);
        setRecentShots(recentResult.data?.slice(0, 5) || []);
      }
    } catch (err) {
      console.error("Error fetching shots:", err);
    }
  };

  const fetchShotSessions = async () => {
    try {
      const [recentResponse, topResponse, bottomResponse] = await Promise.all([
        apiFetch(`/shot_sessions?product_id=${id}&page_size=20&sort=created_at&sort_direction=desc`),
        apiFetch(`/shot_sessions?product_id=${id}&page_size=5&sort=created_at&sort_direction=desc`),
        apiFetch(`/shot_sessions?product_id=${id}&page_size=5&sort=created_at&sort_direction=asc`)
      ]);
      
      if (recentResponse.ok && topResponse.ok && bottomResponse.ok) {
        const [recentResult, topResult, bottomResult] = await Promise.all([
          recentResponse.json(),
          topResponse.json(),
          bottomResponse.json()
        ]);
        
        setShotSessions(recentResult.data || []);
        setTopShotSessions(topResult.data || []);
        setBottomShotSessions(bottomResult.data || []);
        setRecentShotSessions(recentResult.data?.slice(0, 5) || []);
      }
    } catch (err) {
      console.error("Error fetching shot sessions:", err);
    }
  };

  const fetchProductStats = async () => {
    try {
      const response = await apiFetch(`/stats/products/${id}`);
      if (response.ok) {
        const stats = await response.json();
        setProductStats(stats);
      }
    } catch (err) {
      console.error("Error fetching product stats:", err);
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

  // Roast degree visualization using custom PNG images with half-filled beans
  const getRoastVisualization = (roastType) => {
    if (!roastType) {
      // Default - all white/light beans
      return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '2px' }}>
          {[...Array(5)].map((_, i) => (
            <img 
              key={i}
              src="/coffee-bean-white.png" 
              alt="Light roast bean" 
              style={{ width: '16px', height: '16px' }}
            />
          ))}
        </span>
      );
    }
    
    const normalizedValue = Math.max(1, Math.min(10, roastType)); // Clamp between 1-10
    const scaledValue = normalizedValue / 2; // Convert to 0.5-5.0 scale
    
    const beans = [];
    for (let i = 0; i < 5; i++) {
      const beanValue = scaledValue - i; // How much this bean should be filled
      
      if (beanValue >= 1) {
        // Full bean - completely brown
        beans.push(
          <img 
            key={i}
            src="/coffee-bean-brown.png" 
            alt="Dark roast bean" 
            style={{ width: '16px', height: '16px' }}
          />
        );
      } else if (beanValue > 0) {
        // Partial bean - brown overlaid on white with clip-path
        const fillPercentage = Math.round(beanValue * 100);
        beans.push(
          <div 
            key={i}
            style={{ 
              position: 'relative', 
              width: '16px', 
              height: '16px',
              display: 'inline-block'
            }}
          >
            {/* White base bean */}
            <img 
              src="/coffee-bean-white.png" 
              alt={`${fillPercentage}% roasted bean`}
              style={{ 
                width: '16px', 
                height: '16px',
                position: 'absolute',
                top: 0,
                left: 0
              }}
            />
            {/* Brown overlay clipped to percentage */}
            <img 
              src="/coffee-bean-brown.png" 
              alt=""
              style={{ 
                width: '16px', 
                height: '16px',
                position: 'absolute',
                top: 0,
                left: 0,
                clipPath: `inset(0 ${100 - fillPercentage}% 0 0)`
              }}
            />
          </div>
        );
      } else {
        // Empty bean - white only
        beans.push(
          <img 
            key={i}
            src="/coffee-bean-white.png" 
            alt="Light roast bean" 
            style={{ width: '16px', height: '16px' }}
          />
        );
      }
    }
    
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '2px' }}>
        {beans}
      </span>
    );
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
    
    const size = 400;
    const center = size / 2;
    const maxRadius = 160;
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
      const point = getPoint(angles[index], maxRadius + 40);
      return (
        <text
          key={index}
          x={point.x}
          y={point.y}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="14"
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
        <svg 
          width={size + 80} 
          height={size + 80} 
          viewBox={`0 0 ${size + 80} ${size + 80}`}
          style={{ 
            minWidth: `${size + 80}px`, 
            minHeight: `${size + 80}px`,
            maxWidth: 'none'
          }}
        >
          <g transform="translate(40, 40)">
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

      {/* Top Section: Product Details and Flavor Profile */}
      <div style={{ marginBottom: '30px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Product Details - Left Side */}
        <div style={{ 
          padding: '20px', 
          backgroundColor: 'white',
          borderRadius: '12px',
          border: '1px solid #e0e0e0',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ margin: '0 0 20px 0', color: '#333', fontSize: '18px', fontWeight: 'bold' }}>
            ☕ Product Information
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '12px 20px', alignItems: 'start' }}>
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
          <span>
            {product.roast_type ? (
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {getRoastVisualization(product.roast_type)}
                <span>({product.roast_type})</span>
              </span>
            ) : '-'}
          </span>
          
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

        {/* Flavor Profile - Right Side */}
        <div style={{ 
          padding: '20px', 
          backgroundColor: 'white',
          borderRadius: '12px',
          border: '1px solid #e0e0e0',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          minWidth: '520px'  // Ensure container is wide enough for the larger chart
        }}>
          <h3 style={{ margin: '0 0 20px 0', color: '#333', fontSize: '18px', fontWeight: 'bold' }}>
            📊 Flavor Profile
          </h3>
          {getTastingAverages() ? (
            <RadarChart data={getTastingAverages()} />
          ) : (
            <p style={{ color: '#666', fontStyle: 'italic', textAlign: 'center' }}>
              No tasting notes recorded yet
            </p>
          )}
        </div>
      </div>

      {/* Product Statistics and Brew Sessions Section */}
      <UsageStatistics 
        statsData={{
          ...productStats,
          top_5_sessions: topBrewSessions,
          bottom_5_sessions: bottomBrewSessions,
          recent_5_sessions: recentBrewSessions
        }}
        itemName="product"
        showProduct={false}
        customStatistics={productStats && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px', marginBottom: '20px' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2e7d32' }}>{productStats.total_brew_sessions}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>Total Brew Sessions</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#e65100' }}>{shots.length}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>Total Shots</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#3f51b5' }}>{shotSessions.length}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>Total Shot Sessions</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1976d2' }}>{productStats.total_batches}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>Total Batches</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ff9800' }}>{productStats.average_score}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>Average Score</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#9c27b0' }}>
                {productStats.score_range.min} - {productStats.score_range.max}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Score Range</div>
            </div>
          </div>
        )}
      />

      {/* Shots Section */}
      {(shots.length > 0 || topShots.length > 0 || bottomShots.length > 0) && (
        <div style={{ 
          marginBottom: '30px',
          padding: '20px', 
          backgroundColor: 'white',
          borderRadius: '12px',
          border: '1px solid #e0e0e0',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ margin: '0 0 20px 0', color: '#333', fontSize: '18px', fontWeight: 'bold' }}>
            ☕ Shot Statistics
          </h3>
          
          {/* Top 5 Shots */}
          {topShots.length > 0 && (
            <div style={{ marginBottom: '25px' }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#2e7d32', fontSize: '16px' }}>🏆 Top 5 Shots</h4>
              <ShotTable 
                shots={topShots}
                showActions={false}
                showFilters={false}
                showAddButton={false}
                showProduct={false}
                preserveOrder={true}
                onDelete={() => {}}
                onDuplicate={() => {}}
                onEdit={() => {}}
              />
            </div>
          )}
          
          {/* Bottom 5 Shots */}
          {bottomShots.length > 0 && (
            <div style={{ marginBottom: '25px' }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#f44336', fontSize: '16px' }}>📉 Bottom 5 Shots</h4>
              <ShotTable 
                shots={bottomShots}
                showActions={false}
                showFilters={false}
                showAddButton={false}
                showProduct={false}
                preserveOrder={true}
                onDelete={() => {}}
                onDuplicate={() => {}}
                onEdit={() => {}}
              />
            </div>
          )}
          
          {/* Recent 5 Shots */}
          {recentShots.length > 0 && (
            <div>
              <h4 style={{ margin: '0 0 10px 0', color: '#1976d2', fontSize: '16px' }}>🕐 Recent 5 Shots</h4>
              <ShotTable 
                shots={recentShots}
                showActions={false}
                showFilters={false}
                showAddButton={false}
                showProduct={false}
                preserveOrder={true}
                onDelete={() => {}}
                onDuplicate={() => {}}
                onEdit={() => {}}
              />
            </div>
          )}
        </div>
      )}

      {/* Shot Sessions Section */}
      {(shotSessions.length > 0 || topShotSessions.length > 0 || bottomShotSessions.length > 0) && (
        <div style={{ 
          marginBottom: '30px',
          padding: '20px', 
          backgroundColor: 'white',
          borderRadius: '12px',
          border: '1px solid #e0e0e0',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ margin: '0 0 20px 0', color: '#333', fontSize: '18px', fontWeight: 'bold' }}>
            ☕ Shot Session Statistics
          </h3>
          
          {/* Recent Shot Sessions */}
          {recentShotSessions.length > 0 && (
            <div>
              <h4 style={{ margin: '0 0 10px 0', color: '#1976d2', fontSize: '16px' }}>🕐 Recent Shot Sessions</h4>
              <ShotSessionTable 
                shotSessions={recentShotSessions}
                pagination={null}
                showMobileSearch={false}
                onDelete={() => {}}
                onDuplicate={() => {}}
                onEdit={() => {}}
                filters={{}}
                onFiltersChange={() => {}}
              />
            </div>
          )}
        </div>
      )}

      {/* Batches Section */}
      <div style={{ 
        marginBottom: '30px',
        padding: '20px', 
        backgroundColor: 'white',
        borderRadius: '12px',
        border: '1px solid #e0e0e0',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <div style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h3 style={{ margin: 0, marginRight: 'auto', color: '#333', fontSize: '18px', fontWeight: 'bold' }}>
            📦 Batches for this Product
          </h3>
          <button 
            onClick={() => setShowBatchForm(!showBatchForm)}
            data-testid={showBatchForm ? 'cancel-batch-form' : 'add-batch-button'}
            title={showBatchForm ? 'Cancel' : 'Add New Batch'}
            aria-label={showBatchForm ? 'Cancel' : 'Add New Batch'}
            style={{ 
              padding: '6px 8px',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            {showBatchForm ? ICONS.CANCEL : ICONS.CREATE}
          </button>
        </div>
        {batches.length === 0 ? (
          <p>No batches registered for this product.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ 
              width: '100%', 
              borderCollapse: 'collapse', 
              marginTop: '10px',
              backgroundColor: 'white',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}>
              <thead>
                <tr style={{ backgroundColor: '#f5f5f5' }}>
                  <th style={{ 
                    padding: '12px 8px', 
                    textAlign: 'left', 
                    borderBottom: '2px solid #ddd',
                    fontWeight: 'bold'
                  }}>Actions</th>
                  <th style={{ 
                    padding: '12px 8px', 
                    textAlign: 'left', 
                    borderBottom: '2px solid #ddd',
                    fontWeight: 'bold'
                  }}>Batch #</th>
                  <th style={{ 
                    padding: '12px 8px', 
                    textAlign: 'left', 
                    borderBottom: '2px solid #ddd',
                    fontWeight: 'bold'
                  }}>Status</th>
                  <th style={{ 
                    padding: '12px 8px', 
                    textAlign: 'left', 
                    borderBottom: '2px solid #ddd',
                    fontWeight: 'bold'
                  }}>Roast Date</th>
                  <th style={{ 
                    padding: '12px 8px', 
                    textAlign: 'left', 
                    borderBottom: '2px solid #ddd',
                    fontWeight: 'bold'
                  }}>Purchase Date</th>
                  <th style={{ 
                    padding: '12px 8px', 
                    textAlign: 'left', 
                    borderBottom: '2px solid #ddd',
                    fontWeight: 'bold'
                  }}>Amount</th>
                  <th style={{ 
                    padding: '12px 8px', 
                    textAlign: 'left', 
                    borderBottom: '2px solid #ddd',
                    fontWeight: 'bold'
                  }}>Price</th>
                  <th style={{ 
                    padding: '12px 8px', 
                    textAlign: 'left', 
                    borderBottom: '2px solid #ddd',
                    fontWeight: 'bold'
                  }}>Price/Cup</th>
                  <th style={{
                    padding: '12px 8px',
                    textAlign: 'left',
                    borderBottom: '2px solid #ddd',
                    fontWeight: 'bold'
                  }}>Rating</th>
                  <th style={{
                    padding: '12px 8px',
                    textAlign: 'left',
                    borderBottom: '2px solid #ddd',
                    fontWeight: 'bold'
                  }}>Total Uses</th>
                  <th style={{
                    padding: '12px 8px',
                    textAlign: 'left',
                    borderBottom: '2px solid #ddd',
                    fontWeight: 'bold'
                  }}>Usage</th>
                  <th style={{
                    padding: '12px 8px',
                    textAlign: 'left',
                    borderBottom: '2px solid #ddd',
                    fontWeight: 'bold'
                  }}>Uses Left</th>
                  <th style={{
                    padding: '12px 8px',
                    textAlign: 'left',
                    borderBottom: '2px solid #ddd',
                    fontWeight: 'bold'
                  }}>Avg Score</th>
                  <th style={{
                    padding: '12px 8px',
                    textAlign: 'left',
                    borderBottom: '2px solid #ddd',
                    fontWeight: 'bold'
                  }}>Seller</th>
                  <th style={{
                    padding: '12px 8px',
                    textAlign: 'left',
                    borderBottom: '2px solid #ddd',
                    fontWeight: 'bold'
                  }}>Notes</th>
                </tr>
              </thead>
              <tbody>
                {batches.map((batch, index) => (
                  <tr key={batch.id} style={{ 
                    backgroundColor: index % 2 === 0 ? 'white' : '#fafafa',
                    borderBottom: '1px solid #eee'
                  }}>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        <button 
                          onClick={() => navigate(`/batches/${batch.id}`)}
                          style={{ 
                            padding: '4px 6px', 
                            border: 'none', 
                            background: 'none', 
                            cursor: 'pointer', 
                            fontSize: '14px'
                          }}
                          title="View Batch"
                          aria-label="View Batch"
                        >
                          {ICONS.VIEW}
                        </button>
                        <button 
                          onClick={() => handleEditBatch(batch)}
                          style={{ 
                            padding: '4px 6px', 
                            border: 'none', 
                            background: 'none', 
                            cursor: 'pointer', 
                            fontSize: '14px'
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
                    </td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee', fontWeight: 'bold' }}>
                      #{batch.id}
                    </td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                      <span style={{ 
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        backgroundColor: batch.is_active !== false ? '#e8f5e8' : '#ffebee',
                        color: batch.is_active !== false ? '#2e7d32' : '#c62828'
                      }}>
                        {batch.is_active !== false ? '✓ Active' : '✗ Inactive'}
                      </span>
                    </td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                      {batch.roast_date ? formatDateNorwegian(batch.roast_date) : '-'}
                    </td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                      {batch.purchase_date ? formatDateNorwegian(batch.purchase_date) : '-'}
                    </td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                      {batch.amount_grams ? `${Math.round(batch.amount_grams)}g` : '-'}
                    </td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                      {batch.price != null && !isNaN(batch.price) ? `${Math.round(Number(batch.price))} kr` : '-'}
                    </td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                      {batch.price_per_cup != null && !isNaN(batch.price_per_cup) ? `${Math.round(Number(batch.price_per_cup))} kr` : '-'}
                    </td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                      {batch.rating ? (
                        <StarRating rating={batch.rating} readOnly={true} maxRating={5} />
                      ) : '-'}
                    </td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                      {batchStats[batch.id] ? (
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          fontWeight: 'bold',
                          backgroundColor: '#e3f2fd',
                          color: '#1976d2'
                        }}>
                          {(batchStats[batch.id].total_brew_sessions || 0) + (batchStats[batch.id].total_shots || 0)} uses
                        </span>
                      ) : '-'}
                    </td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                      {batchStats[batch.id] ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          <div style={{ fontSize: '12px', color: '#666' }}>
                            {Math.round(batchStats[batch.id].coffee_remaining || 0)}g left
                          </div>
                          <div style={{
                            width: '80px',
                            height: '6px',
                            backgroundColor: '#e0e0e0',
                            borderRadius: '3px',
                            overflow: 'hidden'
                          }}>
                            <div style={{
                              width: `${Math.min(100, batch.amount_grams > 0 ? ((batchStats[batch.id].total_coffee_used || 0) / batch.amount_grams) * 100 : 0)}%`,
                              height: '100%',
                              backgroundColor: (batchStats[batch.id].coffee_remaining || 0) <= 0 ? '#f44336' : '#4caf50',
                              transition: 'width 0.3s ease'
                            }} />
                          </div>
                          <div style={{ fontSize: '10px', color: '#999' }}>
                            {Math.round(batch.amount_grams > 0 ? ((batchStats[batch.id].total_coffee_used || 0) / batch.amount_grams) * 100 : 0)}% used
                          </div>
                        </div>
                      ) : '-'}
                    </td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                      {batchStats[batch.id] ? (
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          fontWeight: 'bold',
                          backgroundColor: (batchStats[batch.id].sessions_remaining_estimate || 0) > 0 ? '#fff3e0' : '#ffebee',
                          color: (batchStats[batch.id].sessions_remaining_estimate || 0) > 0 ? '#f57c00' : '#c62828'
                        }}>
                          {Math.round(batchStats[batch.id].sessions_remaining_estimate || 0)} uses
                        </span>
                      ) : '-'}
                    </td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                      {batchStats[batch.id] && batchStats[batch.id].average_score > 0 ? (
                        <span style={{
                          fontWeight: 'bold',
                          color: batchStats[batch.id].average_score >= 7 ? '#4caf50' :
                                batchStats[batch.id].average_score >= 5 ? '#ff9800' : '#f44336'
                        }}>
                          {batchStats[batch.id].average_score.toFixed(1)}
                        </span>
                      ) : '-'}
                    </td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                      {batch.seller || '-'}
                    </td>
                    <td style={{ 
                      padding: '8px', 
                      borderBottom: '1px solid #eee',
                      maxWidth: '200px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {batch.notes || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {showBatchForm && (
          <div style={{ marginTop: '20px' }}>
            <BatchForm 
              productId={id}
              onBatchSubmitted={handleBatchSubmitted}
              onCancel={handleCancelBatchForm}
            />
          </div>
        )}
        
        {editingBatch && (
          <div style={{ marginTop: '20px' }}>
            <BatchForm 
              productId={id}
              initialData={editingBatch}
              onBatchSubmitted={handleBatchSubmitted}
              onCancel={handleCancelBatchForm}
            />
          </div>
        )}
      </div>

      {/* Brew Recommendations */}
      <div style={{ 
        marginBottom: '30px',
        padding: '20px', 
        backgroundColor: 'white',
        borderRadius: '12px',
        border: '1px solid #e0e0e0',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ margin: '0 0 20px 0', color: '#333', fontSize: '18px', fontWeight: 'bold' }}>
          🤖 Brew Assistant
        </h3>
        <BrewRecommendations 
          productId={id} 
          selectedMethod={null}
          onApplyRecommendation={() => {}} // No-op for ProductDetail view
          showUseButton={false}
        />
      </div>


    </div>
  );
}

export default ProductDetail;