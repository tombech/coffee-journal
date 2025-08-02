import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useToast } from './Toast';
import { apiFetch } from '../config';
import { ICONS } from '../config/icons';
import DeleteConfirmationModal from './DeleteConfirmationModal';

function LookupDetail({ type, singularName, pluralName }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [item, setItem] = useState(null);
  const [usageData, setUsageData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [usageInfo, setUsageInfo] = useState(null);

  useEffect(() => {
    fetchItemDetail();
  }, [id, type]);

  const fetchItemDetail = async (retryCount = 0) => {
    setLoading(true);
    try {
      // Prioritize the main item data - fetch it first
      const itemResponse = await apiFetch(`/${type}/${id}`);
      
      if (!itemResponse.ok) {
        // If server error and we haven't exhausted retries, try again
        if (itemResponse.status >= 500 && retryCount < 2) {
          console.warn(`Retrying ${singularName} detail fetch (attempt ${retryCount + 1})`);
          await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1)));
          return fetchItemDetail(retryCount + 1);
        }
        throw new Error(`HTTP error! status: ${itemResponse.status}`);
      }
      
      const itemData = await itemResponse.json();
      setItem(itemData);
      setError(null); // Clear any previous errors
      
      // Fetch usage data separately without blocking the main render
      fetchUsageData();
    } catch (err) {
      setError(`Failed to fetch ${singularName.toLowerCase()} details: ` + err.message);
      console.error(`Error fetching ${singularName.toLowerCase()} details:`, err);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsageData = async () => {
    try {
      const usageResponse = await apiFetch(`/${type}/${id}/usage`);
      if (usageResponse.ok) {
        const usageData = await usageResponse.json();
        setUsageData(usageData);
      }
    } catch (err) {
      // Silently fail for usage data - it's not critical for the main view
      console.warn(`Usage data fetch failed for ${singularName}: ${err.message}`);
      setUsageData(null);
    }
  };

  const handleSetDefault = async () => {
    try {
      const response = await apiFetch(`/${type}/${id}/set_default`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      addToast(`Set as default ${singularName.toLowerCase()}`, 'success');
      fetchItemDetail(); // Refresh data
    } catch (err) {
      setError(`Failed to set default: ${err.message}`);
    }
  };

  const handleClearDefault = async () => {
    try {
      const response = await apiFetch(`/${type}/${id}/clear_default`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      addToast(`Cleared default ${singularName.toLowerCase()}`, 'success');
      fetchItemDetail(); // Refresh data
    } catch (err) {
      setError(`Failed to clear default: ${err.message}`);
    }
  };

  const handleEdit = () => {
    // Navigate back to the settings page for this type where editing can occur
    navigate(`/settings/${type.replace('_', '-')}`);
  };

  const handleDelete = async () => {
    // Check if item is in use first
    try {
      const usageUrl = `/${type}/${id}/usage`;
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
      const response = await apiFetch(`/${type}/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      addToast(`${singularName} deleted successfully!`, 'success');
      // Navigate back to the settings page
      navigate(`/settings/${type.replace('_', '-')}`);
    } catch (err) {
      addToast(`Failed to delete ${singularName.toLowerCase()}: ` + err.message, 'error');
      throw err; // Re-throw to let modal handle it
    }
  };

  const handleCloseDeleteModal = () => {
    setShowDeleteModal(false);
    setUsageInfo(null);
  };

  if (loading) return <p className="loading-message">Loading {singularName.toLowerCase()} details...</p>;
  if (error) return <p className="error-message">{error}</p>;
  if (!item) return <p>{singularName} not found.</p>;

  return (
    <div>
      <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
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
        >
{ICONS.BACK}
        </button>
        <h2 
          id="item-title"
          data-testid="item-title"
          style={{ 
            margin: 0, 
            marginRight: 'auto', 
            position: 'relative',
            padding: item.is_default ? '8px 12px' : '8px 0',
            backgroundColor: item.is_default ? '#fff3cd' : 'transparent',
            borderRadius: item.is_default ? '8px' : '0',
            border: item.is_default ? '2px solid #ffc107' : 'none'
          }}>
          {item.is_default && (
            <span style={{ 
              position: 'absolute',
              top: '-8px',
              right: '-8px',
              fontSize: '20px',
              color: '#ff9800',
              textShadow: '0 0 3px rgba(0,0,0,0.3)'
            }}>
              {ICONS.DEFAULT}
            </span>
          )}
          <span style={{ fontWeight: item.is_default ? 'bold' : 'normal' }}>
            {item.name}
          </span>
          {item.is_default && <span style={{ marginLeft: '8px', fontSize: '12px', color: '#856404', fontStyle: 'italic' }}>Default</span>}
        </h2>
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
          title={`Edit ${item.name}`}
          aria-label={`Edit ${item.name}`}
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
          title={`Delete ${item.name}`}
          aria-label={`Delete ${item.name}`}
          data-testid="delete-item-btn"
        >
{ICONS.DELETE}
        </button>
        <Link 
          to={`/settings/${type}`}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px',
            textDecoration: 'none'
          }}
          title={`Manage ${pluralName}`}
        >
{ICONS.SETTINGS}
        </Link>
      </div>

      {/* Item Details */}
      <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 15px', alignItems: 'start' }}>
          <strong>Name:</strong>
          <span>{item.name}</span>
          
          {item.short_form && (
            <>
              <strong>Short Form:</strong>
              <span>{item.short_form}</span>
            </>
          )}
          
          {item.description && (
            <>
              <strong>Description:</strong>
              <span>{item.description}</span>
            </>
          )}
          
          {item.url && (
            <>
              <strong>Website:</strong>
              <span>
                <a href={item.url} target="_blank" rel="noopener noreferrer">{item.url}</a>
              </span>
            </>
          )}
          
          {item.notes && (
            <>
              <strong>Notes:</strong>
              <span style={{ whiteSpace: 'pre-wrap' }}>{item.notes}</span>
            </>
          )}
          
          <strong>Default:</strong>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>{item.is_default ? 'Yes' : 'No'}</span>
            {item.is_default ? (
              <button 
                onClick={handleClearDefault}
                style={{ 
                  padding: '4px 8px', 
                  backgroundColor: '#f44336', 
                  color: 'white', 
                  border: 'none', 
                  borderRadius: '4px', 
                  cursor: 'pointer',
                  fontSize: '12px'
                }}
              >
                Clear Default
              </button>
            ) : (
              <button 
                onClick={handleSetDefault}
                style={{ 
                  padding: '4px 8px', 
                  backgroundColor: '#1976d2', 
                  color: 'white', 
                  border: 'none', 
                  borderRadius: '4px', 
                  cursor: 'pointer',
                  fontSize: '12px'
                }}
              >
                Set as Default
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Usage Statistics */}
      {usageData && (
        <div style={{ marginBottom: '30px', padding: '15px', backgroundColor: '#e8f5e8', borderRadius: '8px' }}>
<h3 style={{ margin: '0 0 15px 0' }}>{ICONS.STATS} Usage Statistics</h3>
          
          {usageData.usage_count > 0 ? (
            <div>
              <div style={{ textAlign: 'center', marginBottom: '15px' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2e7d32' }}>{usageData.usage_count}</div>
                <div style={{ fontSize: '12px', color: '#666' }}>Times Used in Brew Sessions</div>
              </div>
              
              {usageData.recent_usage && usageData.recent_usage.length > 0 && (
                <div>
                  <h4 style={{ margin: '15px 0 10px 0', fontSize: '14px' }}>Recent Usage:</h4>
                  <div style={{ fontSize: '12px' }}>
                    {usageData.recent_usage.slice(0, 5).map((usage, index) => (
                      <div key={index} style={{ marginBottom: '5px', color: '#666' }}>
                        • {new Date(usage.timestamp).toLocaleDateString()} - {usage.product_name || 'Unknown Product'}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p style={{ color: '#666', fontStyle: 'italic' }}>
              This {singularName.toLowerCase()} has not been used in any brew sessions yet.
            </p>
          )}
        </div>
      )}

      {/* Item Image */}
      {item.image_url && (
        <div style={{ marginBottom: '30px', textAlign: 'center' }}>
          <img 
            src={item.image_url} 
            alt={item.name} 
            style={{ 
              maxWidth: '300px', 
              maxHeight: '300px', 
              borderRadius: '8px',
              border: '1px solid #ddd'
            }} 
          />
        </div>
      )}

      <DeleteConfirmationModal
        isOpen={showDeleteModal}
        onClose={handleCloseDeleteModal}
        item={item}
        itemType={singularName}
        apiEndpoint={type}
        usageInfo={usageInfo}
        onDeleteConfirmed={handleDeleteConfirmed}
        availableReplacements={[]} // Not needed for single item deletion
      />
    </div>
  );
}

export default LookupDetail;