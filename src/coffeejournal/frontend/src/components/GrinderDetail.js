import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useToast } from './Toast';
import { apiFetch } from '../config';
import { ICONS } from '../config/icons';
import DeleteConfirmationModal from './DeleteConfirmationModal';
import BrewSessionTable from './BrewSessionTable';

function GrinderDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [grinder, setGrinder] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [usageInfo, setUsageInfo] = useState(null);

  useEffect(() => {
    fetchGrinderDetail();
  }, [id]);

  const fetchGrinderDetail = async (retryCount = 0) => {
    setLoading(true);
    try {
      // Prioritize the main grinder data - fetch it first
      const grinderResponse = await apiFetch(`/grinders/${id}`);
      
      if (!grinderResponse.ok) {
        // If server error and we haven't exhausted retries, try again
        if (grinderResponse.status >= 500 && retryCount < 2) {
          console.warn(`Retrying grinder detail fetch (attempt ${retryCount + 1})`);
          await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1)));
          return fetchGrinderDetail(retryCount + 1);
        }
        throw new Error(`HTTP error! status: ${grinderResponse.status}`);
      }
      
      const grinderData = await grinderResponse.json();
      setGrinder(grinderData);
      setError(null); // Clear any previous errors
      
      // Fetch stats data separately without blocking the main render
      fetchStatsData();
    } catch (err) {
      setError("Failed to fetch grinder details: " + err.message);
      console.error("Error fetching grinder details:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatsData = async () => {
    try {
      const statsResponse = await apiFetch(`/grinders/${id}/stats`);
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }
    } catch (err) {
      // Silently fail for stats data - it's not critical for the main view
      console.warn(`Stats data fetch failed for grinder: ${err.message}`);
      setStats(null);
    }
  };

  const handleEdit = () => {
    // Navigate back to the settings page with the grinder to edit
    navigate('/settings/grinders', { 
      state: { editItem: grinder }
    });
  };

  const handleDelete = async () => {
    // Check if grinder is in use first
    try {
      const usageUrl = `/grinders/${id}/usage`;
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
      const response = await apiFetch(`/grinders/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      addToast('Grinder deleted successfully!', 'success');
      // Navigate back to the settings page
      navigate('/settings/grinders');
    } catch (err) {
      addToast('Failed to delete grinder: ' + err.message, 'error');
      throw err; // Re-throw to let modal handle it
    }
  };

  const handleCloseDeleteModal = () => {
    setShowDeleteModal(false);
    setUsageInfo(null);
  };


  if (loading) return <p className="loading-message">Loading grinder details...</p>;
  if (error) return <p className="error-message">{error}</p>;
  if (!grinder) return <p>Grinder not found.</p>;

  return (
    <div>
      <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <h2 id="item-title" data-testid="item-title" style={{ margin: 0, marginRight: 'auto' }}>{grinder.name}</h2>
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
          title={`Edit ${grinder.name}`}
          aria-label={`Edit ${grinder.name}`}
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
          title={`Delete ${grinder.name}`}
          aria-label={`Delete ${grinder.name}`}
          data-testid="delete-item-btn"
        >
{ICONS.DELETE}
        </button>
        <Link 
          to={`/settings/grinders`}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px',
            textDecoration: 'none',
            marginRight: '5px'
          }}
          title="Manage Grinders"
          aria-label="Manage Grinders"
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

      {/* Grinder Details */}
      <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 15px', alignItems: 'start' }}>
          <strong>Name:</strong>
          <span>{grinder.name}</span>
          
          {grinder.brand && (
            <>
              <strong>Brand:</strong>
              <span>{grinder.brand}</span>
            </>
          )}
          
          {grinder.grinder_type && (
            <>
              <strong>Type:</strong>
              <span>{grinder.grinder_type}</span>
            </>
          )}
          
          {grinder.burr_material && (
            <>
              <strong>Burr Material:</strong>
              <span>{grinder.burr_material}</span>
            </>
          )}
          
          {grinder.description && (
            <>
              <strong>Description:</strong>
              <span>{grinder.description}</span>
            </>
          )}
          
          {grinder.notes && (
            <>
              <strong>Notes:</strong>
              <span style={{ whiteSpace: 'pre-wrap' }}>{grinder.notes}</span>
            </>
          )}
        </div>
      </div>

      {/* Usage Statistics */}
      {stats && (
        <div style={{ marginBottom: '30px', padding: '15px', backgroundColor: '#e8f5e8', borderRadius: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h3 style={{ margin: 0 }}>📊 Usage Statistics</h3>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2e7d32' }}>{Math.round(stats.total_brews)}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>Total Brews</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2e7d32' }}>
                {stats.total_kilos > 0 ? `${Math.round(stats.total_kilos)}kg` : `${Math.round(stats.total_grams_ground)}g`}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Coffee Ground (Brews)</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#d32f2f' }}>{Math.round(stats.manually_ground_grams)}g</div>
              <div style={{ fontSize: '12px', color: '#666' }}>Manual Grinding</div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1976d2' }}>
                {stats.total_grams_with_manual >= 1000 
                  ? `${Math.round(stats.total_grams_with_manual / 1000)}kg` 
                  : `${Math.round(stats.total_grams_with_manual)}g`}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Total Ground</div>
            </div>
          </div>
          
          {/* Progress Bar for Seasoning */}
          {stats.total_grams_with_manual < 1000 && (
            <div style={{ marginTop: '20px' }}>
              <div style={{ fontSize: '14px', marginBottom: '5px', color: '#666' }}>
                Seasoning Progress (1kg recommended)
              </div>
              <div style={{ 
                width: '100%', 
                height: '8px', 
                backgroundColor: '#e0e0e0', 
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{ 
                  width: `${Math.min(100, (stats.total_grams_with_manual / 1000) * 100)}%`, 
                  height: '100%', 
                  backgroundColor: stats.total_grams_with_manual >= 1000 ? '#4caf50' : '#ff9800',
                  transition: 'width 0.3s ease'
                }} />
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                {Math.round(1000 - stats.total_grams_with_manual)}g remaining for full seasoning
              </div>
            </div>
          )}
          
          {/* Top 5 Brew Sessions */}
          {stats && stats.top_5_sessions && stats.top_5_sessions.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#2e7d32', fontSize: '16px' }}>🏆 Top 5 Brew Sessions</h4>
              <BrewSessionTable 
                sessions={stats.top_5_sessions} 
                title=""
                showProduct={false}
                showActions={false}
                showFilters={false}
                showAddButton={false}
                preserveOrder={true}
                onDelete={() => {}}
                onDuplicate={() => {}}
                onEdit={() => {}}
              />
            </div>
          )}
          
          {/* Bottom 5 Brew Sessions */}
          {stats && stats.bottom_5_sessions && stats.bottom_5_sessions.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#f44336', fontSize: '16px' }}>📉 Bottom 5 Brew Sessions</h4>
              <BrewSessionTable 
                sessions={stats.bottom_5_sessions} 
                title=""
                showProduct={false}
                showActions={false}
                showFilters={false}
                showAddButton={false}
                preserveOrder={true}
                onDelete={() => {}}
                onDuplicate={() => {}}
                onEdit={() => {}}
              />
            </div>
          )}
        </div>
      )}

      <DeleteConfirmationModal
        isOpen={showDeleteModal}
        onClose={handleCloseDeleteModal}
        item={grinder}
        itemType="Grinder"
        apiEndpoint="grinders"
        usageInfo={usageInfo}
        onDeleteConfirmed={handleDeleteConfirmed}
        availableReplacements={[]} // Not needed for single item deletion
      />
    </div>
  );
}

export default GrinderDetail;