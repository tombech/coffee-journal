import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link, useLocation } from 'react-router-dom';
import { useToast } from './Toast';
import { apiFetch } from '../config';
import StarRating from './StarRating';
import DeleteConfirmationModal from './DeleteConfirmationModal';
import BatchForm from './BatchForm';
import { ICONS } from '../config/icons';
import UsageStatistics from './UsageStatistics';

function BatchDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { addToast } = useToast();
  const isEditMode = location.pathname.includes('/edit');
  const [batch, setBatch] = useState(null);
  const [product, setProduct] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [batchStats, setBatchStats] = useState(null);
  const [topBrewSessions, setTopBrewSessions] = useState([]);
  const [bottomBrewSessions, setBottomBrewSessions] = useState([]);
  const [recentBrewSessions, setRecentBrewSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    fetchBatchDetail();
    fetchBatchStats();
    fetchBrewSessions();
  }, [id]);

  const fetchBatchDetail = async () => {
    setLoading(true);
    try {
      const response = await apiFetch(`/batches/${id}/detail`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setBatch(data.batch);
      setProduct(data.product);
      setStatistics(data.statistics);
    } catch (err) {
      setError("Failed to fetch batch details: " + err.message);
      console.error("Error fetching batch details:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchBatchStats = async () => {
    try {
      const response = await apiFetch(`/stats/batches/${id}`);
      if (response.ok) {
        const data = await response.json();
        setBatchStats(data);
      }
    } catch (err) {
      console.error("Error fetching batch stats:", err);
      // Don't set error state, just log - stats are optional
    }
  };

  const fetchBrewSessions = async () => {
    try {
      // Fetch top, bottom, and recent brew sessions for this batch
      const [topResponse, bottomResponse, recentResponse] = await Promise.all([
        apiFetch(`/brew_sessions?batch_id=${id}&page_size=5&sort=score&sort_direction=desc`), // Top 5 by score
        apiFetch(`/brew_sessions?batch_id=${id}&page_size=5&sort=score&sort_direction=asc`),   // Bottom 5 by score
        apiFetch(`/brew_sessions?batch_id=${id}&page_size=5&sort=timestamp&sort_direction=desc`) // Recent 5 by timestamp
      ]);
      
      if (topResponse.ok && bottomResponse.ok && recentResponse.ok) {
        const [topResult, bottomResult, recentResult] = await Promise.all([
          topResponse.json(),
          bottomResponse.json(),
          recentResponse.json()
        ]);
        
        setTopBrewSessions(topResult.data || []);
        setBottomBrewSessions(bottomResult.data || []);
        setRecentBrewSessions(recentResult.data || []);
      }
    } catch (err) {
      console.warn(`Failed to fetch brew sessions for batch: ${err.message}`);
    }
  };


  const handleDelete = async () => {
    try {
      const response = await apiFetch(`/batches/${id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      addToast('Batch deleted successfully', 'success');
      navigate(product ? `/products/${product.id}` : '/');
    } catch (err) {
      setError("Failed to delete batch: " + err.message);
    }
  };

  const handleBatchUpdated = (updatedBatch) => {
    fetchBatchDetail(); // Refresh the data
    navigate(`/batches/${id}`); // Navigate back to detail view
  };

  const formatDateNorwegian = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear().toString().slice(-2);
    return `${day}.${month}.${year}`;
  };

  const getAgeText = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return '1 day ago';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    return `${Math.floor(diffDays / 365)} years ago`;
  };

  if (loading) return <p className="loading-message">Loading batch details...</p>;
  if (error) return <p className="error-message">{error}</p>;
  if (!batch) return <p>Batch not found.</p>;

  // Show edit form if in edit mode
  if (isEditMode) {
    return (
      <div>
        <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h2 style={{ margin: 0, marginRight: 'auto' }}>
            Edit Batch #{batch.id}
          </h2>
          <button 
            onClick={() => navigate(`/batches/${id}`)}
            style={{ 
              padding: '6px 8px', 
              border: 'none', 
              background: 'none', 
              cursor: 'pointer', 
              fontSize: '16px'
            }}
            title="Cancel Edit"
            aria-label="Cancel Edit"
          >
            {ICONS.BACK}
          </button>
        </div>
        
        <BatchForm 
          initialData={batch}
          onBatchSubmitted={handleBatchUpdated}
          onCancel={() => navigate(`/batches/${id}`)}
        />
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <h2 style={{ margin: 0, marginRight: 'auto' }}>
          Batch #{batch.id} Details
          {!batch.is_active && <span style={{ marginLeft: '8px', fontSize: '14px', color: '#f44336' }}>⚠️ Inactive</span>}
        </h2>
        <button
          onClick={() => navigate(`/batches/${id}/edit`)}
          title="Edit batch"
          aria-label="Edit batch"
          style={{
            padding: '6px 8px',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: '16px',
            marginRight: '5px'
          }}
        >
          {ICONS.EDIT}
        </button>
        <button
          onClick={() => setShowDeleteModal(true)}
          title="Delete batch"
          aria-label="Delete batch"
          style={{
            padding: '6px 8px',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: '16px',
            marginRight: '5px'
          }}
        >
          {ICONS.DELETE}
        </button>
        <button 
          onClick={() => navigate(-1)}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px'
          }}
          title="Go Back"
          aria-label="Go Back"
        >
          {ICONS.BACK}
        </button>
      </div>

      {/* Product Link */}
      {product && (
        <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#e3f2fd', borderRadius: '8px' }}>
          <strong>Product: </strong>
          <Link to={`/products/${product.id}`} style={{ textDecoration: 'none', fontWeight: 'bold' }}>
            {product.roaster?.name} - {product.product_name}
          </Link>
        </div>
      )}

      {/* Batch Details */}
      <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 15px', alignItems: 'start' }}>
          <strong>Roast Date:</strong>
          <span>
            {batch.roast_date ? formatDateNorwegian(batch.roast_date) : 'Unknown'}
            {batch.roast_date && <span data-testid="roast-age" style={{ color: '#666', fontSize: '12px', marginLeft: '8px' }}>
              (roasted {getAgeText(batch.roast_date)})
            </span>}
          </span>
          
          <strong>Purchase Date:</strong>
          <span>
            {batch.purchase_date ? formatDateNorwegian(batch.purchase_date) : '-'}
            {batch.purchase_date && <span style={{ color: '#666', fontSize: '12px', marginLeft: '8px' }}>
              (purchased {getAgeText(batch.purchase_date)})
            </span>}
          </span>
          
          <strong>Amount (grams):</strong>
          <span>{batch.amount_grams ? `${Math.round(batch.amount_grams)}g` : '-'}</span>
          
          <strong>Price:</strong>
          <span>{batch.price != null && !isNaN(batch.price) ? `${Math.round(Number(batch.price))} kr` : '-'}</span>
          
          <strong>Price per Cup:</strong>
          <span data-testid="price-per-cup">{statistics?.price_per_cup != null && !isNaN(statistics.price_per_cup) ? `${Math.round(Number(statistics.price_per_cup))} kr` : '-'}</span>
          
          <strong>Seller:</strong>
          <span>{batch.seller || '-'}</span>
          
          <strong>Rating:</strong>
          <span>
            {batch.rating ? (
              <StarRating rating={batch.rating} readOnly={true} maxRating={5} />
            ) : '-'}
          </span>
          
          <strong>Status:</strong>
          <span style={{ color: batch.is_active ? '#4caf50' : '#f44336' }}>
            {batch.is_active ? 'Active' : 'Inactive'}
          </span>
          
          {batch.notes && (
            <>
              <strong>Notes:</strong>
              <span style={{ whiteSpace: 'pre-wrap' }}>{batch.notes}</span>
            </>
          )}
        </div>
      </div>

      {/* Usage Statistics */}
      <UsageStatistics 
        statsData={{
          ...batchStats,
          top_5_sessions: topBrewSessions,
          bottom_5_sessions: bottomBrewSessions,
          recent_5_sessions: recentBrewSessions
        }}
        itemName="batch"
        showProduct={false}
        customStatistics={statistics && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2e7d32' }}>{Math.round(statistics.total_brew_sessions)}</div>
                <div style={{ fontSize: '12px', color: '#666' }}>Brew Sessions</div>
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2e7d32' }}>{Math.round(statistics.total_coffee_used)}g</div>
                <div style={{ fontSize: '12px', color: '#666' }}>Coffee Used</div>
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1976d2' }}>{Math.round(statistics.coffee_remaining)}g</div>
                <div style={{ fontSize: '12px', color: '#666' }}>Remaining</div>
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ff9800' }}>{Math.round(statistics.sessions_remaining_estimate)}</div>
                <div style={{ fontSize: '12px', color: '#666' }}>Est. Sessions Left</div>
              </div>
              
              {statistics.avg_rating && (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2e7d32' }}>
                    <StarRating rating={statistics.avg_rating} readOnly={true} maxRating={5} />
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>Avg Rating</div>
                </div>
              )}
            </div>

            {/* Progress Bar */}
            {batch.amount_grams > 0 && (
              <div style={{ marginTop: '20px' }}>
                <div style={{ fontSize: '14px', marginBottom: '5px', color: '#666' }}>
                  Usage Progress ({Math.round(statistics.total_coffee_used)}g of {Math.round(batch.amount_grams)}g used)
                </div>
                <div style={{ 
                  width: '100%', 
                  height: '8px', 
                  backgroundColor: '#e0e0e0', 
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{ 
                    width: `${Math.min(100, (statistics.total_coffee_used / batch.amount_grams) * 100)}%`, 
                    height: '100%', 
                    backgroundColor: statistics.coffee_remaining <= 0 ? '#f44336' : '#4caf50',
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>
            )}
          </>
        )}
      />

      {/* Add Brew Session */}
      <div style={{ marginBottom: '20px', textAlign: 'center' }}>
        <button
          onClick={() => navigate(`/brew-sessions/new?batch_id=${id}`)}
          title="Add Brew Session"
          aria-label="Add Brew Session"
          data-testid="add-brew-session-btn"
          style={{
            padding: '12px 20px',
            background: 'none',
            border: '1px solid #ccc',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: 'bold',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            margin: '0 auto'
          }}
        >
          {ICONS.CREATE} Add New Brew Session
        </button>
      </div>

      
      {/* Delete Confirmation Modal */}
      <DeleteConfirmationModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        item={batch}
        itemType="batch"
        apiEndpoint="batches"
        usageInfo={{ in_use: false }}
        onDeleteConfirmed={handleDelete}
      />
    </div>
  );
}

export default BatchDetail;