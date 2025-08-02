import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useToast } from './Toast';
import { apiFetch } from '../config';
import { ICONS } from '../config/icons';
import StarRating from './StarRating';
import DeleteConfirmationModal from './DeleteConfirmationModal';

function RoasterDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [roaster, setRoaster] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [recentProducts, setRecentProducts] = useState([]);
  const [recentSessions, setRecentSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [usageInfo, setUsageInfo] = useState(null);

  useEffect(() => {
    fetchRoasterDetail();
  }, [id]);

  const fetchRoasterDetail = async (retryCount = 0) => {
    setLoading(true);
    try {
      const response = await apiFetch(`/roasters/${id}/detail`);
      if (!response.ok) {
        // If server error and we haven't exhausted retries, try again
        if (response.status >= 500 && retryCount < 2) {
          console.warn(`Retrying roaster detail fetch (attempt ${retryCount + 1})`);
          await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1)));
          return fetchRoasterDetail(retryCount + 1);
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setRoaster(data.roaster);
      setStatistics(data.statistics);
      setRecentProducts(data.recent_products || []);
      setRecentSessions(data.recent_sessions || []);
      setError(null); // Clear any previous errors
    } catch (err) {
      // Fallback: try to fetch basic roaster info if detail fails
      if (retryCount === 0) {
        console.warn("Detail fetch failed, trying basic roaster info:", err.message);
        try {
          const basicResponse = await apiFetch(`/roasters/${id}`);
          if (basicResponse.ok) {
            const basicData = await basicResponse.json();
            setRoaster(basicData);
            setStatistics(null); // No stats available
            setRecentProducts([]);
            setRecentSessions([]);
            setError(null);
            return;
          }
        } catch (basicErr) {
          console.error("Basic roaster fetch also failed:", basicErr);
        }
      }
      setError("Failed to fetch roaster details: " + err.message);
      console.error("Error fetching roaster details:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    // Navigate back to the settings page with the roaster to edit
    navigate('/settings/roasters', { 
      state: { editItem: roaster }
    });
  };

  const handleDelete = async () => {
    // Check if roaster is in use first
    try {
      const usageUrl = `/roasters/${id}/usage`;
      const response = await apiFetch(usageUrl);
      
      if (response.ok) {
        const usage = await response.json();
        setUsageInfo(usage);
      } else {
        // If usage endpoint doesn't exist, assume it's not in use
        setUsageInfo({ in_use: false, usage_count: 0, usage_type: null });
      }
      setShowDeleteModal(true);
    } catch (err) {
      // If usage check fails, proceed with simple confirmation
      console.error('Usage check failed, proceeding with simple delete:', err);
      setUsageInfo({ in_use: false, usage_count: 0, usage_type: null });
      setShowDeleteModal(true);
    }
  };

  const handleDeleteConfirmed = async () => {
    try {
      const response = await apiFetch(`/roasters/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      addToast('Roaster deleted successfully!', 'success');
      // Navigate back to the settings page
      navigate('/settings/roasters');
    } catch (err) {
      addToast('Failed to delete roaster: ' + err.message, 'error');
      throw err; // Re-throw to let modal handle it
    }
  };

  const handleCloseDeleteModal = () => {
    setShowDeleteModal(false);
    setUsageInfo(null);
  };

  const formatDateNorwegian = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear().toString().slice(-2);
    return `${day}.${month}.${year}`;
  };

  if (loading) return <p className="loading-message">Loading roaster details...</p>;
  if (error) return <p className="error-message">{error}</p>;
  if (!roaster) return <p>Roaster not found.</p>;

  return (
    <div>
      <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <h2 id="item-title" data-testid="item-title" style={{ margin: 0, marginRight: 'auto' }}>{roaster.name}</h2>
        <button 
          onClick={handleEdit}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px',
            marginRight: '5px'
          }}
          title={`Edit ${roaster.name}`}
          aria-label={`Edit ${roaster.name}`}
          data-testid="edit-item-btn"
        >
{ICONS.EDIT}
        </button>
        <button 
          onClick={handleDelete}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px',
            marginRight: '5px'
          }}
          title={`Delete ${roaster.name}`}
          aria-label={`Delete ${roaster.name}`}
          data-testid="delete-item-btn"
        >
{ICONS.DELETE}
        </button>
        <Link 
          to={`/settings/roasters`}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px',
            textDecoration: 'none',
            marginRight: '5px'
          }}
          title="Manage Roasters"
          aria-label="Manage Roasters"
        >
          {ICONS.SETTINGS}
        </Link>
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

      {/* Roaster Details */}
      <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 15px', alignItems: 'start' }}>
          <strong>Name:</strong>
          <span>{roaster.name}</span>
          
          {roaster.description && (
            <>
              <strong>Description:</strong>
              <span>{roaster.description}</span>
            </>
          )}
          
          {roaster.url && (
            <>
              <strong>Website:</strong>
              <span>
                <a href={roaster.url} target="_blank" rel="noopener noreferrer">{roaster.url}</a>
              </span>
            </>
          )}
          
          {roaster.notes && (
            <>
              <strong>Notes:</strong>
              <span style={{ whiteSpace: 'pre-wrap' }}>{roaster.notes}</span>
            </>
          )}
        </div>
      </div>

      {/* Statistics */}
      {statistics && (
        <div style={{ marginBottom: '30px', padding: '15px', backgroundColor: '#e8f5e8', borderRadius: '8px' }}>
          <h3 style={{ margin: '0 0 15px 0' }}>📊 Statistics</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2e7d32' }}>{statistics.total_products}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>Products</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2e7d32' }}>{statistics.total_batches}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>Batches</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2e7d32' }}>{statistics.total_brew_sessions}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>Brew Sessions</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2e7d32' }}>{statistics.active_batches}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>Active Batches</div>
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
        </div>
      )}

      {/* Recent Products */}
      {recentProducts.length > 0 && (
        <div style={{ marginBottom: '30px' }}>
          <h3>☕ Recent Products</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '15px' }}>
            {recentProducts.map(product => (
              <div key={product.id} style={{ 
                padding: '15px', 
                border: '1px solid #ddd', 
                borderRadius: '8px', 
                backgroundColor: '#fafafa' 
              }}>
                <h4 style={{ margin: '0 0 10px 0' }}>
                  <Link to={`/products/${product.id}`} style={{ textDecoration: 'none', color: '#6d4c41' }}>
                    {product.product_name}
                  </Link>
                </h4>
                <p><strong>Bean Type:</strong> {Array.isArray(product.bean_type) ? product.bean_type.map(bt => bt.name).join(', ') : 'Unknown'}</p>
                <p><strong>Country:</strong> {product.country?.name || 'Unknown'}</p>
                {product.rating && (
                  <p><strong>Rating:</strong> <StarRating rating={product.rating} readOnly={true} maxRating={5} /></p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Brew Sessions */}
      {recentSessions.length > 0 && (
        <div style={{ marginBottom: '30px' }}>
          <h3>🔥 Recent Brews</h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ borderCollapse: 'collapse', fontSize: '12px', whiteSpace: 'nowrap', width: '100%' }}>
              <thead>
                <tr style={{ backgroundColor: '#e9ecef' }}>
                  <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Date</th>
                  <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Product</th>
                  <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Method</th>
                  <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Coffee</th>
                  <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Rating</th>
                </tr>
              </thead>
              <tbody>
                {recentSessions.map(session => (
                  <tr key={session.id}>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                      <Link to={`/brew-sessions/${session.id}`} style={{ textDecoration: 'none' }}>
                        {formatDateNorwegian(session.timestamp)}
                      </Link>
                    </td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                      <Link to={`/products/${session.product_id}`} style={{ textDecoration: 'none' }}>
                        {session.product_details?.product_name || 'Unknown'}
                      </Link>
                    </td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{session.brew_method?.name || '-'}</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{session.amount_coffee_grams || '-'}g</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                      {session.score ? session.score.toFixed(1) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <DeleteConfirmationModal
        isOpen={showDeleteModal}
        onClose={handleCloseDeleteModal}
        item={roaster}
        itemType="Roaster"
        apiEndpoint="roasters"
        usageInfo={usageInfo}
        onDeleteConfirmed={handleDeleteConfirmed}
        availableReplacements={[]} // Not needed for single item deletion
      />
    </div>
  );
}

export default RoasterDetail;